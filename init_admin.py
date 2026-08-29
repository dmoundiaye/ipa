"""
Script d'initialisation - Crée un utilisateur admin par défaut.

Usage:
    python init_admin.py
"""
import sys
import os
from datetime import datetime, timezone

# Permet l'exécution directe du script
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from databases import SessionLocal, Base, engine
import models  # noqa: F401 - Importer les modèles pour créer les tables
from core.security import hash_password, get_user
from models import Utilisateur


def init_database():
    """Crée toutes les tables si elles n'existent pas."""
    print("Création des tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables créées avec succès.")


def create_admin(
    username: str = "admin",
    password: str = "Admin@123456",
    role: str = "admin"
):
    """Crée un utilisateur admin s'il n'existe pas déjà."""
    db = SessionLocal()
    try:
        # Vérifier si un admin existe déjà
        existing_admin = (
            db.query(Utilisateur)
            .filter(Utilisateur.role == "admin")
            .first()
        )

        if existing_admin:
            print(f"Un administrateur existe déjà: {existing_admin.nom_utilisateur}")
            return False

        # Vérifier si le nom d'utilisateur est déjà pris
        if get_user(db, username):
            print(f"L'utilisateur '{username}' existe déjà.")
            return False

        # Créer l'admin
        admin = Utilisateur(
            nom_utilisateur=username,
            mot_de_passe_hache=hash_password(password),
            role=role,
            actif=True,
            date_creation=datetime.now(timezone.utc),
        )

        db.add(admin)
        db.commit()
        db.refresh(admin)

        print(f"Administrateur créé avec succès!")
        print(f"  Nom d'utilisateur: {admin.nom_utilisateur}")
        print(f"  Rôle: {admin.role}")
        print(f"  Mot de passe: {password}")
        print(f"\n⚠️  IMPORTANT: Changez ce mot de passe dès la première connexion!")
        return True

    except Exception as e:
        print(f"Erreur lors de la création de l'admin: {e}")
        db.rollback()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 50)
    print("Initialisation de l'API DevNet")
    print("=" * 50)

    # Créer les tables
    init_database()

    # Créer l'admin par défaut
    # Vous pouvez modifier ces valeurs
    ADMIN_USERNAME = os.getenv("INIT_ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.getenv("INIT_ADMIN_PASSWORD", "Admin@123456")

    print(f"\nCréation de l'administrateur '{ADMIN_USERNAME}'...")
    if create_admin(ADMIN_USERNAME, ADMIN_PASSWORD):
        print("\nInitialisation terminée!")
    else:
        print("\nAucune modification effectuée.")

    print("\nPour lancer l'API:")
    print("  uvicorn entrypoint:app --reload")
    print("ou")
    print("  docker-compose up -d")
    print("\nDocumentation: http://localhost:8000/docs")
