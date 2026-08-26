"""
Routes d'authentification et de gestion des utilisateurs.

Endpoints :
- POST /token : login (retourne un JWT)
- POST /utilisateurs : créer un utilisateur (admin only)
- GET /utilisateurs/me : profil de l'utilisateur connecté
- GET /utilisateurs : liste des utilisateurs (admin only)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from core.security import (
    Token,
    UtilisateurCreate,
    UtilisateurResponse,
    authenticate_user,
    create_access_token,
    get_current_user,
    get_db,
    get_user,
    hash_password,
    require_role,
)
from models import Utilisateur


router = APIRouter(
    prefix="",
    tags=["Authentification"]
)


# ==========================================================
# LOGIN (POST /token)
# ==========================================================

@router.post("/token", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Authentification OAuth2 (form-data : username, password).

    Retourne un token JWT à utiliser dans l'en-tête Authorization: Bearer <token>.
    """
    user = authenticate_user(db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants invalides",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.actif:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utilisateur inactif",
        )

    # Création du token avec les claims utiles
    access_token = create_access_token(
        data={"sub": user.nom_utilisateur, "role": user.role}
    )

    return Token(access_token=access_token, token_type="bearer")


# ==========================================================
# CRÉER UN UTILISATEUR (admin only)
# ==========================================================

@router.post(
    "/utilisateurs",
    response_model=UtilisateurResponse,
    status_code=status.HTTP_201_CREATED
)
def create_utilisateur(
    data: UtilisateurCreate,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(require_role("admin"))
):
    """
    Crée un nouvel utilisateur (rôle admin requis).
    """
    # Vérifier l'unicité du nom d'utilisateur
    if get_user(db, data.nom_utilisateur):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Nom d'utilisateur déjà utilisé",
        )

    new_user = Utilisateur(
        nom_utilisateur=data.nom_utilisateur,
        mot_de_passe_hache=hash_password(data.mot_de_passe),
        role=data.role,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


# ==========================================================
# PROFIL DE L'UTILISATEUR COURANT
# ==========================================================

@router.get("/utilisateurs/me", response_model=UtilisateurResponse)
def get_my_profile(
    current_user: Utilisateur = Depends(get_current_user)
):
    """
    Retourne le profil de l'utilisateur actuellement authentifié.
    """
    return current_user


# ==========================================================
# LISTE DES UTILISATEURS (admin only)
# ==========================================================

@router.get(
    "/utilisateurs",
    response_model=list[UtilisateurResponse]
)
def list_utilisateurs(
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(require_role("admin"))
):
    """
    Liste tous les utilisateurs (admin uniquement).
    """
    return db.query(Utilisateur).all()
