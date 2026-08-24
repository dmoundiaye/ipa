from dotenv import load_dotenv
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class Equipement(Base):
    __tablename__ = "equipements"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(100), nullable=False)
    adresse_ip = Column(String(45), unique=True, nullable=False)
    type_equipement = Column(String(50), default="routeur")
    actif = Column(Boolean, default=True)
    date_creation = Column(DateTime, default=datetime.utcnow)

    # Relation avec Interface
    interfaces = relationship("Interface", back_populates="equipement", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Equipement {self.nom} ({self.adresse_ip})>"


class Interface(Base):
    __tablename__ = "interfaces"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(100), nullable=False)
    statut = Column(String(20), nullable=True)
    vlan = Column(Integer, nullable=True)
    equipement_id = Column(Integer, ForeignKey("equipements.id"), nullable=False)

    # Relation inverse
    equipement = relationship("Equipement", back_populates="interfaces")

    def __repr__(self):
        return f"<Interface {self.nom} VLAN={self.vlan}>"


class Utilisateur(Base):
    __tablename__ = "utilisateurs"

    id = Column(Integer, primary_key=True, index=True)
    nom_utilisateur = Column(String(100), unique=True, nullable=False)
    mot_de_passe_hache = Column(String(255), nullable=False)
    role = Column(String(50), index=True)

    def __repr__(self):
        return f"<Utilisateur {self.nom_utilisateur} ({self.role})>"
