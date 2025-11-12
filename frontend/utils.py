# utils.py: sert a regrpouper les fonction qui seront utiliser dans plusieurs fichiers frontend.
import requests
from typing import List
# utilitaire pour récupérer les modèles depuis le backend
def fetch_models(api_url: str) -> List[str]:
    """Récupérer la liste des modèles depuis le backend"""
    try:
        resp = requests.get(f"{api_url}/api/models", timeout=15)
        resp.raise_for_status()
        return resp.json().get("models", ["phi3"])
    except Exception as e:
        print(f"[Utils] Erreur récupération modèles: {e}")
        return ["phi3"]
    
# utilitaire pour envoyer des requêtes POST de manière sécurisée: avec gestion des erreurs
def safe_post(url: str, payload: dict) -> dict:
    """Envoi sécurisé POST request"""
    try:
        resp = requests.post(url, json=payload, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"[Utils] Erreur POST {url}: {e}")
        return {}

# utilitaire pour valider la grille
def validate_grid(grid, rows=10, cols=10):
    """Vérifie si la grille est valide"""
    return grid and len(grid) == rows and all(len(r) == cols for r in grid)

# utilitaire pour formater les cellules de la grille
def format_cell(cell_value):
    """Retourne le texte, la couleur du texte et la couleur de fond"""
    if cell_value == "X":
        return "X", "white", "red"
    elif cell_value == "O":
        return "O", "white", "blue"
    elif cell_value == "":
        # case vide 
        return "", "black","#DEDBD2"
    else:
        return "-", "black", "#DEDBD2"

