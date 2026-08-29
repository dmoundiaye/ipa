"""
Module de sécurité pour l'API DevNet.

Contient :
- Le hashage des mots de passe avec bcrypt (via passlib)
- La création et vérification des tokens JWT (via python-jose)
- Les dépendances FastAPI pour l'authentification et l'autorisation
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.orm import Session

from core.config import settings
from databases import SessionLocal
from models import Utilisateur

# ==========================================================
# HASHAGE DES MOTS DE PASSE (bcrypt)
# ==========================================================

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash un mot de passe en clair avec bcrypt.

    Args:
        password: Mot de passe en clair

    Returns:
        Hash bcrypt du mot de passe
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Vérifie qu'un mot de passe en clair correspond à son hash.

    Args:
        plain_password: Mot de passe en clair
        hashed_password: Hash bcrypt à vérifier

    Returns:
        True si le mot de passe correspond, False sinon
    """
    return pwd_context.verify(plain_password, hashed_password)


# ==========================================================
# GESTION DES TOKENS JWT
# ==========================================================

def create_access_token(
    data: dict, expires_delta: Optional[timedelta] = None
) -> str:
    """
    Crée un token JWT signé.

    Args:
        data: Données à encoder dans le token (sub, role, etc.)
        expires_delta: Durée de validité (défaut : ACCESS_TOKEN_EXPIRE_MINUTES)

    Returns:
        Token JWT signé
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )

    return encoded_jwt


def decode_token(token: str) -> dict:
    """
    Décode et vérifie un token JWT.

    Args:
        token: Token JWT à décoder

    Returns:
        Données décodées du token

    Raises:
        JWTError: Si le token est invalide ou expiré
    """
    payload = jwt.decode(
        token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
    )
    return payload


# ==========================================================
# DÉPENDANCES FASTAPI
# ==========================================================

# Schéma OAuth2 : extrait le token Bearer de l'en-tête Authorization
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_db() -> Session:
    """
    Dépendance FastAPI : ouvre une session DB, la yield, la referme toujours.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_user(db: Session, username: str) -> Optional[Utilisateur]:
    """
    Récupère un utilisateur par son nom d'utilisateur.

    Args:
        db: Session SQLAlchemy
        username: Nom d'utilisateur à rechercher

    Returns:
        Utilisateur trouvé ou None
    """
    return db.query(Utilisateur).filter(
        Utilisateur.nom_utilisateur == username
    ).first()


def authenticate_user(
    db: Session, username: str, password: str
) -> Optional[Utilisateur]:
    """
    Authentifie un utilisateur (nom d'utilisateur + mot de passe).

    Args:
        db: Session SQLAlchemy
        username: Nom d'utilisateur
        password: Mot de passe en clair

    Returns:
        Utilisateur si authentification réussie, None sinon
    """
    user = get_user(db, username)
    if not user:
        return None

    if not verify_password(password, user.mot_de_passe_hache):
        return None

    return user


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Utilisateur:
    """
    Dépendance : extrait et vérifie l'utilisateur depuis le token JWT.

    Args:
        token: Token JWT (extrait par OAuth2PasswordBearer)
        db: Session SQLAlchemy

    Returns:
        Utilisateur authentifié

    Raises:
        HTTPException 401: Si token invalide, expiré ou utilisateur inconnu/inactif
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Impossible de valider les identifiants",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(token)
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = get_user(db, username=username)
    if user is None:
        raise credentials_exception

    if not user.actif:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utilisateur inactif",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def require_role(*allowed_roles: str):
    """
    Fabrique de dépendance : vérifie que l'utilisateur a l'un des rôles autorisés.

    Usage :
        @router.delete("/equipements/{id}")
        def delete_equipement(
            id: int,
            user: Utilisateur = Depends(require_role("admin", "operator"))
        ):
            ...

    Args:
        *allowed_roles: Rôles autorisés (ex: "admin", "operator")

    Returns:
        Dépendance FastAPI qui retourne l'utilisateur si autorisé
    """
    def role_checker(
        current_user: Utilisateur = Depends(get_current_user)
    ) -> Utilisateur:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permissions insuffisantes. Rôles requis : {allowed_roles}",
            )
        return current_user

    return role_checker


# ==========================================================
# SCHÉMAS PYDANTIC (pour les endpoints auth)
# ==========================================================

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None


class UtilisateurCreate(BaseModel):
    nom_utilisateur: str = Field(
        min_length=3,
        max_length=100,
        json_schema_extra={"example": "jdupont"}
    )
    mot_de_passe: str = Field(
        min_length=8,
        json_schema_extra={"example": "MonMotDePasseSecret123!"}
    )
    role: str = Field(
        default="lecteur",
        json_schema_extra={"example": "admin"}
    )


class UtilisateurUpdate(BaseModel):
    """Schéma pour la modification partielle d'un utilisateur (PATCH)."""
    nom_utilisateur: str | None = Field(
        default=None,
        min_length=3,
        max_length=100,
    )
    mot_de_passe: str | None = Field(
        default=None,
        min_length=8,
    )
    role: str | None = None
    actif: bool | None = None


class UtilisateurResponse(BaseModel):
    id: int
    nom_utilisateur: str
    role: str
    actif: bool
    date_creation: datetime

    model_config = ConfigDict(from_attributes=True)