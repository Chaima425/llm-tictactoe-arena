import os
import requests
import random
import re
from dotenv import load_dotenv
from azure_client import AzureClient

load_dotenv()

class LLMClient:
    def __init__(self):
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.recent_moves = []
        self.azure_client = AzureClient()

    def get_available_models(self) -> list:
        local_models = []
        try:
            response = requests.get(f"{self.ollama_url}/api/tags")
            if response.status_code == 200:
                local_models = [model['name'] for model in response.json().get('models', [])]
        except Exception:
            local_models = ["phi3:3.8b"]
        
        azure_models = self.azure_client.get_azure_models()
        return local_models + azure_models

    def ask_move(self, grid: list, player: str, model: str, max_attempts: int = 3) -> dict:
        """Demander un coup à un modèle (local ou Azure) avec validation"""
        empty_cells = [(i, j) for i in range(10) for j in range(10) if grid[i][j] == " "]
        if not empty_cells:
            return {"row": 0, "col": 0, "valid": False, "error": "grid_full"}
        
        if model.startswith("azure:"):
            for attempt in range(max_attempts):
                azure_response = self.azure_client.get_azure_move(grid, player, model)

                print(f"AzureClient response (attempt {attempt+1}): {azure_response}")
                
                # CORRECTION : Vérifier d'abord si la réponse contient une erreur
                if azure_response.get("error"):
                    print(f"AzureClient error: {azure_response.get('error')}")
                    if attempt == max_attempts - 1:  # Dernière tentative
                        break
                    continue
                
                # CORRECTION : Validation plus robuste
                if (self._is_valid_move(azure_response, grid) and 
                    azure_response.get("row", -1) >= 0 and 
                    azure_response.get("col", -1) >= 0):
                    
                    self.recent_moves.append((azure_response['row'], azure_response['col']))
                    if len(self.recent_moves) > 5:
                        self.recent_moves.pop(0)
                    return {"row": azure_response['row'], "col": azure_response['col'], "valid": True}
                else:
                    print(f"Azure a proposé un coup invalide ({azure_response.get('row')}, {azure_response.get('col')})")
                    
            # CORRECTION : Log clair de l'échec avant fallback
            print(f"INFO : Échec après {max_attempts} tentatives avec Azure. Utilisation d'un coup stratégique.")
            return self._select_strategic_move(empty_cells)
        
        # Pour les modèles locaux
        for attempt in range(max_attempts):
            prompt = self._create_prompt(grid, player, empty_cells, attempt)
            try:
                response = requests.post(
                    f"{self.ollama_url}/api/generate", 
                    json={
                        "model": model, 
                        "prompt": prompt, 
                        "stream": False,
                        "options": {"temperature": 0.3, "top_p": 0.3, "num_predict": 10}
                    }, 
                    timeout=20
                )
                
                if response.status_code == 200:
                    llm_response = response.json().get("response", "").strip()
                    parsed_move = self._parse_response(llm_response, empty_cells)
                    if self._is_valid_move(parsed_move, grid):
                        self.recent_moves.append((parsed_move['row'], parsed_move['col']))
                        if len(self.recent_moves) > 5:
                            self.recent_moves.pop(0)
                        return parsed_move
            except Exception as e:
                print(f"Erreur modèle local {model}: {e}")
                continue
        
        return self._select_strategic_move(empty_cells)

    # Le reste des méthodes reste inchangé...
    def _create_prompt(self, grid: list, player: str, empty_cells: list, attempt: int) -> str:
        grid_visual = "   0 1 2 3 4 5 6 7 8 9\n  +-------------------+\n"
        for i, row in enumerate(grid):
            grid_visual += f"{i} |" + "".join(f" {'.' if cell==' ' else cell}" for cell in row) + " |\n"
        grid_visual += "  +-------------------+\n"
        
        if attempt == 0:
            available_cells = [c for c in empty_cells if c not in self.recent_moves][:8]
            return f"{grid_visual}Player {player}, available cells: {available_cells}. Answer: row,column"
        elif attempt == 1:
            return f"{grid_visual}Player {player}, answer ONLY: row,column (e.g. 3,5)"
        else:
            return f"Player {player}, give two numbers (row, column): "

    def _parse_response(self, response: str, empty_cells: list) -> dict:
        patterns = [r'^\s*(\d)\s*,\s*(\d)\s*$', r'(\d)\s*[,.\-\s]?\s*(\d)']
        for pattern in patterns:
            match = re.search(pattern, response)
            if match: 
                row, col = int(match.group(1)), int(match.group(2))
                return self._validate_move(row, col, empty_cells, response)
        
        numbers = re.findall(r'\d', response)
        if len(numbers) >= 2: 
            return self._validate_move(int(numbers[0]), int(numbers[1]), empty_cells, response)
        
        return self._select_random_move(empty_cells, response)

    def _validate_move(self, row: int, col: int, empty_cells: list, response: str) -> dict:
        valid = (row, col) in empty_cells and (row, col) not in self.recent_moves
        return {"row": row, "col": col, "raw_response": response, "valid": valid}

    def _select_random_move(self, empty_cells: list, response: str) -> dict:
        non_recent = [c for c in empty_cells if c not in self.recent_moves]
        if not non_recent:
            non_recent = empty_cells
        row, col = random.choice(non_recent)
        return {"row": row, "col": col, "raw_response": f"random: {response}", "valid": True}

    def _select_strategic_move(self, empty_cells: list) -> dict:
        center_cells = [(4,4), (4,5), (5,4), (5,5)]
        for cell in center_cells:
            if cell in empty_cells and cell not in self.recent_moves:
                return {"row": cell[0], "col": cell[1], "raw_response": "strategic", "valid": True}
        return self._select_random_move(empty_cells, "fallback")

    def _is_valid_move(self, move: dict, grid: list) -> bool:
        row, col = move.get("row", -1), move.get("col", -1)
        return (0 <= row < 10 and 
                0 <= col < 10 and 
                grid[row][col] == " " and 
                (row, col) not in self.recent_moves)