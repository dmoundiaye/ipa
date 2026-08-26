import os
from typing import Any

import httpx
from dotenv import load_dotenv


load_dotenv()


class GNS3Service:

    def __init__(self):

        self.base_url = os.getenv(
            "GNS3_URL",
            "http://192.168.80.1:3080"
        ).rstrip("/")

        self.username = os.getenv(
            "GNS3_USERNAME"
        )

        self.password = os.getenv(
            "GNS3_PASSWORD"
        )

        if not self.username or not self.password:
            raise RuntimeError(
                "GNS3_USERNAME et GNS3_PASSWORD "
                "doivent être définis dans .env"
            )

        self.auth = (
            self.username,
            self.password
        )

    # ==========================================================
    # TEST CONNEXION GNS3
    # ==========================================================

    def get_version(self) -> dict[str, Any]:

        response = httpx.get(
            f"{self.base_url}/v2/version",
            auth=self.auth,
            timeout=10.0
        )

        response.raise_for_status()

        return response.json()

    # ==========================================================
    # TEMPLATES
    # ==========================================================

    def get_templates(self) -> list[dict[str, Any]]:

        response = httpx.get(
            f"{self.base_url}/v2/templates",
            auth=self.auth,
            timeout=30.0
        )

        response.raise_for_status()

        return response.json()

    # ==========================================================
    # PROJETS
    # ==========================================================

    def get_projects(self) -> list[dict[str, Any]]:

        response = httpx.get(
            f"{self.base_url}/v2/projects",
            auth=self.auth,
            timeout=30.0
        )

        response.raise_for_status()

        return response.json()

    # ==========================================================
    # NODES D'UN PROJET
    # ==========================================================

    def get_nodes(
        self,
        project_id: str
    ) -> list[dict[str, Any]]:

        response = httpx.get(
            f"{self.base_url}/v2/projects/"
            f"{project_id}/nodes",
            auth=self.auth,
            timeout=30.0
        )

        response.raise_for_status()

        return response.json()
    
    # ==========================================================
    # CREER UN PROJET
    # ==========================================================

    def create_project(
        self,
        name: str
    ) -> dict[str, Any]:

        response = httpx.post(
            f"{self.base_url}/v2/projects",
            auth=self.auth,
            json={
                "name": name
            },
            timeout=30.0
        )

        response.raise_for_status()

        return response.json()

    # ==========================================================
    # CREER UN NODE
    # ==========================================================

    def create_node(
        self,
        project_id: str,
        template_id: str,
        name: str,
        x: int = 100,
        y: int = 100,
    ) -> dict[str, Any]:

        response = httpx.post(
            f"{self.base_url}/v2/projects/"
            f"{project_id}/templates/{template_id}",
            auth=self.auth,
            json={
                "name": name,
                "x": x,
                "y": y
            },
            timeout=60.0
        )

        response.raise_for_status()

        return response.json()

    # ==========================================================
    # CREER UN LIEN
    # ==========================================================

    def create_link(
        self,
        project_id: str,
        node1_id: str,
        adapter1: int,
        port1: int,
        node2_id: str,
        adapter2: int,
        port2: int,
    ) -> dict[str, Any]:

        payload = {
            "nodes": [
                {
                    "node_id": node1_id,
                    "adapter_number": adapter1,
                    "port_number": port1
                },
                {
                    "node_id": node2_id,
                    "adapter_number": adapter2,
                    "port_number": port2
                }
            ]
        }

        response = httpx.post(
            f"{self.base_url}/v2/projects/"
            f"{project_id}/links",
            auth=self.auth,
            json=payload,
            timeout=30.0
        )

        response.raise_for_status()

        return response.json()

    # ==========================================================
    # DEMARRER UN NODE
    # ==========================================================

    def start_node(
        self,
        project_id: str,
        node_id: str
    ) -> dict[str, Any]:

        response = httpx.post(
            f"{self.base_url}/v2/projects/"
            f"{project_id}/nodes/{node_id}/start",
            auth=self.auth,
            timeout=30.0
        )

        response.raise_for_status()

        return response.json()
        # ==========================================================
    # DEMARRER UN PROJET
    # ==========================================================

    def start_all_nodes(
        self,
        project_id: str
    ) -> list[dict[str, Any]]:

        nodes = self.get_nodes(project_id)

        results = []

        for node in nodes:

            if node.get("status") == "started":
                results.append(node)
                continue

            result = self.start_node(
                project_id,
                node["node_id"]
            )

            results.append(result)

        return results