from pydantic import BaseModel, Field, field_validator, model_validator
import ipaddress


# ============================================================
# EQUIPEMENTS
# ============================================================

class EquipementCreate(BaseModel):
    nom: str = Field(
        min_length=2,
        max_length=100
    )

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
    nom: str | None = Field(
        default=None,
        min_length=2,
        max_length=100
    )

    adresse_ip: str | None = None

    type_equipement: str | None = None

    actif: bool | None = None

    @field_validator("adresse_ip")
    @classmethod
    def validate_ip(
        cls,
        value: str | None
    ) -> str | None:

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


# ============================================================
# TOPOLOGIES
# ============================================================

class TopologieCreate(BaseModel):

    nom: str = Field(
        min_length=2,
        max_length=100
    )

    description: str | None = Field(
        default=None,
        max_length=1000
    )


class TopologieUpdate(BaseModel):

    nom: str | None = Field(
        default=None,
        min_length=2,
        max_length=100
    )

    description: str | None = Field(
        default=None,
        max_length=1000
    )

    statut: str | None = Field(
        default=None,
        max_length=30
    )

    gns3_project_id: str | None = Field(
        default=None,
        max_length=100
    )


class TopologieResponse(BaseModel):

    id: int

    nom: str

    description: str | None

    statut: str

    gns3_project_id: str | None

    model_config = {
        "from_attributes": True
    }


# ============================================================
# CONNEXIONS
# ============================================================

class ConnexionCreate(BaseModel):

    source_equipement_id: int = Field(
        gt=0
    )

    destination_equipement_id: int = Field(
        gt=0
    )

    source_adapter: int = Field(
        default=0,
        ge=0
    )

    source_port: int = Field(
        default=0,
        ge=0
    )

    destination_adapter: int = Field(
        default=0,
        ge=0
    )

    destination_port: int = Field(
        default=0,
        ge=0
    )

    @model_validator(mode="after")
    def verifier_equipements(self):

        if (
            self.source_equipement_id
            == self.destination_equipement_id
        ):
            raise ValueError(
                "Un équipement ne peut pas "
                "être connecté à lui-même"
            )

        return self


class ConnexionResponse(BaseModel):

    id: int

    topologie_id: int

    source_equipement_id: int

    destination_equipement_id: int

    source_adapter: int

    source_port: int

    destination_adapter: int

    destination_port: int

    gns3_link_id: str | None

    model_config = {
        "from_attributes": True
    }

# ============================================================
# INTERFACES
# ============================================================

class InterfaceCreate(BaseModel):
    nom: str = Field(
        min_length=1,
        max_length=100
    )

    statut: str | None = None

    vlan: int | None = Field(
        default=None,
        ge=1,
        le=4094
    )

    equipement_id: int


class InterfaceUpdate(BaseModel):
    nom: str | None = Field(
        default=None,
        min_length=1,
        max_length=100
    )

    statut: str | None = None

    vlan: int | None = Field(
        default=None,
        ge=1,
        le=4094
    )


class InterfaceResponse(BaseModel):
    id: int
    nom: str
    statut: str | None
    vlan: int | None
    equipement_id: int

    model_config = {
        "from_attributes": True
    }

class ConnexionCreate(BaseModel):
    topologie_id: int
    source_equipement_id: int
    destination_equipement_id: int

    source_adapter: int = Field(default=0, ge=0)
    source_port: int = Field(default=0, ge=0)

    destination_adapter: int = Field(default=0, ge=0)
    destination_port: int = Field(default=0, ge=0)

    gns3_link_id: str | None = None


class ConnexionUpdate(BaseModel):
    source_equipement_id: int | None = None
    destination_equipement_id: int | None = None

    source_adapter: int | None = Field(default=None, ge=0)
    source_port: int | None = Field(default=None, ge=0)

    destination_adapter: int | None = Field(default=None, ge=0)
    destination_port: int | None = Field(default=None, ge=0)

    gns3_link_id: str | None = None


class ConnexionResponse(BaseModel):
    id: int
    topologie_id: int

    source_equipement_id: int
    destination_equipement_id: int

    source_adapter: int
    source_port: int

    destination_adapter: int
    destination_port: int

    gns3_link_id: str | None

    model_config = {
        "from_attributes": True
    }
    
class ConnexionCreate(BaseModel):
    topologie_id: int = Field(gt=0)

    source_equipement_id: int = Field(gt=0)
    source_interface_id: int = Field(gt=0)

    destination_equipement_id: int = Field(gt=0)
    destination_interface_id: int = Field(gt=0)


class ConnexionUpdate(BaseModel):
    source_equipement_id: int | None = Field(default=None, gt=0)
    source_interface_id: int | None = Field(default=None, gt=0)

    destination_equipement_id: int | None = Field(default=None, gt=0)
    destination_interface_id: int | None = Field(default=None, gt=0)

    gns3_link_id: str | None = None


class ConnexionResponse(BaseModel):
    id: int
    topologie_id: int

    source_equipement_id: int
    source_interface_id: int

    destination_equipement_id: int
    destination_interface_id: int

    gns3_link_id: str | None

    model_config = {
        "from_attributes": True
    }