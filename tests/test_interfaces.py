"""
Tests pour les interfaces (CRUD + validation VLAN).
"""
import pytest
from fastapi import status


def _creer_equipement(client, headers, nom="Router1", ip="192.168.1.1"):
    """Helper pour créer un équipement de test."""
    response = client.post(
        "/equipements",
        json={
            "nom": nom,
            "adresse_ip": ip,
            "type_equipement": "routeur",
        },
        headers=headers,
    )
    return response.json() if response.status_code == 201 else None


def test_creer_interface(client, db_session, admin_token_headers):
    """Test création d'une interface."""
    equip = _creer_equipement(client, admin_token_headers)
    assert equip is not None

    response = client.post(
        "/interfaces",
        json={
            "nom": "GigabitEthernet0/0",
            "statut": "up",
            "vlan": 100,
            "equipement_id": equip["id"],
        },
        headers=admin_token_headers,
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["nom"] == "GigabitEthernet0/0"
    assert data["vlan"] == 100


def test_creer_interface_equipement_inexistant(client, db_session, admin_token_headers):
    """Test création d'interface avec équipement inexistant."""
    response = client.post(
        "/interfaces",
        json={
            "nom": "Eth0",
            "equipement_id": 9999,
        },
        headers=admin_token_headers,
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_creer_interface_vlan_invalide(client, db_session, admin_token_headers):
    """Test création d'interface avec VLAN hors plage (1-4094)."""
    equip = _creer_equipement(client, admin_token_headers, nom="R1", ip="10.0.0.1")

    # VLAN > 4094 doit échouer
    response = client.post(
        "/interfaces",
        json={
            "nom": "Eth0",
            "vlan": 5000,
            "equipement_id": equip["id"],
        },
        headers=admin_token_headers,
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # VLAN < 1 doit échouer
    response = client.post(
        "/interfaces",
        json={
            "nom": "Eth0",
            "vlan": 0,
            "equipement_id": equip["id"],
        },
        headers=admin_token_headers,
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_creer_interface_vlan_valide(client, db_session, admin_token_headers):
    """Test création d'interface avec VLAN valide."""
    equip = _creer_equipement(client, admin_token_headers, nom="R2", ip="10.0.0.2")

    # VLAN 1 (minimum)
    response = client.post(
        "/interfaces",
        json={"nom": "Eth0", "vlan": 1, "equipement_id": equip["id"]},
        headers=admin_token_headers,
    )
    assert response.status_code == status.HTTP_201_CREATED

    # VLAN 4094 (maximum)
    response = client.post(
        "/interfaces",
        json={"nom": "Eth1", "vlan": 4094, "equipement_id": equip["id"]},
        headers=admin_token_headers,
    )
    assert response.status_code == status.HTTP_201_CREATED


def test_lister_interfaces(client, db_session, admin_token_headers):
    """Test listage des interfaces."""
    equip = _creer_equipement(client, admin_token_headers, nom="R3", ip="10.0.0.3")
    client.post(
        "/interfaces",
        json={"nom": "Eth0", "equipement_id": equip["id"]},
        headers=admin_token_headers,
    )

    response = client.get("/interfaces", headers=admin_token_headers)
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), list)
    assert len(response.json()) >= 1


def test_obtenir_interface(client, db_session, admin_token_headers):
    """Test récupération d'une interface par ID."""
    equip = _creer_equipement(client, admin_token_headers, nom="R4", ip="10.0.0.4")
    create = client.post(
        "/interfaces",
        json={"nom": "Eth0", "equipement_id": equip["id"]},
        headers=admin_token_headers,
    )
    interface_id = create.json()["id"]

    response = client.get(f"/interfaces/{interface_id}", headers=admin_token_headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == interface_id


def test_modifier_interface(client, db_session, admin_token_headers):
    """Test modification d'une interface."""
    equip = _creer_equipement(client, admin_token_headers, nom="R5", ip="10.0.0.5")
    create = client.post(
        "/interfaces",
        json={"nom": "Eth0", "vlan": 10, "equipement_id": equip["id"]},
        headers=admin_token_headers,
    )
    interface_id = create.json()["id"]

    response = client.put(
        f"/interfaces/{interface_id}",
        json={"nom": "GigabitEthernet0/1", "vlan": 20},
        headers=admin_token_headers,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["nom"] == "GigabitEthernet0/1"
    assert data["vlan"] == 20


def test_supprimer_interface(client, db_session, admin_token_headers):
    """Test suppression d'une interface (admin only)."""
    equip = _creer_equipement(client, admin_token_headers, nom="R6", ip="10.0.0.6")
    create = client.post(
        "/interfaces",
        json={"nom": "Eth0", "equipement_id": equip["id"]},
        headers=admin_token_headers,
    )
    interface_id = create.json()["id"]

    response = client.delete(
        f"/interfaces/{interface_id}",
        headers=admin_token_headers,
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_supprimer_interface_unauthorized(client, db_session, normal_user_token_headers, admin_token_headers):
    """Test suppression d'interface par un non-admin doit retourner 403."""
    equip = _creer_equipement(client, admin_token_headers, nom="R7", ip="10.0.0.7")
    create = client.post(
        "/interfaces",
        json={"nom": "Eth0", "equipement_id": equip["id"]},
        headers=admin_token_headers,
    )
    interface_id = create.json()["id"]

    response = client.delete(
        f"/interfaces/{interface_id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
