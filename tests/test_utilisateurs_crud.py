"""
Tests pour le CRUD complet des utilisateurs (update/delete).
"""
import pytest
from fastapi import status


def test_modifier_utilisateur_admin(client, db_session, admin_user, admin_token_headers):
    """Test modification d'utilisateur avec rôle admin."""
    # Créer un utilisateur à modifier
    create_response = client.post(
        "/utilisateurs",
        json={
            "nom_utilisateur": "modifyme",
            "mot_de_passe": "oldpass123",
            "role": "lecteur",
        },
        headers=admin_token_headers,
    )
    assert create_response.status_code == status.HTTP_201_CREATED
    user_id = create_response.json()["id"]

    # Modifier l'utilisateur
    response = client.put(
        f"/utilisateurs/{user_id}",
        json={
            "nom_utilisateur": "modified",
            "mot_de_passe": "newpass123",
            "role": "operator",
        },
        headers=admin_token_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["nom_utilisateur"] == "modified"
    assert data["role"] == "operator"


def test_modifier_utilisateur_unauthorized(client, db_session, normal_user_token_headers, admin_user):
    """Test modification sans rôle admin doit retourner 403."""
    response = client.put(
        f"/utilisateurs/{admin_user.id}",
        json={"nom_utilisateur": "hack"},
        headers=normal_user_token_headers,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_modifier_utilisateur_not_found(client, db_session, admin_token_headers):
    """Test modification d'un utilisateur inexistant."""
    response = client.put(
        "/utilisateurs/9999",
        json={"nom_utilisateur": "nobody"},
        headers=admin_token_headers,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_modifier_utilisateur_self_deactivation_blocked(
    client, db_session, admin_user, admin_token_headers
):
    """Test qu'un admin ne peut pas se désactiver lui-même."""
    response = client.put(
        f"/utilisateurs/{admin_user.id}",
        json={"actif": False},
        headers=admin_token_headers,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "désactiver" in response.json()["detail"].lower()


def test_supprimer_utilisateur_admin(client, db_session, admin_token_headers, operator_user):
    """Test suppression d'utilisateur avec rôle admin."""
    response = client.delete(
        f"/utilisateurs/{operator_user.id}",
        headers=admin_token_headers,
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_supprimer_utilisateur_unauthorized(client, db_session, normal_user_token_headers, admin_user):
    """Test suppression sans rôle admin doit retourner 403."""
    response = client.delete(
        f"/utilisateurs/{admin_user.id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_supprimer_utilisateur_self_blocked(client, db_session, admin_user, admin_token_headers):
    """Test qu'un admin ne peut pas se supprimer lui-même."""
    response = client.delete(
        f"/utilisateurs/{admin_user.id}",
        headers=admin_token_headers,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "propre compte" in response.json()["detail"].lower()


def test_supprimer_utilisateur_not_found(client, db_session, admin_token_headers):
    """Test suppression d'un utilisateur inexistant."""
    response = client.delete(
        "/utilisateurs/9999",
        headers=admin_token_headers,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
