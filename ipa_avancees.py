
from interface import Vlan


class EquipementIntrouvableError(Exception):
     
    """Levée quand un équipement demandé n'existe pas."""     
    pass

def trouver_equipement(inventaires: list, equipement: Vlan) -> dict:
    if equipement not in inventaires:
        raise EquipementIntrouvableError(f"Aucun équipement avec id {equipement.id}")
    return equipement

def trouver_equipement(inventaires: list, equipement_id: int) -> dict:


    listIds=[]
    for el in inventaires:
        id= el.id
        listIds.append(id)
    print("Liste des ids de l'inventaires" + str(listIds))
    # Comprehension list
    ids= [inventaire.id for inventaire in inventaires]
    print("Liste des ids de l'inventaires par comprehension" + str(ids))



    if equipement_id not in ids:
        raise EquipementIntrouvableError(f"Aucun équipement avec id {equipement_id}")
    return "Equipement trouvé"

vlans= [Vlan(13,"VLAN 1", "Premier composant"),
        Vlan(5,"VLAN 1", "Second composant"),
        Vlan(7,"VLAN 1", "Troisième composant")]

#trouver_equipement(vlans, Vlan(13,"VLAN 1", "Premier composant"))
#trouver_equipement(vlans, Vlan(12, "VLAN 12", "QUATRIEME EQUIPEMENT"))

trouver_equipement(vlans, 13)
import time
from functools import wraps
def chronometre(fonction):
     
    """Mesure le temps d'exécution."""     @wraps(fonction)
    def wrapper(*args, **kwargs):
        debut = time.time()
        resultat = fonction(*args, **kwargs)
        duree = time.time() - debut
        print(f"{fonction.__name__} en {duree:.3f}s")
        return resultat
    return wrapper
@chronometre
def scanner_reseau(sous_reseau: str) -> list[str]:
    time.sleep(0.2)
    return ["10.0.0.1", "10.0.0.2"]
scanner_reseau("10.0.0.0/24") 
# scanner_reseau exécutée en 0.201s