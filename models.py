from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    ForeignKey,
    DateTime,
    Text,
)
from sqlalchemy.orm import relationship

from databases import Base


# ============================================================
# TOPOLOGIE
# ============================================================

class Topologie(Base):
    __tablename__ = "topologies"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    nom = Column(
        String(100),
        nullable=False
    )

    description = Column(
        Text,
        nullable=True
    )

    statut = Column(
        String(30),
        default="brouillon"
    )

    # ID du projet correspondant dans GNS3
    gns3_project_id = Column(
        String(100),
        nullable=True,
        unique=True
    )

    date_creation = Column(
        DateTime,
        default=datetime.utcnow
    )

    date_modification = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Une topologie possède plusieurs équipements
    equipements = relationship(
        "Equipement",
        back_populates="topologie",
        cascade="all, delete-orphan"
    )

    # Une topologie possède plusieurs connexions
    connexions = relationship(
        "Connexion",
        back_populates="topologie",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Topologie {self.nom}>"


# ============================================================
# EQUIPEMENT
# ============================================================

class Equipement(Base):
    __tablename__ = "equipements"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    nom = Column(
        String(100),
        nullable=False
    )

    adresse_ip = Column(
        String(45),
        unique=True,
        nullable=False
    )

    type_equipement = Column(
        String(50),
        default="routeur"
    )

    actif = Column(
        Boolean,
        default=True
    )

    date_creation = Column(
        DateTime,
        default=datetime.utcnow
    )

    # --------------------------------------------------------
    # Relation avec Topologie
    # --------------------------------------------------------

    topologie_id = Column(
        Integer,
        ForeignKey("topologies.id"),
        nullable=True
    )

    topologie = relationship(
        "Topologie",
        back_populates="equipements"
    )

    # --------------------------------------------------------
    # Relation avec Interface
    # --------------------------------------------------------

    interfaces = relationship(
        "Interface",
        back_populates="equipement",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Equipement {self.nom} ({self.adresse_ip})>"


# ============================================================
# INTERFACE
# ============================================================

class Interface(Base):
    __tablename__ = "interfaces"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    nom = Column(
        String(100),
        nullable=False
    )

    statut = Column(
        String(20),
        nullable=True
    )

    vlan = Column(
        Integer,
        nullable=True
    )

    equipement_id = Column(
        Integer,
        ForeignKey("equipements.id"),
        nullable=False
    )

    equipement = relationship(
        "Equipement",
        back_populates="interfaces"
    )

    def __repr__(self):
        return f"<Interface {self.nom} VLAN={self.vlan}>"


# ============================================================
# CONNEXION
# ============================================================

class Connexion(Base):
    __tablename__ = "connexions"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # --------------------------------------------------------
    # Topologie
    # --------------------------------------------------------

    topologie_id = Column(
        Integer,
        ForeignKey("topologies.id"),
        nullable=False
    )

    # --------------------------------------------------------
    # Équipement source
    # --------------------------------------------------------

    source_equipement_id = Column(
        Integer,
        ForeignKey("equipements.id"),
        nullable=False
    )

    # Interface source
    source_interface_id = Column(
        Integer,
        ForeignKey("interfaces.id"),
        nullable=False
    )

    # --------------------------------------------------------
    # Équipement destination
    # --------------------------------------------------------

    destination_equipement_id = Column(
        Integer,
        ForeignKey("equipements.id"),
        nullable=False
    )

    # Interface destination
    destination_interface_id = Column(
        Integer,
        ForeignKey("interfaces.id"),
        nullable=False
    )

    # --------------------------------------------------------
    # Identifiant du lien GNS3
    # --------------------------------------------------------

    gns3_link_id = Column(
        String(100),
        nullable=True
    )

    # --------------------------------------------------------
    # Relations
    # --------------------------------------------------------

    topologie = relationship(
        "Topologie",
        back_populates="connexions"
    )

    source_equipement = relationship(
        "Equipement",
        foreign_keys=[source_equipement_id]
    )

    destination_equipement = relationship(
        "Equipement",
        foreign_keys=[destination_equipement_id]
    )

    source_interface = relationship(
        "Interface",
        foreign_keys=[source_interface_id]
    )

    destination_interface = relationship(
        "Interface",
        foreign_keys=[destination_interface_id]
    )

    def __repr__(self):
        return (
            f"<Connexion "
            f"{self.source_equipement_id}:"
            f"{self.source_interface_id} -> "
            f"{self.destination_equipement_id}:"
            f"{self.destination_interface_id}>"
        )


# ============================================================
# UTILISATEUR
# ============================================================

class Utilisateur(Base):
    __tablename__ = "utilisateurs"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    nom_utilisateur = Column(
        String(100),
        unique=True,
        nullable=False
    )

    mot_de_passe_hache = Column(
        String(255),
        nullable=False
    )

    role = Column(
        String(50),
        index=True,
        default="lecteur"
    )

    actif = Column(
        Boolean,
        default=True
    )

    date_creation = Column(
        DateTime,
        default=datetime.utcnow
    )

    def __repr__(self):
        return (
            f"<Utilisateur "
            f"{self.nom_utilisateur} ({self.role})>"
        )