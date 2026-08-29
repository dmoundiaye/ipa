"""
Tests pour les topologies (CRUD).
"""
from unittest.mock import patch, MagicMock

import pytest
from fastapi import status


# Mock du service GNS3 pour éviter de vraies requêtes
@pytest.fixture(autouse=True)
def mock_gns3():
    """Mock le service d'association GNS3 pour les tests."""
    with patch("routes.topologies.association_service") as mock_assoc:
        # Mock pour la création de topologie
        mock_assoc.get_or_create_gns3_project.return_value = "test-project-id-123"
        # Mock pour la suppression
        mock_assoc.delete_gns3_project.return_value = True
        yield mock_assoc


def test_creer_topologie(client, db_session, admin_token_headers):
    """Test création d'une topologie avec synchronisation GNS3."""
    response = client.post(
        "/topologies",
        json={
            "nom": "Test Topology",
            "description": "Une topologie de test",
        },
        headers=admin_token_headers,
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["nom"] == "Test Topology"
    assert data["statut"] == "brouillon"
    # Vérifier la synchronisation GNS3
    assert data.get("gns3_project_id") == "test-project-id-123"
    assert data.get("synced_with_gns3") is True


def test_lister_topologies(client, db_session, admin_token_headers, mock_gns3):
    """Test listage des topologies."""
    # Créer au moins une topologie
    client.post(
        "/topologies",
        json={"nom": "Topology1"},
        headers=admin_token_headers,
    )
    response = client.get("/topologies", headers=admin_token_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_obtenir_topologie(client, db_session, admin_token_headers, mock_gns3):
    """Test récupération d'une topologie par ID."""
    create_response = client.post(
        "/topologies",
        json={"nom": "MyTopology"},
        headers=admin_token_headers,
    )
    topologie_id = create_response.json()["id"]

    response = client.get(
        f"/topologies/{topologie_id}",
        headers=admin_token_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["nom"] == "MyTopology"


def test_obtenir_topologie_not_found(client, db_session, admin_token_headers):
    """Test récupération d'une topologie inexistante."""
    response = client.get(
        "/topologies/9999",
        headers=admin_token_headers,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_modifier_topologie(client, db_session, admin_token_headers, mock_gns3):
    """Test modification d'une topologie."""
    create_response = client.post(
        "/topologies",
        json={"nom": "OldName"},
        headers=admin_token_headers,
    )
    topologie_id = create_response.json()["id"]

    response = client.put(
        f"/topologies/{topologie_id}",
        json={"nom": "NewName", "statut": "actif"},
        headers=admin_token_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["nom"] == "NewName"
    assert data["statut"] == "actif"


def test_modifier_topologie_unauthorized(client, db_session, normal_user_token_headers, mock_gns3):
    """Test modification sans permissions."""
    response = client.put(
        "/topologies/1",
        json={"nom": "hack"},
        headers=normal_user_token_headers,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_supprimer_topologie(client, db_session, admin_token_headers, mock_gns3):
    """Test suppression d'une topologie (et nettoyage GNS3)."""
    create_response = client.post(
        "/topologies",
        json={"nom": "ToDelete"},
        headers=admin_token_headers,
    )
    topologie_id = create_response.json()["id"]

    response = client.delete(
        f"/topologies/{topologie_id}",
        headers=admin_token_headers,
    )
    assert response.status_code in [status.HTTP_204_NO_CONTENT, status.HTTP_200_OK]

    # Vérifier que la suppression du projet GNS3 a été appelée
    mock_gns3.delete_gns3_project.assert_called()


def test_creer_topologie_gns3_failure(client, db_session, admin_token_headers):
    """Test création quand GNS3 échoue (la topologie doit quand même être créée)."""
    with patch("routes.topologies.association_service") as mock_assoc:
        mock_assoc.get_or_create_gns3_project.side_effect = Exception("GNS3 down")

        response = client.post(
            "/topologies",
            json={"nom": "OfflineTopology"},
            headers=admin_token_headers,
        )
        # La topologie doit être créée même si GNS3 échoue
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["nom"] == "OfflineTopology"
        assert data["synced_with_gns3"] is False
