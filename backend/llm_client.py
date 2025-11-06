from dotenv import load_dotenv
from os import getenv
import requests
import logging
import re
import random

load_dotenv()
logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self):
        self.ollama_url = getenv("OLLAMA_URL", "http://localhost:11434")
        # Historique des coups récents pour éviter les répétitions
        self.recent_moves = []

    def get_available_models(self) -> list:
        """Récupérer les modèles disponibles dans Ollama"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get('models', [])
                return [model['name'] for model in models]
        except Exception as e:
            logger.error(f"Erreur de récupération du modèle: {e}")
        return ["llama2"]

    def ask_move(self, grid: list, player: str, model: str) -> dict:
        """Demande un coup au LLM avec système de retry amélioré"""
        
        # D'abord, obtenir toutes les cases vides
        empty_cells = [(i, j) for i in range(10) for j in range(10) if grid[i][j] == " "]
        if not empty_cells:
            return {"row": 0, "col": 0, "raw_response": "no_moves", "error": "grid_full"}
        
        # Essayer jusqu'à 3 fois avec des prompts de plus en plus stricts
        for attempt in range(3):
            if attempt == 0:
                prompt = self._create_prompt(grid, player, empty_cells)
            elif attempt == 1:
                prompt = self._create_strict_prompt(grid, player, empty_cells)
            else:
                # Dernière tentative, prompt ultra-simple
                prompt = f"Joueur {player}, donnez juste deux chiffres (ligne,colonne) entre 0-9 pour une case vide: "
            
            try:
                response = requests.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.3,
                            "top_p": 0.3,
                            "num_predict": 10
                        }
                    },
                    timeout=20
                )
                
                if response.status_code == 200:
                    llm_response = response.json().get("response", "").strip()
                    logger.info(f"Tentative {attempt+1} - Réponse LLM: {llm_response}")
                    
                    # Essayer de parser la réponse
                    parsed_move = self._parse_response(llm_response, empty_cells)
                    
                    # Validation finale
                    if self._is_valid_move(parsed_move, grid):
                        logger.info(f"Coup VALIDE trouvé: ({parsed_move['row']},{parsed_move['col']})")
                        
                        # Ajouter ce coup à l'historique
                        self.recent_moves.append((parsed_move['row'], parsed_move['col']))
                        if len(self.recent_moves) > 5:  # Garder seulement les 5 derniers coups
                            self.recent_moves.pop(0)
                        
                        return parsed_move
                    else:
                        logger.warning(f"Tentative {attempt+1} - Coup invalide: {parsed_move}")
                        
            except Exception as e:
                logger.error(f"Erreur tentative {attempt+1}: {e}")
        
        # Si après 3 tentatives ça ne marche pas, fallback stratégique
        logger.warning("Fallback stratégique après 3 échecs LLM")
        return self._select_strategic_move(empty_cells, "llm_failed_after_retry")

    def _create_prompt(self, grid: list, player: str, empty_cells: list) -> str:
        """Créer un prompt avec historique des coups pour éviter la répétition"""
        
        # Créer une représentation visuelle très claire
        grid_visual = self._create_visual_grid(grid)
        
        # Sélectionner des cases vides VARIÉES (pas toujours les mêmes)
        if len(empty_cells) > 8:
            # Prendre des cases de différentes zones de la grille
            zones = {
                'centre': [(4,4), (4,5), (5,4), (5,5)],
                'haut_gauche': [(0,0), (1,1), (2,2), (3,3)],
                'haut_droit': [(0,9), (1,8), (2,7), (3,6)],
                'bas_gauche': [(9,0), (8,1), (7,2), (6,3)],
                'bas_droit': [(9,9), (8,8), (7,7), (6,6)]
            }
            
            sample_empty = []
            for zone_name, zone_cells in zones.items():
                for cell in zone_cells:
                    if cell in empty_cells and cell not in sample_empty and cell not in self.recent_moves:
                        sample_empty.append(cell)
                        if len(sample_empty) >= 8:
                            break
                if len(sample_empty) >= 8:
                    break
                    
            # Compléter avec des cases aléatoires si nécessaire
            while len(sample_empty) < 8 and len(empty_cells) > len(sample_empty):
                new_cell = random.choice([c for c in empty_cells if c not in sample_empty and c not in self.recent_moves])
                sample_empty.append(new_cell)
        else:
            sample_empty = [c for c in empty_cells if c not in self.recent_moves]
        
        available_info = ", ".join([f"({r},{c})" for r, c in sample_empty])
        recent_moves_info = ", ".join([f"({r},{c})" for r, c in self.recent_moves])

        return f"""JEU DE MORPION - TOUR {player}

