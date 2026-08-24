from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from databases import get_db
from models import Equipement
from schemas import (
    EquipementCreate,
    EquipementUpdate,
    EquipementResponse,
)


router = APIRouter(
    prefix="/equipements",
    tags=["Equipements"]
)


# --------------------------------------------------
# CREATE
# --------------------------------------------------

@router.post("",
    response_model=EquipementResponse,
    status_code=status.HTTP_201_CREATED
)
def create_equipement(
    equipement: EquipementCreate,
    db: Session = Depends(get_db)
):

    # Check duplicate IP
    existing = (
        db.query(Equipement)
        .filter(Equipement.adresse_ip == equipement.adresse_ip)
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


# --------------------------------------------------
# READ ALL
# --------------------------------------------------

@router.get(
    "",
    response_model=list[EquipementResponse]
)
def get_equipements(
    db: Session = Depends(get_db)
):

    return db.query(Equipement).all()


# --------------------------------------------------
# READ ONE
# --------------------------------------------------

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
        .filter(Equipement.id == equipement_id)
        .first()
    )

    if not equipement:
        raise HTTPException(
            status_code=404,
            detail="Équipement introuvable"
        )

    return equipement


# --------------------------------------------------
# UPDATE
# --------------------------------------------------

@router.put(
    "/{equipement_id}",
    response_model=EquipementResponse
)
def update_equipement(
    equipement_id: int,
    data: EquipementUpdate,
    db: Session = Depends(get_db)
):

    equipement = (
        db.query(Equipement)
        .filter(Equipement.id == equipement_id)
        .first()
    )

    if not equipement:
        raise HTTPException(
            status_code=404,
            detail="Équipement introuvable"
        )

    # Check duplicate IP
    if data.adresse_ip:
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

    # Only update fields provided by the client
    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(equipement, field, value)

    db.commit()
    db.refresh(equipement)

    return equipement


# --------------------------------------------------
# DELETE
# --------------------------------------------------

@router.delete(
    "/{equipement_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_equipement(
    equipement_id: int,
    db: Session = Depends(get_db)
):

    equipement = (
        db.query(Equipement)
        .filter(Equipement.id == equipement_id)
        .first()
    )

    if not equipement:
        raise HTTPException(
            status_code=404,
            detail="Équipement introuvable"
        )

    db.delete(equipement)
    db.commit()

    return None