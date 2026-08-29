from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.security import get_current_user, require_role
from databases import get_db
from models import Connexion, Equipement, Interface, Topologie, Utilisateur
from schemas import (
    ConnexionCreate,
    ConnexionUpdate,
    ConnexionResponse,
)


router = APIRouter(
    prefix="/connexions",
    tags=["Connexions"]
)


# ==========================================================
# CREATE
# ==========================================================

@router.post(
    "",
    response_model=ConnexionResponse,
    status_code=status.HTTP_201_CREATED
)
def create_connexion(
    data: ConnexionCreate,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(require_role("admin", "operator")),
):

    # Vérifier la topologie
    topologie = (
        db.query(Topologie)
        .filter(Topologie.id == data.topologie_id)
        .first()
    )

    if not topologie:
        raise HTTPException(
            status_code=404,
            detail="Topologie introuvable"
        )

    # Vérifier l'équipement source
    source_equipement = (
        db.query(Equipement)
        .filter(Equipement.id == data.source_equipement_id)
        .first()
    )

    if not source_equipement:
        raise HTTPException(
            status_code=404,
            detail="Équipement source introuvable"
        )

    # Vérifier l'équipement destination
    destination_equipement = (
        db.query(Equipement)
        .filter(Equipement.id == data.destination_equipement_id)
        .first()
    )

    if not destination_equipement:
        raise HTTPException(
            status_code=404,
            detail="Équipement destination introuvable"
        )

    # Vérifier l'interface source
    source_interface = (
        db.query(Interface)
        .filter(Interface.id == data.source_interface_id)
        .first()
    )

    if not source_interface:
        raise HTTPException(
            status_code=404,
            detail="Interface source introuvable"
        )

    # Vérifier l'interface destination
    destination_interface = (
        db.query(Interface)
        .filter(Interface.id == data.destination_interface_id)
        .first()
    )

    if not destination_interface:
        raise HTTPException(
            status_code=404,
            detail="Interface destination introuvable"
        )

    # Vérifier que l'interface source appartient
    # bien à l'équipement source
    if source_interface.equipement_id != data.source_equipement_id:
        raise HTTPException(
            status_code=400,
            detail=(
                "L'interface source n'appartient pas "
                "à l'équipement source"
            )
        )

    # Vérifier que l'interface destination appartient
    # bien à l'équipement destination
    if (
        destination_interface.equipement_id
        != data.destination_equipement_id
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "L'interface destination n'appartient pas "
                "à l'équipement destination"
            )
        )

    # Empêcher une connexion d'un équipement vers lui-même
    if (
        data.source_equipement_id
        == data.destination_equipement_id
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Un équipement ne peut pas "
                "être connecté à lui-même"
            )
        )

    # Création
    connexion = Connexion(
        topologie_id=data.topologie_id,
        source_equipement_id=data.source_equipement_id,
        source_interface_id=data.source_interface_id,
        destination_equipement_id=data.destination_equipement_id,
        destination_interface_id=data.destination_interface_id,
    )

    db.add(connexion)
    db.commit()
    db.refresh(connexion)

    return connexion


# ==========================================================
# READ ALL
# ==========================================================

@router.get(
    "",
    response_model=list[ConnexionResponse]
)
def get_connexions(
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user),
):

    return db.query(Connexion).all()


# ==========================================================
# READ ONE
# ==========================================================

@router.get(
    "/{connexion_id}",
    response_model=ConnexionResponse
)
def get_connexion(
    connexion_id: int,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user),
):

    connexion = (
        db.query(Connexion)
        .filter(Connexion.id == connexion_id)
        .first()
    )

    if not connexion:
        raise HTTPException(
            status_code=404,
            detail="Connexion introuvable"
        )

    return connexion


# ==========================================================
# UPDATE
# ==========================================================

@router.put(
    "/{connexion_id}",
    response_model=ConnexionResponse
)
def update_connexion(
    connexion_id: int,
    data: ConnexionUpdate,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(require_role("admin", "operator")),
):

    connexion = (
        db.query(Connexion)
        .filter(Connexion.id == connexion_id)
        .first()
    )

    if not connexion:
        raise HTTPException(
            status_code=404,
            detail="Connexion introuvable"
        )

    update_data = data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(connexion, field, value)

    db.commit()
    db.refresh(connexion)

    return connexion


# ==========================================================
# DELETE
# ==========================================================

@router.delete(
    "/{connexion_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_connexion(
    connexion_id: int,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(require_role("admin")),
):

    connexion = (
        db.query(Connexion)
        .filter(Connexion.id == connexion_id)
        .first()
    )

    if not connexion:
        raise HTTPException(
            status_code=404,
            detail="Connexion introuvable"
        )

    db.delete(connexion)
    db.commit()

    return None