GRILLE ACTUELLE :
{grid_visual}

COUPS RÉCENTS (à éviter de répéter) : {recent_moves_info}

INSTRUCTIONS CRITIQUES :
- Vous êtes le joueur {player}
- Évitez ABSOLUMENT les coups récents : {recent_moves_info}
- Choisissez une case VARIÉE, pas toujours la même zone
- Répondez UNIQUEMENT avec deux chiffres séparés par une virgule
- Format : ligne,colonne (exemple: "3,8")
- Chiffres entre 0 et 9 uniquement

CASES VIDES DIVERSIFIÉES : {available_info}

VOTRE COUP (choisissez une case VARIÉE qui n'est pas dans les coups récents) :"""

    def _create_strict_prompt(self, grid: list, player: str, empty_cells: list) -> str:
        """Prompt ULTRA-STRICT avec interdiction explicite"""
        grid_visual = self._create_visual_grid(grid)
        
        # Identifier les cases souvent répétées et les coups récents
        forbidden_cells = [(4,7), (4,5), (4,6)]  # Les cases obsessionnelles
        forbidden_cells.extend(self.recent_moves)  # Ajouter les coups récents
        
        available_cells = [cell for cell in empty_cells if cell not in forbidden_cells]
        if not available_cells:  # Si toutes les cases sont interdites, on prend toutes
            available_cells = empty_cells
        
        sample_available = random.sample(available_cells, min(6, len(available_cells)))
        available_info = ", ".join([f"({r},{c})" for r, c in sample_available])
        recent_moves_info = ", ".join([f"({r},{c})" for r, c in self.recent_moves])
        
        return f"""MORPION - TOUR {player} - ULTIMATUM

GRILLE :
{grid_visual}

INTERDICTION ABSOLUE :
- NE PAS JOUER : {recent_moves_info}
- NE PAS JOUER : (4,7), (4,5), (4,6)
- Ces cases sont DÉJÀ OCCUPÉES ou TROP UTILISÉES

CASES AUTORISÉES : {available_info}

DERNIER AVERTISSEMENT :
- RÉPONDEZ UNIQUEMENT : chiffre,chiffre  
- CHOISISSEZ parmi les cases AUTORISÉES ci-dessus
- EXEMPLE : 2,8 ou 7,3 ou 1,9

RÉPONSE IMMÉDIATE (chiffre,chiffre des cases AUTORISÉES) :"""

    def _create_visual_grid(self, grid: list) -> str:
        """Créer une représentation visuelle très claire"""
        result = "   0 1 2 3 4 5 6 7 8 9\n"
        result += "  +-------------------+\n"
        
        for i, row in enumerate(grid):
            line = f"{i} |"
            for cell in row:
                if cell == " ":
                    line += " ."  # Case vide
                elif cell == "X":
                    line += " X"
                elif cell == "O":
                    line += " O"
            line += " |\n"
            result += line
        
        result += "  +-------------------+\n"
        result += "Légende : '.' = vide, 'X' = joueur X, 'O' = joueur O"
        
        return result

    def _parse_response(self, response: str, empty_cells: list) -> dict:
        """Parser avec pénalité pour les cases répétitives"""
        try:
            # Nettoyer radicalement la réponse
            cleaned = response.strip()
            
            # STRATÉGIE 1: Chercher le pattern exact "chiffre,chiffre"
            exact_pattern = r'^\s*(\d)\s*,\s*(\d)\s*$'
            match = re.search(exact_pattern, cleaned)
            if match:
                row, col = int(match.group(1)), int(match.group(2))
                return self._evaluate_move(row, col, empty_cells, response)
            
            # STRATÉGIE 2: Chercher la PREMIÈRE occurrence de deux chiffres séparés
            first_pattern = r'(\d)\s*[,.\-\s]?\s*(\d)'
            match = re.search(first_pattern, cleaned)
            if match:
                row, col = int(match.group(1)), int(match.group(2))
                return self._evaluate_move(row, col, empty_cells, response)
            
            # STRATÉGIE 3: Extraire tous les chiffres et prendre les 2 premiers
            numbers = re.findall(r'\d', cleaned)
            if len(numbers) >= 2:
                row, col = int(numbers[0]), int(numbers[1])
                return self._evaluate_move(row, col, empty_cells, response)
                
        except Exception as e:
            logger.error(f"Erreur parsing: {e}")
        
        # Dernier recours - choisir une case aléatoire
        return self._select_random_move(empty_cells, response)

    def _evaluate_move(self, row: int, col: int, empty_cells: list, response: str) -> dict:
        """Évaluer un move avec pénalité pour répétition"""
        # Cases "obsessionnelles" à éviter
        obsessive_cells = [(4,7), (4,5), (4,6)]
        
        if (row, col) in empty_cells and (row, col) not in self.recent_moves:
            # Pénalité si c'est une case obsessionnelle
            if (row, col) in obsessive_cells:
                logger.warning(f"Case obsessionnelle détectée: ({row},{col})")
                # On l'accepte mais on note le problème
                return {"row": row, "col": col, "raw_response": response, "valid": True, "obsessive": True}
            else:
                return {"row": row, "col": col, "raw_response": response, "valid": True}
        elif 0 <= row < 10 and 0 <= col < 10:
            return {"row": row, "col": col, "raw_response": response, "valid": False, "reason": "occupied_or_recent"}
        else:
            return {"row": row, "col": col, "raw_response": response, "valid": False, "reason": "out_of_bounds"}

    def _select_random_move(self, empty_cells: list, response: str) -> dict:
        """Choisir un move aléatoire parmi les cases vides qui ne sont pas récentes"""
        if not empty_cells:
            return {"row": 0, "col": 0, "raw_response": response, "error": "no_cells"}
        
        # Éviter les cases récentes
        non_recent = [cell for cell in empty_cells if cell not in self.recent_moves]
        
        if non_recent:
            row, col = random.choice(non_recent)
            return {"row": row, "col": col, "raw_response": f"random_fallback: {response}", "valid": True}
        
        # Si toutes les cases sont récentes (cas rare), prendre une case aléatoire
        row, col = random.choice(empty_cells)
        return {"row": row, "col": col, "raw_response": f"random_fallback: {response}", "valid": True}

    def _is_valid_move(self, move: dict, grid: list) -> bool:
        """Vérifier si le coup est valide"""
        row, col = move.get("row", -1), move.get("col", -1)
        return (0 <= row < 10 and 0 <= col < 10 and 
                grid[row][col] == " " and 
                (row, col) not in self.recent_moves)

    def _select_strategic_move(self, empty_cells: list, reason: str) -> dict:
        """Choisir un coup stratégique parmi les cases vides"""
        if not empty_cells:
            return {"row": 0, "col": 0, "raw_response": reason, "error": "no_cells"}
        
        # Priorité aux cases centrales qui ne sont pas récentes
        center_cells = [(4,4), (4,5), (5,4), (5,5), (3,3), (3,6), (6,3), (6,6)]
        for cell in center_cells:
            if cell in empty_cells and cell not in self.recent_moves:
                return {"row": cell[0], "col": cell[1], "raw_response": f"strategic_center: {reason}"}
        
        # Sinon, prendre une case non récente au hasard
        non_recent = [cell for cell in empty_cells if cell not in self.recent_moves]
        if non_recent:
            cell = random.choice(non_recent)
            return {"row": cell[0], "col": cell[1], "raw_response": f"random_fallback: {reason}"}
        
        # Si toutes les cases sont récentes, prendre une case au hasard
        cell = random.choice(empty_cells)
        return {"row": cell[0], "col": cell[1], "raw_response": f"random_fallback: {reason}"}

    def _find_first_valid_move(self, grid: list) -> dict:
        """Trouver le premier coup valide (fallback)"""
        for i in range(10):
            for j in range(10):
                if grid[i][j] == " " and (i, j) not in self.recent_moves:
                    return {"row": i, "col": j, "raw_response": "first_available"}
        return {"row": 0, "col": 0, "raw_response": "no_moves"}