"""
Tests d'authentification et gestion des utilisateurs.
"""
import pytest
from fastapi import status
from sqlalchemy.orm import Session

from tests.conftest import client, db_session, normal_user_token_headers, admin_token_headers


def test_login(client, db_session, normal_user, admin_user):
    """Test login with valid credentials."""
    response = client.post(
        "/token",
        data={"username": normal_user.nom_utilisateur, "password": "testpass123"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_credentials(client, db_session, normal_user):
    """Test login with invalid credentials returns 401."""
    response = client.post(
        "/token",
        data={"username": normal_user.nom_utilisateur, "password": "wrongpassword"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_login_inactive_user(client, db_session, inactive_user):
    """Test login with inactive user returns 401."""
    response = client.post(
        "/token",
        data={"username": inactive_user.nom_utilisateur, "password": "testpass123"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_utilisateur_admin(client, db_session, admin_user, normal_user):
    """Test creating a user with admin role."""
    # First login as admin
    login_response = client.post(
        "/token",
        data={"username": admin_user.nom_utilisateur, "password": "testpass123"},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create a new user
    response = client.post(
        "/utilisateurs",
        json={"nom_utilisateur": "newuser", "mot_de_passe": "testpass123", "role": "admin"},
        headers=headers,
    )
    assert response.status_code == status.HTTP_201_CREATED


def test_create_utilisateur_duplicate(client, db_session, admin_user):
    """Test creating a duplicate user returns 409."""
    login_response = client.post(
        "/token",
        data={"username": admin_user.nom_utilisateur, "password": "testpass123"},
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create a user first
    response = client.post(
        "/utilisateurs",
        json={"nom_utilisateur": "newuser", "mot_de_passe": "testpass123", "role": "admin"},
        headers=headers,
    )
    assert response.status_code == status.HTTP_201_CREATED

    # Try to create the same user again - should fail with 409
    response = client.post(
        "/utilisateurs",
        json={"nom_utilisateur": "newuser", "mot_de_passe": "testpass456", "role": "lecteur"},
        headers=headers,
    )
    assert response.status_code == status.HTTP_409_CONFLICT


def test_get_my_profile(client, db_session, normal_user, normal_user_token_headers):
    """Test getting the current user's profile."""
    response = client.get("/utilisateurs/me", headers=normal_user_token_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["nom_utilisateur"] == normal_user.nom_utilisateur


def test_list_utilisateurs_admin(client, db_session, admin_user, admin_token_headers):
    """Test listing users with admin role."""
    response = client.get("/utilisateurs", headers=admin_token_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)


def test_list_utilisateurs_non_admin_403(client, db_session, normal_user, normal_user_token_headers):
    """Test listing users without admin role returns 403."""
    response = client.get("/utilisateurs", headers=normal_user_token_headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN