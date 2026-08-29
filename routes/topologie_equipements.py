from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging

from core.security import get_current_user, require_role
from databases import get_db
from models import Equipement, Topologie, Utilisateur
from schemas import (
    EquipementCreate,
    EquipementResponse,
)
from services.association_service import association_service

logger = logging.getLogger("inventory-app")

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
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(require_role("admin", "operator")),
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

    # Intégration GNS3 : créer automatiquement un nœud
    try:
        gns3_node_id = association_service.get_or_create_gns3_node(
            nouveau_equipement, topologie_id
        )
        nouveau_equipement.gns3_node_id = gns3_node_id
        nouveau_equipement.gns3_template_id = (
            "router" if nouveau_equipement.type_equipement == "routeur" else "ethernet_switch"
        )
        nouveau_equipement.synced_with_gns3 = True
        db.commit()
        db.refresh(nouveau_equipement)
        logger.info(
            f"Équipement '{nouveau_equipement.nom}' créé et synchronisé "
            f"avec GNS3 (node_id={gns3_node_id})"
        )
    except Exception as e:
        logger.warning(
            f"Équipement '{nouveau_equipement.nom}' créé localement mais "
            f"échec de la synchronisation GNS3: {e}"
        )
        # L'équipement est créé dans la DB même si GNS3 échoue

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
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user),
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


# ============================================================
# SUPPRIMER UN EQUIPEMENT D'UNE TOPOLOGIE
# ============================================================

@router.delete(
    "/{equipement_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def supprimer_equipement_topologie(
    topologie_id: int,
    equipement_id: int,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(require_role("admin")),
):
    # Vérifier que la topologie existe
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

    # Vérifier que l'équipement existe et appartient à la topologie
    equipement = (
        db.query(Equipement)
        .filter(
            Equipement.id == equipement_id,
            Equipement.topologie_id == topologie_id
        )
        .first()
    )

    if equipement is None:
        raise HTTPException(
            status_code=404,
            detail="Équipement introuvable dans cette topologie"
        )

    # Supprimer le nœud GNS3 associé
    if equipement.synced_with_gns3 and equipement.gns3_node_id:
        try:
            association_service.delete_gns3_node(equipement_id, topologie_id)
            logger.info(
                f"Nœud GNS3 supprimé pour l'équipement '{equipement.nom}'"
            )
        except Exception as e:
            logger.warning(
                f"Échec de la suppression du nœud GNS3 pour "
                f"l'équipement '{equipement.nom}': {e}"
            )

    db.delete(equipement)
    db.commit()

    return None
