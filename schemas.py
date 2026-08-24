from pydantic import BaseModel, Field, field_validator
import ipaddress


class EquipementCreate(BaseModel):
    nom: str = Field(min_length=2, max_length=100)
    adresse_ip: str
    type_equipement: str = "routeur"

    @field_validator("adresse_ip")
    @classmethod
    def validate_ip(cls, value: str) -> str:
        try:
            ipaddress.ip_address(value)
        except ValueError:
            raise ValueError("Adresse IP invalide")
        return value


class EquipementUpdate(BaseModel):
    nom: str | None = Field(default=None, min_length=2, max_length=100)
    adresse_ip: str | None = None
    type_equipement: str | None = None
    actif: bool | None = None

    @field_validator("adresse_ip")
    @classmethod
    def validate_ip(cls, value: str | None) -> str | None:
        if value is not None:
            try:
                ipaddress.ip_address(value)
            except ValueError:
                raise ValueError("Adresse IP invalide")
        return value


class EquipementResponse(BaseModel):
    id: int
    nom: str
    adresse_ip: str
    type_equipement: str
    actif: bool

    model_config = {
        "from_attributes": True
    }