import os
import re
import logging
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AzureClient:
    def __init__(self):
        self.api_key = os.getenv("AZURE_API_KEY")
        self.azure_endpoint = os.getenv("AZURE_ENDPOINT", "")
        self.api_version = os.getenv("AZURE_API_VERSION", "2024-02-01")
        self.model = os.getenv("AZURE_MODELS", "gpt-4o-mini").split(",")[0].strip()

        if not self.api_key or not self.azure_endpoint:
            logger.warning("Variables Azure manquantes - utilisation des modèles locaux seulement")
            self.client = None
        else:
            try:
                self.client = AzureOpenAI(
                    api_key=self.api_key,
                    api_version=self.api_version,
                    azure_endpoint=self.azure_endpoint
                )
                logger.info("Client Azure OpenAI initialisé")
            except Exception as e:
                logger.error(f"Erreur initialisation Azure: {e}")
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
            logger.error("Client Azure non initialisé")
            return {"row": -1, "col": -1, "raw_response": "", "error": "Client Azure non initialisé"}
            
        actual_model = model_name.replace("azure:", "") if model_name and model_name.startswith("azure:") else self.model
        
        prompt = self._build_prompt(grid, player)
        logger.debug(f"[DEBUG Azure] Modèle utilisé: {actual_model}")
        logger.debug(f"[DEBUG Azure] Prompt envoyé: {prompt}")
        
        try:
            response = self.client.chat.completions.create(
                model=actual_model,
                messages=[
                    {"role": "system", "content": (
                        "You are playing Tic-Tac-Toe on a 10x10 grid. "
                        "The victory condition is to line up 5 identical elements horizontally, vertically or diagonally. "
                        "If your opponent is about to win, you should block these potentially winning moves. "
                        "CRITICAL: Your response must be ONLY two numbers separated by a comma (row,column). "
                        "No explanations, no sentences, just the coordinates like '3,7'."
                    )},
                    {"role": "user", "content": prompt}
                ],
                max_completion_tokens=500,
            )
            
            logger.debug(f"[DEBUG Azure] Réponse complète reçue: {response}")
            
            # Vérification détaillée de la réponse
            if not response.choices:
                logger.error("[DEBUG Azure] Erreur : L'API a renvoyé une réponse sans 'choices'.")
                return {"row": -1, "col": -1, "raw_response": "", "error": "Réponse sans choices de l'API Azure"}
                
            if not response.choices[0]:
                logger.error("[DEBUG Azure] Erreur : Le premier choix dans 'choices' est vide.")
                return {"row": -1, "col": -1, "raw_response": "", "error": "Premier choix vide de l'API Azure"}
                
            if not response.choices[0].message:
                logger.error("[DEBUG Azure] Erreur : Le 'message' dans le premier choix est vide.")
                return {"row": -1, "col": -1, "raw_response": "", "error": "Message vide de l'API Azure"}
                
            if response.choices[0].message.content is None:
                logger.error("[DEBUG Azure] Erreur : Le 'content' dans le message est None.")
                return {"row": -1, "col": -1, "raw_response": "", "error": "Content None de l'API Azure"}
                    
            move = response.choices[0].message.content.strip()
            
            if not move:
                logger.error("[DEBUG Azure] Erreur : L'API a renvoyé un contenu vide après nettoyage.")
                return {"row": -1, "col": -1, "raw_response": "", "error": "Réponse vide de l'API Azure"}

            logger.debug(f"[DEBUG Azure] Réponse brute: '{move}'")

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
                    logger.debug(f"[DEBUG Azure] Pattern '{pattern}' match: ({row}, {col})")
                    return {"row": row, "col": col, "raw_response": move}
            
            logger.error(f"[DEBUG Azure] Format de réponse Azure invalide: '{move}'")
            return {"row": -1, "col": -1, "raw_response": move, "error": f"Format invalide: '{move}'"}
                
        except Exception as e:
            logger.error(f"[DEBUG Azure] Exception lors de l'appel API: {e}")
            import traceback
            logger.error(traceback.print_exc())
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
            f"Player '{player}' is playing a Tic-Tac-Toe game. "
            "The goal is to line up 5 identical symbols. "
            "If the opponent is about to win, block them immediately. "
            "IMPORTANT: Respond with ONLY the coordinates in format 'row,column' (e.g. '3,7'). "
            "Do not add any explanation or text. Just the coordinates."
        )
        return prompt