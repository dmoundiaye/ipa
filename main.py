

from fastapi import FastAPI, Request


app = FastAPI(title="API Inventaire Réseau", version="1.0.0")


@app.get("/")
def acceuil():
    return {
        "message": "L'API fonctionne correctement"
    }


INVENTAIRE_EN_MEMOIRE = [
    {"id": 1, "nom": "R1", "adresse_ip": "10.0.0.1", "type_equipement": "routeur"},
    {"id": 2, "nom": "SW1", "adresse_ip": "10.0.0.2", "type_equipement": "commutateur"},
    {"id": 3, "nom": "R2", "adresse_ip": "10.0.0.3", "type_equipement": "routeur"},
]


@app.get("/equipements")
def lister_equipements():
    return INVENTAIRE_EN_MEMOIRE

@app.get("/equipements/{id}")
def find_equimement(id : int):
    for equipement in INVENTAIRE_EN_MEMOIRE:
        if equipement['id']==id:        
            return {
                "id":id,
                "equipment":equipement
                    }
        return {"message":"equipement not found"}
            