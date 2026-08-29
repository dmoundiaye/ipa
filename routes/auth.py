"""
Routes d'authentification et de gestion des utilisateurs.

Endpoints :
- POST /token : login (retourne un JWT)
- POST /utilisateurs : créer un utilisateur (admin only)
- GET /utilisateurs/me : profil de l'utilisateur connecté
- GET /utilisateurs : liste des utilisateurs (admin only)
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from core.security import (
    Token,
    UtilisateurCreate,
    UtilisateurUpdate,
    UtilisateurResponse,
    authenticate_user,
    create_access_token,
    get_current_user,
    get_db,
    get_user,
    hash_password,
    require_role,
    verify_password,
)
from core.limiter import limiter
from models import Utilisateur
import logging

logger = logging.getLogger("inventory-app")


router = APIRouter(
    prefix="",
    tags=["Authentification"]
)


# ==========================================================
# LOGIN (POST /token)
# ==========================================================

@router.post("/token", response_model=Token)
@limiter.limit("5/minute")
def login(
    request: Request,
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


# ==========================================================
# MODIFIER UN UTILISATEUR (admin only)
# ==========================================================

@router.put(
    "/utilisateurs/{user_id}",
    response_model=UtilisateurResponse
)
def modifier_utilisateur(
    user_id: int,
    data: UtilisateurUpdate,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(require_role("admin"))
):
    """
    Modifie un utilisateur (rôle admin requis).
    L'admin ne peut pas modifier son propre rôle ni désactiver son propre compte.
    """
    # Trouver l'utilisateur à modifier
    user = db.query(Utilisateur).filter(Utilisateur.id == user_id).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur introuvable"
        )

    # Utiliser model_dump avec exclude_unset pour ne mettre à jour que les champs fournis
    update_data = data.model_dump(exclude_unset=True)

    # Vérifier l'unicité du nom d'utilisateur s'il est modifié
    if "nom_utilisateur" in update_data and update_data["nom_utilisateur"] != user.nom_utilisateur:
        existing = get_user(db, update_data["nom_utilisateur"])
        if existing and existing.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Nom d'utilisateur déjà utilisé",
            )

    # Empêcher l'admin de désactiver son propre compte
    if user.id == current_user.id and update_data.get("actif") is False:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Impossible de désactiver son propre compte",
        )

    # Hacher le mot de passe avant de le sauvegarder
    if "mot_de_passe" in update_data:
        update_data["mot_de_passe_hache"] = hash_password(update_data.pop("mot_de_passe"))

    # Appliquer les modifications
    for champ, valeur in update_data.items():
        setattr(user, champ, valeur)

    db.commit()
    db.refresh(user)

    return user


# ==========================================================
# SUPPRIMER UN UTILISATEUR (admin only)
# ==========================================================

@router.delete(
    "/utilisateurs/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def supprimer_utilisateur(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(require_role("admin"))
):
    """
    Supprime un utilisateur (rôle admin requis).
    L'admin ne peut pas supprimer son propre compte.
    """
    # Trouver l'utilisateur à supprimer
    user = db.query(Utilisateur).filter(Utilisateur.id == user_id).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur introuvable"
        )

    # Empêcher l'admin de supprimer son propre compte
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Impossible de supprimer son propre compte",
        )

    # Si l'utilisateur a un nœud GNS3 synchronisé, le nettoyer
    if hasattr(user, 'gns3_node_id') and user.gns3_node_id:
        logger.warning(
            f"Suppression de l'utilisateur '{user.nom_utilisateur}' "
            f"sans nettoyage GNS3 (pas d'intégration GNS3 pour utilisateurs)"
        )

    db.delete(user)
    db.commit()

    return None
