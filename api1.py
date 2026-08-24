from fastapi import FastAPI
app = FastAPI(title="API Inventaire Réseau", version="1.0.0")
@app.get("/")
def racine():
    """Confirme que l'API répond.""" 
    return {"message": "API opérationnelle"} # Étape 1 : inventaire "en dur", en mémoire (remplacé en 2.4) 
INVENTAIRE_EN_MEMOIRE = [
    {"id": 1, "nom": "R1", "adresse_ip": "10.0.0.1", "type_equipement": "routeur"},
    {"id": 2, "nom": "SW1", "adresse_ip": "10.0.0.2", "type_equipement": "commutateur"},
]
@app.get("/equipements")
def lister_equipements():
    return INVENTAIRE_EN_MEMOIRE

@app.get("/equipements/{equipement_id}")
def obtenir_equipement(id: int):
    for equipement in INVENTAIRE_EN_MEMOIRE:
        if equipement["id"] == id:
            return equipement
    return {"message": "Équipement non trouvé"}
