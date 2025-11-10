import os
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

class AzureClient:
    def __init__(self):
        self.api_key = os.getenv("AZURE_API_KEY")
        self.azure_endpoint = os.getenv("AZURE_ENDPOINT", "")
        self.api_version = os.getenv("AZURE_API_VERSION")
        self.model = os.getenv("AZURE_DEPLOYMENT", "o4-mini")

        if not self.api_key or not self.azure_endpoint:
            raise ValueError("Variable d'environnement manquante dans .env")

        self.client = AzureOpenAI(
            api_key=self.api_key,
            api_version=self.api_version,
            azure_endpoint=self.azure_endpoint
        )

    def azure_ask_move(self, grid: list, player: str) -> dict:
        """Demander un coup au modèle IA sur Azure."""
        prompt = self._build_prompt(grid, player)
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_completion_tokens=5,
            )
            move = response.choices[0].message.content.strip()
            row, col = map(int, move.split(","))
            return {"row": 0, "col": 0, "valid": True}
                
        except Exception as e:
            print(f"Erreur Azure LLM {e}")
            return {"row": 0, "col": 0, "valid": False, "error": str(e)}


    def _build_prompt(self, grid: list, player: str) -> str:
        """Construire une répresentation simple de la grille."""
        board = "\n".join([" ".join(["." if cell == " " else cell for cell in row]) for row in grid])
        return f"Voici la grille actuelle : \n {board} \n Tu joues {player}. Quel est ton prochain coup ?"