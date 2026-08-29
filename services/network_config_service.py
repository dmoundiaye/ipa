"""
Service de configuration réseau via Netmiko.

Permet d'envoyer des commandes de configuration aux équipements réseau
(réels ou simulés) via SSH.
"""

import logging
from typing import Optional, Any

logger = logging.getLogger("inventory-app")


class NetworkConfigService:
    """
    Service pour la configuration distante des équipements réseau.

    Utilise Netmiko pour se connecter en SSH aux équipements
    et envoyer des commandes de configuration.
    """

    def __init__(
        self,
        username: str = "admin",
        password: str = "",
        secret: str = "",
        device_type: str = "cisco_ios",
        timeout: int = 30,
    ):
        """
        Initialise le service de configuration.

        Args:
            username: Nom d'utilisateur SSH
            password: Mot de passe SSH
            secret: Mot de passe enable (si nécessaire)
            device_type: Type d'appareil Netmiko (cisco_ios, cisco_nxos, etc.)
            timeout: Timeout en secondes pour les connexions
        """
        self.username = username
        self.password = password
        self.secret = secret or password
        self.device_type = device_type
        self.timeout = timeout

    def _get_connection_params(
        self,
        host: str,
        port: int = 22,
    ) -> dict[str, Any]:
        """Retourne les paramètres de connexion pour Netmiko."""
        return {
            "host": host,
            "port": port,
            "username": self.username,
            "password": self.password,
            "secret": self.secret,
            "device_type": self.device_type,
            "timeout": self.timeout,
            "banner_timeout": 20,
            "session_timeout": 60,
        }

    def send_command(
        self,
        host: str,
        command: str,
        port: int = 22,
    ) -> str:
        """
        Envoie une commande unique à un équipement et retourne la sortie.

        Args:
            host: Adresse IP de l'équipement
            command: Commande à envoyer
            port: Port SSH (défaut: 22)

        Returns:
            Sortie de la commande

        Raises:
            Exception: Si la connexion ou l'exécution échoue
        """
        try:
            from netmiko import ConnectHandler

            params = self._get_connection_params(host, port)
            logger.info(f"Connexion SSH à {host}...")

            with ConnectHandler(**params) as conn:
                output = conn.send_command(command)
                logger.info(
                    f"Commande exécutée sur {host}: {command[:50]}..."
                )
                return output

        except ImportError:
            logger.error("Netmiko n'est pas installé. pip install netmiko")
            raise Exception(
                "Module Netmiko non disponible. "
                "Installez-le avec: pip install netmiko"
            )
        except Exception as e:
            logger.error(f"Erreur SSH vers {host}: {e}")
            raise

    def send_config(
        self,
        host: str,
        config_commands: list[str],
        port: int = 22,
    ) -> str:
        """
        Envoie une liste de commandes de configuration à un équipement.

        Args:
            host: Adresse IP de l'équipement
            config_commands: Liste de commandes de configuration
            port: Port SSH (défaut: 22)

        Returns:
            Sortie des commandes de configuration

        Raises:
            Exception: Si la connexion ou l'exécution échoue
        """
        try:
            from netmiko import ConnectHandler

            params = self._get_connection_params(host, port)
            logger.info(f"Connexion SSH à {host} pour configuration...")

            with ConnectHandler(**params) as conn:
                # Passer en mode enable si nécessaire
                if conn.secret:
                    try:
                        conn.enable()
                    except Exception:
                        pass

                output = conn.send_config_set(config_commands)
                conn.save_config()

                logger.info(
                    f"Configuration appliquée sur {host} "
                    f"({len(config_commands)} commandes)"
                )
                return output

        except ImportError:
            logger.error("Netmiko n'est pas installé. pip install netmiko")
            raise Exception(
                "Module Netmiko non disponible. "
                "Installez-le avec: pip install netmiko"
            )
        except Exception as e:
            logger.error(f"Erreur de configuration SSH vers {host}: {e}")
            raise

    def apply_interface_config(
        self,
        host: str,
        interface_name: str,
        description: str = "",
        vlan: Optional[int] = None,
        duplex: str = "auto",
        speed: str = "auto",
        shutdown: bool = False,
    ) -> str:
        """
        Applique une configuration d'interface standard.

        Args:
            host: Adresse IP de l'équipement
            interface_name: Nom de l'interface (ex: GigabitEthernet0/0)
            description: Description de l'interface
            vlan: VLAN à affecter (optionnel)
            duplex: Mode duplex (auto, full, half)
            speed: Vitesse (auto, 100, 1000, etc.)
            shutdown: True pour désactiver l'interface

        Returns:
            Sortie de la configuration
        """
        commands = [
            f"interface {interface_name}",
        ]

        if description:
            commands.append(f"description {description}")

        if shutdown:
            commands.append("shutdown")
        else:
            commands.append("no shutdown")

        if vlan is not None:
            commands.append(f"switchport trunk allowed vlan {vlan}")
            commands.append("switchport mode trunk")

        commands.append(f"speed {speed}")
        commands.append(f"duplex {duplex}")
        commands.append("exit")

        return self.send_config(host, commands)

    def get_interface_status(
        self,
        host: str,
        interface_name: str,
    ) -> str:
        """
        Récupère le statut d'une interface.

        Args:
            host: Adresse IP de l'équipement
            interface_name: Nom de l'interface

        Returns:
            Statut de l'interface (format texte)
        """
        command = f"show interface {interface_name}"
        return self.send_command(host, command)

    def get_running_config(
        self,
        host: str,
    ) -> str:
        """
        Récupère la configuration en cours d'un équipement.

        Args:
            host: Adresse IP de l'équipement

        Returns:
            Configuration en cours
        """
        command = "show running-config"
        return self.send_command(host, command)


# Instance par défaut (sera configurée via les variables d'environnement)
_network_config_service: Optional[NetworkConfigService] = None


def get_network_config_service() -> NetworkConfigService:
    """
    Retourne le service de configuration réseau (singleton).

    Configure le service depuis les variables d'environnement:
    - NETWORK_SSH_USERNAME
    - NETWORK_SSH_PASSWORD
    - NETWORK_SSH_SECRET (optionnel)
    - NETWORK_DEVICE_TYPE (défaut: cisco_ios)
    """
    global _network_config_service

    if _network_config_service is None:
        import os

        _network_config_service = NetworkConfigService(
            username=os.getenv("NETWORK_SSH_USERNAME", "admin"),
            password=os.getenv("NETWORK_SSH_PASSWORD", ""),
            secret=os.getenv("NETWORK_SSH_SECRET", ""),
            device_type=os.getenv("NETWORK_DEVICE_TYPE", "cisco_ios"),
        )

    return _network_config_service
