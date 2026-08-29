"""
Fixtures partagés pour la suite de tests.

Utilise une base SQLite fichier (isolée) pour ne pas polluer
la base de production MySQL.
"""
import os
import sys
from datetime import datetime, timezone
from typing import Iterator

import pytest

# IMPORTANT: Définir la base de données de test AVANT tout autre import
# qui pourrait charger la configuration de production
TEST_DATABASE_FILE = "./test_inventory.db"
TEST_DATABASE_URL = f"sqlite:///{TEST_DATABASE_FILE}"

# Surcharger la variable d'environnement avant d'importer quoi que ce soit
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker, declarative_base
from fastapi.testclient import TestClient

from core.security import create_access_token, hash_password
from core.config import settings

# Forcer la config de test
settings.DATABASE_URL = TEST_DATABASE_URL

# Maintenant on peut importer le reste
# IMPORTANT: Importer les modèles AVANT de créer les tables
import models  # noqa: F401 - Import des modèles pour enregistrer les tables
from databases import Base, get_db
from entrypoint import app

# Créer le moteur de test
test_engine = create_engine(
    TEST_DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)

TestSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    autocommit=False,
)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Crée les tables une fois pour toute la session de test."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def _cleanup_db_file():
    """Nettoie le fichier de base de test après la session."""
    yield
    import time
    time.sleep(0.1)
    if os.path.exists(TEST_DATABASE_FILE):
        try:
            os.remove(TEST_DATABASE_FILE)
        except PermissionError:
            pass


@pytest.fixture
def db_session() -> Iterator[Session]:
    """Fournit une session par test avec rollback automatique."""
    # Nettoie les tables avant chaque test
    with test_engine.connect() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())
        conn.commit()

    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(db_session: Session) -> TestClient:
    """Client de test FastAPI utilisant la base de test."""
    def override_get_db() -> Iterator[Session]:
        try:
            yield db_session
        finally:
            pass  # La session est déjà fermée par db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


# --- Utilisateurs de test ---
from models import Utilisateur


def _creer_utilisateur(
    db: Session,
    nom_utilisateur: str,
    mot_de_passe: str,
    role: str,
    actif: bool = True
) -> Utilisateur:
    user = Utilisateur(
        nom_utilisateur=nom_utilisateur,
        mot_de_passe_hache=hash_password(mot_de_passe),
        role=role,
        actif=actif,
        date_creation=datetime.now(timezone.utc),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def normal_user(db_session: Session) -> Utilisateur:
    return _creer_utilisateur(db_session, "normaluser", "testpass123", "lecteur")


@pytest.fixture
def admin_user(db_session: Session) -> Utilisateur:
    return _creer_utilisateur(db_session, "adminuser", "testpass123", "admin")


@pytest.fixture
def operator_user(db_session: Session) -> Utilisateur:
    return _creer_utilisateur(db_session, "operatoruser", "testpass123", "operator")


@pytest.fixture
def inactive_user(db_session: Session) -> Utilisateur:
    return _creer_utilisateur(
        db_session, "inactiveuser", "testpass123", "lecteur", actif=False
    )


@pytest.fixture
def normal_user_token_headers(normal_user) -> dict:
    token = create_access_token({
        "sub": normal_user.nom_utilisateur,
        "role": normal_user.role
    })
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_token_headers(admin_user) -> dict:
    token = create_access_token({
        "sub": admin_user.nom_utilisateur,
        "role": admin_user.role
    })
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def operator_token_headers(operator_user) -> dict:
    token = create_access_token({
        "sub": operator_user.nom_utilisateur,
        "role": operator_user.role
    })
    return {"Authorization": f"Bearer {token}"}
