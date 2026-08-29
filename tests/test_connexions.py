"""
Tests pour les connexions (CRUD + validations métier).
"""
from unittest.mock import patch

import pytest
from fastapi import status


@pytest.fixture(autouse=True)
def mock_gns3():
    """Mock le service d'association GNS3 pour les tests."""
    with patch("routes.topologies.association_service") as mock_top_assoc, \
         patch("routes.topologie_equipements.association_service") as mock_te_assoc:
        mock_top_assoc.get_or_create_gns3_project.return_value = "test-project-id"
        mock_top_assoc.delete_gns3_project.return_value = True
        mock_te_assoc.get_or_create_gns3_node.return_value = "test-node-id"
        mock_te_assoc.delete_gns3_node.return_value = True
        yield mock_top_assoc


def _creer_topologie(client, headers, nom="Topo1"):
    """Helper pour créer une topologie."""
    response = client.post(
        "/topologies",
        json={"nom": nom, "description": "Test"},
        headers=headers,
    )
    return response.json() if response.status_code == 201 else None


def _creer_equipement(client, headers, topologie_id, nom="Eq1", ip="10.0.0.1"):
    """Helper pour créer un équipement dans une topologie."""
    response = client.post(
        f"/topologies/{topologie_id}/equipements",
        json={"nom": nom, "adresse_ip": ip, "type_equipement": "routeur"},
        headers=headers,
    )
    return response.json() if response.status_code == 201 else None


def _creer_interface(client, headers, equipement_id, nom="Eth0"):
    """Helper pour créer une interface."""
    response = client.post(
        "/interfaces",
        json={"nom": nom, "equipement_id": equipement_id},
        headers=headers,
    )
    return response.json() if response.status_code == 201 else None


def test_creer_connexion_valide(
    client, db_session, admin_token_headers, mock_gns3
):
    """Test création d'une connexion valide entre 2 équipements."""
    topo = _creer_topologie(client, admin_token_headers, "TopoConn")
    eq1 = _creer_equipement(client, admin_token_headers, topo["id"], "R1", "10.0.0.1")
    eq2 = _creer_equipement(client, admin_token_headers, topo["id"], "R2", "10.0.0.2")
    if1 = _creer_interface(client, admin_token_headers, eq1["id"], "Eth0/0")
    if2 = _creer_interface(client, admin_token_headers, eq2["id"], "Eth0/0")

    response = client.post(
        "/connexions",
        json={
            "topologie_id": topo["id"],
            "source_equipement_id": eq1["id"],
            "source_interface_id": if1["id"],
            "destination_equipement_id": eq2["id"],
            "destination_interface_id": if2["id"],
        },
        headers=admin_token_headers,
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["topologie_id"] == topo["id"]
    assert data["source_equipement_id"] == eq1["id"]


def test_creer_connexion_self_loop_refuse(
    client, db_session, admin_token_headers, mock_gns3
):
    """Test qu'un équipement ne peut pas se connecter à lui-même."""
    topo = _creer_topologie(client, admin_token_headers, "TopoSelf")
    eq = _creer_equipement(client, admin_token_headers, topo["id"], "R1", "10.0.0.10")
    if1 = _creer_interface(client, admin_token_headers, eq["id"], "Eth0")
    if2 = _creer_interface(client, admin_token_headers, eq["id"], "Eth1")

    response = client.post(
        "/connexions",
        json={
            "topologie_id": topo["id"],
            "source_equipement_id": eq["id"],
            "source_interface_id": if1["id"],
            "destination_equipement_id": eq["id"],
            "destination_interface_id": if2["id"],
        },
        headers=admin_token_headers,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "lui-même" in response.json()["detail"].lower()


def test_creer_connexion_interface_mismatch(
    client, db_session, admin_token_headers, mock_gns3
):
    """Test que l'interface source doit appartenir à l'équipement source."""
    topo = _creer_topologie(client, admin_token_headers, "TopoMismatch")
    eq1 = _creer_equipement(client, admin_token_headers, topo["id"], "R1", "10.0.0.20")
    eq2 = _creer_equipement(client, admin_token_headers, topo["id"], "R2", "10.0.0.21")
    if1 = _creer_interface(client, admin_token_headers, eq1["id"], "Eth0")
    if2 = _creer_interface(client, admin_token_headers, eq2["id"], "Eth0")

    response = client.post(
        "/connexions",
        json={
            "topologie_id": topo["id"],
            "source_equipement_id": eq1["id"],
            "source_interface_id": if2["id"],  # Interface de R2 sur R1 !
            "destination_equipement_id": eq2["id"],
            "destination_interface_id": if2["id"],
        },
        headers=admin_token_headers,
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_creer_connexion_topologie_inexistante(
    client, db_session, admin_token_headers, mock_gns3
):
    """Test connexion avec topologie inexistante."""
    # Créer une topologie valide avec équipements pour récupérer des IDs valides
    topo = _creer_topologie(client, admin_token_headers, "TopoForTest")
    eq1 = _creer_equipement(client, admin_token_headers, topo["id"], "R1", "10.0.1.1")
    eq2 = _creer_equipement(client, admin_token_headers, topo["id"], "R2", "10.0.1.2")
    if1 = _creer_interface(client, admin_token_headers, eq1["id"], "Eth0")
    if2 = _creer_interface(client, admin_token_headers, eq2["id"], "Eth0")

    response = client.post(
        "/connexions",
        json={
            "topologie_id": 9999,  # Topologie inexistante
            "source_equipement_id": eq1["id"],
            "source_interface_id": if1["id"],
            "destination_equipement_id": eq2["id"],
            "destination_interface_id": if2["id"],
        },
        headers=admin_token_headers,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_lister_connexions(
    client, db_session, admin_token_headers, mock_gns3
):
    """Test listage des connexions."""
    response = client.get("/connexions", headers=admin_token_headers)
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), list)


def test_supprimer_connexion_admin(
    client, db_session, admin_token_headers, mock_gns3
):
    """Test suppression d'une connexion par admin."""
    topo = _creer_topologie(client, admin_token_headers, "TopoDel")
    eq1 = _creer_equipement(client, admin_token_headers, topo["id"], "R1", "10.0.2.1")
    eq2 = _creer_equipement(client, admin_token_headers, topo["id"], "R2", "10.0.2.2")
    if1 = _creer_interface(client, admin_token_headers, eq1["id"], "Eth0")
    if2 = _creer_interface(client, admin_token_headers, eq2["id"], "Eth0")

    create = client.post(
        "/connexions",
        json={
            "topologie_id": topo["id"],
            "source_equipement_id": eq1["id"],
            "source_interface_id": if1["id"],
            "destination_equipement_id": eq2["id"],
            "destination_interface_id": if2["id"],
        },
        headers=admin_token_headers,
    )
    connexion_id = create.json()["id"]

    response = client.delete(
        f"/connexions/{connexion_id}",
        headers=admin_token_headers,
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_supprimer_connexion_unauthorized(
    client, db_session, normal_user_token_headers
):
    """Test suppression par un non-admin doit retourner 403."""
    response = client.delete(
        "/connexions/1",
        headers=normal_user_token_headers,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
