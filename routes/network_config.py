"""
Routes pour la configuration réseau distante via Netmiko.

Permet d'appliquer des configurations sur les équipements réseau.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional

from core.security import get_current_user, require_role
from databases import get_db
from models import Equipement, Utilisateur
from services.network_config_service import get_network_config_service


router = APIRouter(
    prefix="/network-config",
    tags=["Network Configuration"]
)


class ConfigCommandRequest(BaseModel):
    """Requête pour envoyer une commande unique."""
    equipement_id: int = Field(gt=0)
    command: str = Field(min_length=1, max_length=500)


class ConfigSetRequest(BaseModel):
    """Requête pour envoyer un set de commandes de configuration."""
    equipement_id: int = Field(gt=0)
    commands: list[str] = Field(min_length=1, max_length=100)


class InterfaceConfigRequest(BaseModel):
    """Requête pour configurer une interface."""
    equipement_id: int = Field(gt=0)
    interface_name: str = Field(min_length=1, max_length=50)
    description: Optional[str] = Field(default=None, max_length=200)
    vlan: Optional[int] = Field(default=None, ge=1, le=4094)
    duplex: str = Field(default="auto")
    speed: str = Field(default="auto")
    shutdown: bool = False


@router.post("/command")
def execute_command(
    request: ConfigCommandRequest,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(require_role("admin", "operator")),
):
    """
    Envoie une commande unique à un équipement et retourne la sortie.
    """
    # Vérifier que l'équipement existe
    equipement = (
        db.query(Equipement)
        .filter(Equipement.id == request.equipement_id)
        .first()
    )

    if equipement is None:
        raise HTTPException(
            status_code=404,
            detail="Équipement introuvable"
        )

    # Envoyer la commande
    try:
        service = get_network_config_service()
        output = service.send_command(
            host=equipement.adresse_ip,
            command=request.command,
        )
        return {
            "equipement": equipement.nom,
            "command": request.command,
            "output": output,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'exécution de la commande: {str(e)}"
        )


@router.post("/config")
def apply_config(
    request: ConfigSetRequest,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(require_role("admin", "operator")),
):
    """
    Applique un ensemble de commandes de configuration sur un équipement.
    """
    # Vérifier que l'équipement existe
    equipement = (
        db.query(Equipement)
        .filter(Equipement.id == request.equipement_id)
        .first()
    )

    if equipement is None:
        raise HTTPException(
            status_code=404,
            detail="Équipement introuvable"
        )

    # Appliquer la configuration
    try:
        service = get_network_config_service()
        output = service.send_config(
            host=equipement.adresse_ip,
            config_commands=request.commands,
        )
        return {
            "equipement": equipement.nom,
            "commands_count": len(request.commands),
            "output": output,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'application de la configuration: {str(e)}"
        )


@router.post("/interface")
def configure_interface(
    request: InterfaceConfigRequest,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(require_role("admin", "operator")),
):
    """
    Configure une interface réseau sur un équipement.
    """
    # Vérifier que l'équipement existe
    equipement = (
        db.query(Equipement)
        .filter(Equipement.id == request.equipement_id)
        .first()
    )

    if equipement is None:
        raise HTTPException(
            status_code=404,
            detail="Équipement introuvable"
        )

    # Appliquer la configuration
    try:
        service = get_network_config_service()
        output = service.apply_interface_config(
            host=equipement.adresse_ip,
            interface_name=request.interface_name,
            description=request.description,
            vlan=request.vlan,
            duplex=request.duplex,
            speed=request.speed,
            shutdown=request.shutdown,
        )
        return {
            "equipement": equipement.nom,
            "interface": request.interface_name,
            "output": output,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la configuration de l'interface: {str(e)}"
        )


@router.get("/running-config/{equipement_id}")
def get_running_config(
    equipement_id: int,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user),
):
    """
    Récupère la configuration en cours d'un équipement.
    """
    # Vérifier que l'équipement existe
    equipement = (
        db.query(Equipement)
        .filter(Equipement.id == equipement_id)
        .first()
    )

    if equipement is None:
        raise HTTPException(
            status_code=404,
            detail="Équipement introuvable"
        )

    # Récupérer la configuration
    try:
        service = get_network_config_service()
        config = service.get_running_config(host=equipement.adresse_ip)
        return {
            "equipement": equipement.nom,
            "config": config,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération de la config: {str(e)}"
        )
