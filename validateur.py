from fastapi import FastAPI
from pydantic import BaseModel, Field, field_validator
import ipaddress


app = FastAPI(title="API Inventaire Réseau", version="1.0.0")

class EquipementCreate (BaseModel) :

    """Valide et documente le format des donnees recues (pas une table !)."""
    adresse_ip: str
    type_equipement: str = "routeur"

    nom: str = Field (min_length=2, max_length=50)

    @field_validator("adresse_ip")
    @classmethod

    def valider_ip(cls, valeur: str) -> str:

        try:

            ipaddress.ip_address (valeur)
        # lève ValueError si invalide
        except ValueError:
            raise ValueError("Adresse IP invalide (IPv4 ou IPv6 attendue)")
        return valeur

@app. post ("/equipements", status_code=201)
def creer_equipement (equipement: EquipementCreate) :

    # "equipement" est deja valide : aucune verification manuelle
    return equipement