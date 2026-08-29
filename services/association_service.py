"""
Service d'association entre l'API DevNet et GNS3.
Ce service assure la synchronisation automatique :
- Création d'équipement API ↔ Création de nœud GNS3
- Création de topologie API ↔ Création de projet GNS3
- Suppression d'équipement API ↔ Suppression de nœud GNS3
"""

import logging
from typing import Optional, Dict, Any
from .gns3_service import GNS3Service
from core.config import settings
from models import Topologie, Equipement

logger = logging.getLogger("inventory-app")


class AssociationService:
    """Gère l'association entre les entités API et GNS3."""

    def __init__(self):
        self.gns3 = GNS3Service()
        # Cache des associations API ID <-> GNS3 ID
        self._topologie_cache: Dict[int, str] = {}  # topologie_id -> project_id
        self._equipement_cache: Dict[int, str] = {}  # equipement_id -> node_id

    # ==========================================================
    # GESTION DES TOPOLOGIES
    # ==========================================================

    def get_or_create_gns3_project(self, topologie: Topologie) -> str:
        """
        Récupère ou crée un projet GNS3 associé à une topologie.
        Retourne l'ID du projet GNS3.
        """
        # Vérifier le cache
        if topologie.id in self._topologie_cache:
            project_id = self._topologie_cache[topologie.id]
            # Vérifier que le projet existe encore
            try:
                projects = self.gns3.get_projects()
                if any(p["project_id"] == project_id for p in projects):
                    return project_id
            except Exception:
                pass  # Le projet n'existe plus, on en crée un nouveau

        # Chercher un projet existant par nom
        try:
            projects = self.gns3.get_projects()
            for project in projects:
                if project["name"] == topologie.nom:
                    self._topologie_cache[topologie.id] = project["project_id"]
                    logger.info(
                        f"Projet GNS3 existant trouvé pour la topologie '{topologie.nom}': {project['project_id']}"
                    )
                    return project["project_id"]
        except Exception as e:
            logger.warning(f"Erreur lors de la recherche de projet GNS3: {e}")

        # Créer un nouveau projet
        try:
            project_data = self.gns3.create_project(topologie.nom)
            project_id = project_data["project_id"]
            self._topologie_cache[topologie.id] = project_id

            # Mettre à jour la topologie avec l'ID GNS3
            # Ceci serait normalement fait dans la couche repository/service
            logger.info(
                f"Projet GNS3 créé pour la topologie '{topologie.nom}': {project_id}"
            )
            return project_id
        except Exception as e:
            logger.error(f"Erreur lors de la création du projet GNS3: {e}")
            raise

    def delete_gns3_project(self, topologie_id: int) -> bool:
        """Supprime le projet GNS3 associé à une topologie."""
        if topologie_id not in self._topologie_cache:
            logger.warning(f"Aucun projet GNS3 associé à la topologie ID {topologie_id}")
            return True  # Rien à supprimer

        project_id = self._topologie_cache[topologie_id]
        try:
            # Note: L'API GNS3 actuelle n'a pas d'endpoint DELETE pour les projets
            # On pourrait implémenter une suppression logique ou juste laisser tel quel
            logger.info(
                f"Projet GNS3 {project_id} marqué pour suppression (topologie ID {topologie_id})"
            )
            # Supprimer du cache
            del self._topologie_cache[topologie_id]
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du projet GNS3 {project_id}: {e}")
            return False

    # ==========================================================
    # GESTION DES EQUIPEMENTS
    # ==========================================================

    def get_or_create_gns3_node(
        self, equipement: Equipement, topologie_id: int
    ) -> str:
        """
        Récupère ou crée un nœud GNS3 associé à un équipement.
        Retourne l'ID du nœud GNS3.
        """
        # Vérifier le cache
        if equipement.id in self._equipement_cache:
            node_id = self._equipement_cache[equipement.id]
            # Vérifier que le nœud existe encore
            try:
                project_id = self._topologie_cache.get(topologie_id)
                if project_id:
                    nodes = self.gns3.get_nodes(project_id)
                    if any(n["node_id"] == node_id for n in nodes):
                        return node_id
            except Exception:
                pass  # Le nœud n'existe plus ou erreur, on en crée un nouveau

        # S'assurer qu'on a un projet GNS3 pour cette topologie
        # Normalement, le projet devrait déjà exister via la création de topologie
        project_id = self._topologie_cache.get(topologie_id)
        if not project_id:
            # Essayer de retrouver ou créer le projet
            # Ceci devrait idéalement être géré au niveau supérieur
            from databases import SessionLocal
            from models import Topologie

            db = SessionLocal()
            try:
                topologie = db.query(Topologie).filter(Topologie.id == topologie_id).first()
                if topologie:
                    project_id = self.get_or_create_gns3_project(topologie)
                else:
                    raise ValueError(f"Topologie {topologie_id} introuvable")
            finally:
                db.close()

        # Déterminer le template à utiliser selon le type d'équipement
        template_id = self._get_template_for_equipement_type(equipement.type_equipement)
        if not template_id:
            raise ValueError(
                f"Aucun template GNS3 trouvé pour le type d'équipement: {equipement.type_equipement}"
            )

        # Calculer une position basée sur l'ID pour éviter les collisions
        base_x = 100 + (equipement.id % 10) * 50
        base_y = 100 + (equipement.id // 10) * 50

        # Créer le nœud
        try:
            node_data = self.gns3.create_node(
                project_id=project_id,
                template_id=template_id,
                name=equipement.nom,
                x=base_x,
                y=base_y,
            )
            node_id = node_data["node_id"]
            self._equipement_cache[equipement.id] = node_id

            logger.info(
                f"Nœud GNS3 créé pour l'équipement '{equipement.nom}' (ID: {equipement.id}): {node_id}"
            )
            return node_id
        except Exception as e:
            logger.error(f"Erreur lors de la création du nœud GNS3 pour {equipement.nom}: {e}")
            raise

    def delete_gns3_node(self, equipement_id: int, topologie_id: int) -> bool:
        """Supprime le nœud GNS3 associé à un équipement."""
        if equipement_id not in self._equipement_cache:
            logger.warning(f"Aucun nœud GNS3 associé à l'équipement ID {equipement_id}")
            return True  # Rien à supprimer

        node_id = self._equipement_cache[equipement_id]
        project_id = self._topologie_cache.get(topologie_id)

        if not project_id:
            logger.warning(f"Aucun projet GNS3 trouvé pour la topologie ID {topologie_id}")
            # Toujours nettoyer le cache même si pas de projet
            del self._equipement_cache[equipement_id]
            return True

        try:
            # Note: L'API GNS3 a un endpoint DELETE pour les nœuds
            # DELETE /v2/projects/{project_id}/nodes/{node_id}
            import httpx

            response = httpx.delete(
                f"{self.gns3.base_url}/v2/projects/{project_id}/nodes/{node_id}",
                auth=self.gns3.auth,
                timeout=30.0
            )
            response.raise_for_status()

            logger.info(
                f"Nœud GNS3 {node_id} supprimé pour l'équipement ID {equipement_id}"
            )
            # Supprimer du cache
            del self._equipement_cache[equipement_id]
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du nœud GNS3 {node_id}: {e}")
            # Même en cas d'erreur, on nettoie le cache pour éviter les tentatives répétées
            del self._equipement_cache[equipement_id]
            return False

    # ==========================================================
    # MÉTHODES AUXILIAIRES
    # ==========================================================

    def _get_template_for_equipement_type(self, type_equipement: str) -> Optional[str]:
        """
        Retourne l'ID du template GNS3 correspondant au type d'équipement.
        Dans une implémentation réelle, ceci ferait appel à get_templates() et ferait le mapping.
        """
        # Mapping simplifié - à améliorer avec une recherche réelle dans les templates
        type_mapping = {
            "routeur": "router",  # Ces valeurs dépendent des templates disponibles dans votre GNS3
            "commutateur": "ethernet_switch",
            "parefeu": "firewall",
            "serveur": "linux",
        }

        # Pour une implémentation complète, on chercherait dans les templates disponibles:
        # templates = self.gns3.get_templates()
        # return next((t["template_id"] for t in templates if t["name"] == type_mapping.get(type_equipement, type_equipement)), None)

        # Retourner un template générique pour le démonstration
        # Dans la pratique, vous devriez configurer cela selon vos templates GNS3
        return "router" if type_equipement == "routeur" else "ethernet_switch"

    def clear_cache(self):
        """Vide tous les caches (utile pour les tests ou en cas de incohérences)."""
        self._topologie_cache.clear()
        self._equipement_cache.clear()
        logger.info("Caches d'association vidés")


# Instance singleton
association_service = AssociationService()