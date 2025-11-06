from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

from game_engine import GameEngine
from llm_client import LLMClient


# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Tic-Tac-Toe LLM")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialisation
game_engine = GameEngine()
llm_client = LLMClient()

@app.get("/")
async def root():
    return JSONResponse(content={"message": "Tic-Tac-Toe LLM", "status": "running"})

@app.get("/api/models")
async def get_models():
    """Récupérer les modèles disponibles"""
    models = llm_client.get_available_models()
    return JSONResponse(content={"models": models})

@app.post("/api/game/start")
async def start_game():
    """Démarrer une nouvelle partie"""
    try:
        game_state = game_engine.create_new_game()
        
        # Journalisation de l'état initial du jeu
        logger.info(f"Nouvelle partie créée - ID: {game_state['game_id']}, Joueur: {game_state['current_player']}")
        
        # Retour (JSON)
        response_data = {
            "grid": game_state["grid"],
            "current_player": game_state["current_player"],
            "game_id": game_state["game_id"],
            "winner": game_state["winner"],
            "move_count": game_state["move_count"]
        }
        logger.info(f"Réponse envoyée: {response_data}")
        return JSONResponse(content=response_data)
        
    except Exception as e:
        logger.error(f"Erreur start_game: {e}")
        return JSONResponse(
            content={"error": str(e)}, 
            status_code=500
        )

@app.post("/api/game/move")
async def make_move(request: dict):
    """Demander un coup au LLM"""
    try:
        # Journaliser la requête entrante
        logger.info(f"Requête reçue: {request}")
        
        required_fields = ["game_id", "model_name", "grid", "current_player"]
        for field in required_fields:
            if field not in request:
                logger.error(f"Champ manquant: {field}")
                return JSONResponse(
                    content={"error": f"Champ manquant: {field}"},
                    status_code=400
                )
        game_id = request["game_id"]
        model_name = request["model_name"]
        grid = request["grid"]
        current_player = request["current_player"]

        logger.info(f"Demande de coup - Partie: {game_id}, Joueur: {current_player}, Modèle: {model_name}")

        # Vérifier s'il y a un gagnant
        if game_engine.check_winner(grid, "X"):
            logger.info(f"Le joueur X a déjà gagné dans la partie {game_id}")
            return JSONResponse(content={
                "grid": grid,
                "winner": "X",
                "current_player": current_player,
                "move": {}
            })
        
        if game_engine.check_winner(grid, "O"):
            logger.info(f"Le joueur O a déjà gagné dans la partie {game_id}")
            return JSONResponse(content={
                "grid": grid,
                "winner": "O",
                "current_player": current_player,
                "move": {}
            })
        
        # Demander au LLM de jouer un coup
        logger.info(f"Envoi de la requête au LLM {model_name}")
        move_result = llm_client.ask_move(grid, current_player, model_name)
        logger.info(f"Réponse du LLM: {move_result}")

        # Vérifier si le coup est valide
        if not move_result.get("valid", False):
            logger.warning(f"Coup invalide - Partie: {game_id}, Coup: {move_result}")
            return JSONResponse(
                content={"error": f"Coup invalide - Partie: {game_id}, Coup: {move_result}"},
                status_code=400
            )
        
        # Appliquer le coup joué par LLM
        new_grid = game_engine.make_move(grid, move_result['row'], move_result['col'], current_player)

        # Vérifier si gagnant
        winner = None
        if game_engine.check_winner(new_grid, current_player):
            winner = current_player
            logger.info(f"Le joueur {current_player} a gagné dans la partie {game_id}")

        # Réponse (JSON)
        response_data = {
            "grid": new_grid,
            "winner": winner,
            "current_player": "O" if current_player == "X" else "X",
            "move": {
                "row": move_result['row'],
                "col": move_result['col'],
                "player": current_player
            }
        }
        
        logger.info(f"Réponse envoyée: {response_data}")
        return JSONResponse(content=response_data)
        
    except Exception as e:
        logger.error(f"Erreur make_move: {e}")
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )