"""
Tests sur les équipements (CRUD + RBAC + unicité IP).
"""
import pytest
from fastapi import status


def test_create_equipement(client, db_session, admin_user, admin_token_headers):
    """Test creating an equipment with admin role."""
    response = client.post(
        "/equipements",
        json={
            "nom": "Router1",
            "adresse_ip": "192.168.1.1",
            "type_equipement": "routeur",
        },
        headers=admin_token_headers,
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["nom"] == "Router1"
    assert data["adresse_ip"] == "192.168.1.1"
    assert data["actif"] is True


def test_create_equipement_invalid_ip(client, db_session, admin_token_headers):
    """Test creating an equipment with invalid IP returns 422."""
    response = client.post(
        "/equipements",
        json={
            "nom": "Router1",
            "adresse_ip": "not-an-ip",
            "type_equipement": "routeur",
        },
        headers=admin_token_headers,
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_equipement_duplicate_ip(client, db_session, admin_token_headers):
    """Test creating an equipment with duplicate IP returns 409."""
    # Create first equipment
    client.post(
        "/equipements",
        json={
            "nom": "Router1",
            "adresse_ip": "192.168.1.1",
            "type_equipement": "routeur",
        },
        headers=admin_token_headers,
    )
    # Try to create another with same IP
    response = client.post(
        "/equipements",
        json={
            "nom": "Router2",
            "adresse_ip": "192.168.1.1",
            "type_equipement": "routeur",
        },
        headers=admin_token_headers,
    )
    assert response.status_code == status.HTTP_409_CONFLICT


def test_get_equipements(client, db_session, admin_token_headers):
    """Test listing equipment."""
    client.post(
        "/equipements",
        json={
            "nom": "Router1",
            "adresse_ip": "192.168.1.1",
            "type_equipement": "routeur",
        },
        headers=admin_token_headers,
    )
    response = client.get("/equipements", headers=admin_token_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_get_equipement_by_id(client, db_session, admin_token_headers):
    """Test getting a single equipment by ID."""
    response = client.post(
        "/equipements",
        json={
            "nom": "Router1",
            "adresse_ip": "192.168.1.1",
            "type_equipement": "routeur",
        },
        headers=admin_token_headers,
    )
    equipement_id = response.json()["id"]

    response = client.get(f"/equipements/{equipement_id}", headers=admin_token_headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == equipement_id


def test_get_equipement_not_found(client, db_session, admin_token_headers):
    """Test getting a non-existent equipment returns 404."""
    response = client.get("/equipements/9999", headers=admin_token_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_equipement(client, db_session, admin_token_headers):
    """Test updating an equipment."""
    response = client.post(
        "/equipements",
        json={
            "nom": "Router1",
            "adresse_ip": "192.168.1.1",
            "type_equipement": "routeur",
        },
        headers=admin_token_headers,
    )
    equipement_id = response.json()["id"]

    response = client.put(
        f"/equipements/{equipement_id}",
        json={"nom": "Router1-Updated"},
        headers=admin_token_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["nom"] == "Router1-Updated"


def test_delete_equipement(client, db_session, admin_token_headers):
    """Test deleting an equipment."""
    response = client.post(
        "/equipements",
        json={
            "nom": "Router1",
            "adresse_ip": "192.168.1.1",
            "type_equipement": "routeur",
        },
        headers=admin_token_headers,
    )
    equipement_id = response.json()["id"]

    response = client.delete(f"/equipements/{equipement_id}", headers=admin_token_headers)
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_create_equipement_unauthorized(client, db_session, normal_user_token_headers):
    """Test creating an equipment without authorization returns 403."""
    response = client.post(
        "/equipements",
        json={
            "nom": "Router1",
            "adresse_ip": "192.168.1.1",
            "type_equipement": "routeur",
        },
        headers=normal_user_token_headers,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_create_equipement_no_token(client, db_session):
    """Test creating an equipment without token returns 401."""
    response = client.post(
        "/equipements",
        json={
            "nom": "Router1",
            "adresse_ip": "192.168.1.1",
            "type_equipement": "routeur",
        },
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_delete_equipement_unauthorized(client, db_session, normal_user_token_headers):
    """Test deleting an equipment without admin role returns 403."""
    # Create equipment as admin first
    admin_headers = {"Authorization": "Bearer admin_token"}
    # We need a real admin token, so use the fixture instead
    # (This test uses normal_user which should not be able to delete)
    response = client.delete("/equipements/1", headers=normal_user_token_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN