from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from databases import get_db
from models import Equipement, Topologie
from schemas import (
    EquipementCreate,
    EquipementResponse,
)


router = APIRouter(
    prefix="/topologies/{topologie_id}/equipements",
    tags=["Topologie - Equipements"]
)


# ============================================================
# AJOUTER UN EQUIPEMENT A UNE TOPOLOGIE
# ============================================================

@router.post(
    "",
    response_model=EquipementResponse,
    status_code=status.HTTP_201_CREATED
)
def ajouter_equipement_topologie(
    topologie_id: int,
    equipement: EquipementCreate,
    db: Session = Depends(get_db)
):

    # Vérifier que la topologie existe
    topologie = (
        db.query(Topologie)
        .filter(
            Topologie.id == topologie_id
        )
        .first()
    )

    if topologie is None:
        raise HTTPException(
            status_code=404,
            detail="Topologie introuvable"
        )

    # Vérifier l'adresse IP
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

    # Créer l'équipement et le rattacher
    # à la topologie
    nouveau_equipement = Equipement(
        nom=equipement.nom,
        adresse_ip=equipement.adresse_ip,
        type_equipement=equipement.type_equipement,
        topologie_id=topologie_id
    )

    db.add(nouveau_equipement)
    db.commit()
    db.refresh(nouveau_equipement)

    return nouveau_equipement


# ============================================================
# LISTER LES EQUIPEMENTS D'UNE TOPOLOGIE
# ============================================================

@router.get(
    "",
    response_model=list[EquipementResponse]
)
def lister_equipements_topologie(
    topologie_id: int,
    db: Session = Depends(get_db)
):

    # Vérifier que la topologie existe
    topologie = (
        db.query(Topologie)
        .filter(
            Topologie.id == topologie_id
        )
        .first()
    )

    if topologie is None:
        raise HTTPException(
            status_code=404,
            detail="Topologie introuvable"
        )

    return (
        db.query(Equipement)
        .filter(
            Equipement.topologie_id == topologie_id
        )
        .all()
    )