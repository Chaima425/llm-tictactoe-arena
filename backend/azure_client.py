import os
import re
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

class AzureClient:
    def __init__(self):
        self.api_key = os.getenv("AZURE_API_KEY")
        self.azure_endpoint = os.getenv("AZURE_ENDPOINT", "")
        self.api_version = os.getenv("AZURE_API_VERSION", "2024-02-01")
        self.model = os.getenv("AZURE_MODELS", "gpt-4o-mini").split(",")[0].strip()

        if not self.api_key or not self.azure_endpoint:
            print("Variables Azure manquantes - utilisation des modèles locaux seulement")
            self.client = None
        else:
            try:
                self.client = AzureOpenAI(
                    api_key=self.api_key,
                    api_version=self.api_version,
                    azure_endpoint=self.azure_endpoint
                )
                print("Client Azure OpenAI initialisé")
            except Exception as e:
                print(f"Erreur initialisation Azure: {e}")
                self.client = None
    
    def get_azure_models(self):
        """Retourne la liste des modèles Azure configurés."""
        if not self.client:
            return []
            
        models_env = os.getenv("AZURE_MODELS", "gpt-4")
        return [f"azure:{model.strip()}" for model in models_env.split(",") if model.strip()]

    def get_azure_move(self, grid: list, player: str, model_name: str) -> dict:
        """Demander un coup à Azure - retourne la réponse brute sans validation"""
        if not self.client:
            return {"row": -1, "col": -1, "raw_response": "", "error": "Client Azure non initialisé"}
            
        actual_model = model_name.replace("azure:", "") if model_name and model_name.startswith("azure:") else self.model
        
        prompt = self._build_prompt(grid, player)
        print(f"[DEBUG Azure] Modèle utilisé: {actual_model}")
        print(f"[DEBUG Azure] Prompt envoyé: {prompt}")
        
        try:
            response = self.client.chat.completions.create(
                model=actual_model,
                messages=[
                    {"role": "system", "content": (
                        "You are an expert Tic-Tac-Toe player on a 10x10 grid. "
                        "Your ONLY task is to provide your next move as two comma-separated digits (row,column). "
                        "For example, if you want to play at row 3, column 7, your response MUST be '3,7'. "
                        "DO NOT include any other text, greetings, explanations, or formatting whatsoever. "
                        "You must only output 'row,column'."
                        "Victory condition: line up 5 identical elements horizontally, vertically or diagonally."
                        "Defeat condition: if your opponent fulfils the victory condition, you must block these potentially winning moves."
                        "Prioritises victory first and blocking second."
                    )},
                    {"role": "user", "content": prompt}
                ],
                max_completion_tokens=20,
            )
            
            print(f"[DEBUG Azure] Réponse complète reçue: {response}")
            
            # Vérification détaillée de la réponse
            if not response.choices:
                print("[DEBUG Azure] Erreur : L'API a renvoyé une réponse sans 'choices'.")
                return {"row": -1, "col": -1, "raw_response": "", "error": "Réponse sans choices de l'API Azure"}
                
            if not response.choices[0]:
                print("[DEBUG Azure] Erreur : Le premier choix dans 'choices' est vide.")
                return {"row": -1, "col": -1, "raw_response": "", "error": "Premier choix vide de l'API Azure"}
                
            if not response.choices[0].message:
                print("[DEBUG Azure] Erreur : Le 'message' dans le premier choix est vide.")
                return {"row": -1, "col": -1, "raw_response": "", "error": "Message vide de l'API Azure"}
                
            if response.choices[0].message.content is None:
                print("[DEBUG Azure] Erreur : Le 'content' dans le message est None.")
                return {"row": -1, "col": -1, "raw_response": "", "error": "Content None de l'API Azure"}
                    
            move = response.choices[0].message.content.strip()
            
            if not move:
                print("[DEBUG Azure] Erreur : L'API a renvoyé un contenu vide après nettoyage.")
                return {"row": -1, "col": -1, "raw_response": "", "error": "Réponse vide de l'API Azure"}

            print(f"[DEBUG Azure] Réponse brute: '{move}'")

            # Le reste de votre code d'analyse...
            patterns = [
                r'^\s*(\d)\s*,\s*(\d)\s*$',  # 4,5
                r'^\s*(\d)\s+(\d)\s*$',      # 4 5
                r'\(\s*(\d)\s*,\s*(\d)\s*\)', # (4,5)
                r'row\s*(\d).*col\s*(\d)',   # row 4 col 5
                r'(\d+)\s*(\d+)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, move, re.IGNORECASE)
                if match:
                    row, col = int(match.group(1)), int(match.group(2))
                    print(f"[DEBUG Azure] Pattern '{pattern}' match: ({row}, {col})")
                    return {"row": row, "col": col, "raw_response": move}
            
            print(f"[DEBUG Azure] Format de réponse Azure invalide: '{move}'")
            return {"row": -1, "col": -1, "raw_response": move, "error": f"Format invalide: '{move}'"}
                
        except Exception as e:
            print(f"[DEBUG Azure] Exception lors de l'appel API: {e}")
            import traceback
            traceback.print_exc()
            return {"row": -1, "col": -1, "raw_response": "", "error": str(e)}

    def _build_prompt(self, grid: list, player: str, history: list = None) -> str: # type: ignore
        """
        Construit un prompt enrichi contenant :
        - la grille actuelle
        - l'historique des coups précédents
        - les instructions claires pour le modèle
        """
        # Historique des coups
        history_text = ""
        if history:
            history_text = "Historique des coups précédents :\n" + "\n".join(
                [f"Tour {i+1}: Joueur {p} -> {r},{c}" for i, (p, r, c) in enumerate(history)]
            ) + "\n\n"

        # Représentation textuelle de la grille
        board = "\n".join([
            f"{i}: " + " ".join(["." if cell == " " else cell for cell in row]) 
            for i, row in enumerate(grid)
        ])

        prompt = (
            f"{history_text}"
            f"Current 10x10 grid (rows 0-9, columns 0-9) :\n{board}\n\n"
            f"You are playing as '{player}'. "
            "Your goal is to win by lining up 5 identical symbols. "
            "If your opponent is about to win, block them immediately. "
            "Respond only with the coordinates 'row,column' (e.g. 3,7)."
        )
        return prompt