from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.config import settings
from core.security import get_current_user, require_role
from databases import get_db
from models import Equipement, Utilisateur
from schemas import (
    EquipementCreate,
    EquipementUpdate,
    EquipementResponse,
)


router = APIRouter(
    prefix="/equipements",
    tags=["Equipements"]
)


# ============================================================
# CREATE
# ============================================================

@router.post(
    "",
    response_model=EquipementResponse,
    status_code=status.HTTP_201_CREATED
)
def create_equipement(
    equipement: EquipementCreate,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(require_role("admin", "operator")),
):

    # Vérifier si l'adresse IP existe déjà
    existing = (
        db.query(Equipement)
        .filter(
            Equipement.adresse_ip == equipement.adresse_ip
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Un équipement utilise déjà cette adresse IP"
        )

    new_equipement = Equipement(
        nom=equipement.nom,
        adresse_ip=equipement.adresse_ip,
        type_equipement=equipement.type_equipement
    )

    db.add(new_equipement)
    db.commit()
    db.refresh(new_equipement)

    return new_equipement


# ============================================================
# READ ALL
# ============================================================

@router.get(
    "",
    response_model=list[EquipementResponse]
)
def get_equipements(
    db: Session = Depends(get_db)
):

    return db.query(Equipement).all()


# ============================================================
# READ ONE
# ============================================================

@router.get(
    "/{equipement_id}",
    response_model=EquipementResponse
)
def get_equipement(
    equipement_id: int,
    db: Session = Depends(get_db)
):

    equipement = (
        db.query(Equipement)
        .filter(
            Equipement.id == equipement_id
        )
        .first()
    )

    if equipement is None:
        raise HTTPException(
            status_code=404,
            detail="Équipement introuvable"
        )

    return equipement


# ============================================================
# UPDATE
# ============================================================

@router.put(
    "/{equipement_id}",
    response_model=EquipementResponse
)
def update_equipement(
    equipement_id: int,
    data: EquipementUpdate,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(require_role("admin", "operator")),
):

    equipement = (
        db.query(Equipement)
        .filter(
            Equipement.id == equipement_id
        )
        .first()
    )

    if equipement is None:
        raise HTTPException(
            status_code=404,
            detail="Équipement introuvable"
        )

    # Vérifier l'unicité de l'adresse IP
    if data.adresse_ip is not None:

        existing = (
            db.query(Equipement)
            .filter(
                Equipement.adresse_ip == data.adresse_ip,
                Equipement.id != equipement_id
            )
            .first()
        )

        if existing:
            raise HTTPException(
                status_code=409,
                detail="Cette adresse IP est déjà utilisée"
            )

    # Récupérer uniquement les champs fournis
    update_data = data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(equipement, field, value)

    db.commit()
    db.refresh(equipement)

    return equipement


# ============================================================
# DELETE
# ============================================================

@router.delete(
    "/{equipement_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_equipement(
    equipement_id: int,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(require_role("admin")),
):

    equipement = (
        db.query(Equipement)
        .filter(
            Equipement.id == equipement_id
        )
        .first()
    )

    if equipement is None:
        raise HTTPException(
            status_code=404,
            detail="Équipement introuvable"
        )

    db.delete(equipement)
    db.commit()

    return None