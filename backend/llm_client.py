import requests
import json
import logging

logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self, ollama_url: str):
        self.ollama_url = ollama_url

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