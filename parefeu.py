def diviser(a: float, b: float) -> float:
    return a / b

try:
    resultat = diviser(10, 0)
except ZeroDivisionError as e:
    print(f"Erreur : {e}")
except (ValueError, TypeError) as e:
    print(f"Erreur de valeur/type : {e}")
else:
    # Exécuté si AUCUNE exception
    print("Résultat :", resultat)
finally:
    # Exécuté systématiquement
    print("Nettoyage effectué")