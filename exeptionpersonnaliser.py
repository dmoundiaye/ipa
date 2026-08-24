from dataclasses import dataclass

@dataclass
class Chronometre:
    temps: float = 0

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
# scanner_reseau exécutée en 0.201