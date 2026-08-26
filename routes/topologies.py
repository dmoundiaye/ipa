from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.security import get_current_user, require_role
from databases import get_db
from models import Topologie, Utilisateur
from schemas import (
    TopologieCreate,
    TopologieUpdate,
    TopologieResponse,
)


router = APIRouter(
    prefix="/topologies",
    tags=["Topologies"]
)


# ============================================================
# CREATE
# ============================================================

@router.post(
    "",
    response_model=TopologieResponse,
    status_code=status.HTTP_201_CREATED
)
def creer_topologie(
    topologie: TopologieCreate,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(require_role("admin", "operator")),
):
    nouvelle_topologie = Topologie(
        nom=topologie.nom,
        description=topologie.description,
        statut="brouillon"
    )

    db.add(nouvelle_topologie)
    db.commit()
    db.refresh(nouvelle_topologie)

    return nouvelle_topologie


# ============================================================
# READ ALL
# ============================================================

@router.get(
    "",
    response_model=list[TopologieResponse]
)
def lister_topologies(
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(require_role("admin", "operator")),
):
    return db.query(Topologie).all()


# ============================================================
# READ ONE
# ============================================================

@router.get(
    "/{topologie_id}",
    response_model=TopologieResponse
)
def obtenir_topologie(
    topologie_id: int,
    db: Session = Depends(get_db)
):
    topologie = (
        db.query(Topologie)
        .filter(Topologie.id == topologie_id)
        .first()
    )

    if topologie is None:
        raise HTTPException(
            status_code=404,
            detail="Topologie introuvable"
        )

    return topologie


# ============================================================
# UPDATE
# ============================================================

@router.put(
    "/{topologie_id}",
    response_model=TopologieResponse
)
def modifier_topologie(
    topologie_id: int,
    donnees: TopologieUpdate,
    db: Session = Depends(get_db)
):
    topologie = (
        db.query(Topologie)
        .filter(Topologie.id == topologie_id)
        .first()
    )

    if topologie is None:
        raise HTTPException(
            status_code=404,
            detail="Topologie introuvable"
        )

    donnees_modifiees = donnees.model_dump(
        exclude_unset=True
    )

    for champ, valeur in donnees_modifiees.items():
        setattr(topologie, champ, valeur)

    db.commit()
    db.refresh(topologie)

    return topologie


# ============================================================
# DELETE
# ============================================================

@router.delete(
    "/{topologie_id}",
    status_code=204
)
def supprimer_topologie(
    topologie_id: int,
    db: Session = Depends(get_db)
):
    topologie = (
        db.query(Topologie)
        .filter(Topologie.id == topologie_id)
        .first()
    )

    if topologie is None:
        raise HTTPException(
            status_code=404,
            detail="Topologie introuvable"
        )

    db.delete(topologie)
    db.commit()

    return None