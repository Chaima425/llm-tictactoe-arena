from dotenv import load_dotenv
from os import getenv
import requests
import json
import logging

load_dotenv()
logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self):
        self.ollama_url = getenv("OLLAMA_URL")

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
        """Demande un coup au LLM"""

        prompt = self._create_prompt(grid, player)

        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=30
            )
            if response.status_code == 200:
                llm_response = response.json().get("response", "").strip()
                return self._parse_response(llm_response)
            else:
                logger.error(f"Erreur LLM: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Erreur appel LLM: {e}")
        
        # Fallback: premier coup disponible
        return self._find_first_valid_move(grid)
    
    def _create_prompt(self, grid: list, player: str) -> str:
        """Créer le prompt pour le LLM"""
        grid_str = self._format_grid(grid)
        
        return f"""You are playing tic-tac-toe on a 10x10 grid. You are player “{player}”. 
        Rules: Line up 5 “{player}” horizontally, vertically or diagonally to win. 
        Current grid (rows 0-9, columns 0-9):{grid_str}
        Respond ONLY with coordinates in the format: ‘row,column’Example: ‘3,4’ for row 3, column 4.
        Choose a valid move (empty square). Your move:"""
    
    def _format_grid(self, grid: list) -> str:
        """Formater la grille pour l'affichage"""
        result = "   " + " ".join(str(i) for i in range(10)) + "\n"
        for i, row in enumerate(grid):
            result += f"{i:2} " + " ".join(cell if cell != " " else "." for cell in row) + "\n"
        return result
    
    def _parse_response(self, response: str) -> dict:
        """Parser la réponse du LLM"""
        try:
            # Extraire les nombres de la réponse
            import re
            numbers = re.findall(r'\d+', response)
            if len(numbers) >= 2:
                row, col = int(numbers[0]), int(numbers[1])
                return {"row": row, "col": col, "raw_response": response}
        except Exception as e:
            logger.error(f"Erreur parsing réponse: {response}, erreur: {e}")
        
        return {"row": 0, "col": 0, "raw_response": response, "error": "parse_failed"}
    
    def _find_first_valid_move(self, grid: list) -> dict:
        """Trouver le premier coup valide (fallback)"""
        for i in range(10):
            for j in range(10):
                if grid[i][j] == " ":
                    return {"row": i, "col": j, "raw_response": "fallback", "error": "llm_failed"}
        return {"row": 0, "col": 0, "raw_response": "no_moves"}