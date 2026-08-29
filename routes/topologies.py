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
from services.association_service import association_service
import logging

logger = logging.getLogger("inventory-app")

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

    # Intégration GNS3 : créer automatiquement un projet GNS3
    try:
        gns3_project_id = association_service.get_or_create_gns3_project(
            nouvelle_topologie
        )
        nouvelle_topologie.gns3_project_id = gns3_project_id
        nouvelle_topologie.synced_with_gns3 = True
        db.commit()
        db.refresh(nouvelle_topologie)
        logger.info(
            f"Topologie '{nouvelle_topologie.nom}' créée et synchronisée "
            f"avec GNS3 (project_id={gns3_project_id})"
        )
    except Exception as e:
        logger.warning(
            f"Topologie '{nouvelle_topologie.nom}' créée localement mais "
            f"échec de la synchronisation GNS3: {e}"
        )
        # La topologie est créée dans la DB même si GNS3 échoue
        # On pourrait implémenter une stratégie de retry ou de compensation

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
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user),
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
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(require_role("admin", "operator")),
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

    # Suppression cascade : les équipements sont supprimés automatiquement
    # grace au cascade="all, delete-orphan" dans la relation Topologie.equipements
    # Les connexions aussi grace au cascade="all, delete-orphan" dans Topologie.connexions

    # Supprimer les nœuds GNS3 associés aux équipements de cette topologie
    for equipement in topologie.equipements:
        if equipement.synced_with_gns3 and equipement.gns3_node_id:
            try:
                association_service.delete_gns3_node(
                    equipement.id, topologie_id
                )
                logger.info(
                    f"Nœud GNS3 supprimé pour l'équipement '{equipement.nom}'"
                )
            except Exception as e:
                logger.warning(
                    f"Échec de la suppression du nœud GNS3 pour "
                    f"l'équipement '{equipement.nom}': {e}"
                )

    # Supprimer le projet GNS3
    if topologie.synced_with_gns3 and topologie.gns3_project_id:
        try:
            association_service.delete_gns3_project(topologie_id)
            logger.info(
                f"Projet GNS3 supprimé pour la topologie '{topologie.nom}'"
            )
        except Exception as e:
            logger.warning(
                f"Échec de la suppression du projet GNS3 pour "
                f"la topologie '{topologie.nom}': {e}"
            )

    db.delete(topologie)
    db.commit()

    return None