# frontend/config.py: sert à gérer la configuration de l'application frontend.
import os
from dotenv import load_dotenv

load_dotenv()  # Charge le fichier .env

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
