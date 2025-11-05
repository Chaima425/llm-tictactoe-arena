from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import json

# from shared.models import GameState, MoveRequest, MoveResponse
from backend.game_engine import GameEngine
from backend.llm_client import LLMClient


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
    """Récupérer les modèles disponibles - RETOUR JSON"""
    models = llm_client.get_available_models()
    return JSONResponse(content={"models": models})

@app.post("/api/game/start")
async def start_game():
    """Démarrer une nouvelle partie"""
    try:
        game_state = game_engine.create_new_game()
        
        # Retour (JSON)
        response_data = {
            "grid": game_state["grid"],
            "current_player": game_state["current_player"],
            "game_id": game_state["game_id"],
            "winner": game_state["winner"],
            "move_count": game_state["move_count"]
        }
        return JSONResponse(content=response_data)
        
    except Exception as e:
        logger.error(f"Erreur start_game: {e}")
        return JSONResponse(
            content={"error": str(e)}, 
            status_code=500
        )

@app.post("/api/game/move")
async def make_move(request: MoveRequest):
    """Demander un coup au LLM"""
    logger.info(f"Demande de coup - Joueur: {request.current_player}, Modèle: {request.model_name}")
    
    try:
        # Vérifier gagnant existant
        if game_engine.check_winner(request.grid, "X"):
            return JSONResponse(content={
                "grid": request.grid,
                "winner": "X", 
                "current_player": request.current_player,
                "move": {}
            })
            
        if game_engine.check_winner(request.grid, "O"):
            return JSONResponse(content={
                "grid": request.grid,
                "winner": "O", 
                "current_player": request.current_player,
                "move": {}
            })
        
        # Demander coup au LLM avec la grille JSON
        move_result = llm_client.ask_move(request.grid, request.current_player, request.model_name)
        
        # Valider et appliquer le coup
        if game_engine.is_valid_move(request.grid, move_result["row"], move_result["col"]):
            new_grid = game_engine.make_move(request.grid, move_result["row"], move_result["col"], request.current_player)
            
            # Vérifier le gagnant
            winner = None
            if game_engine.check_winner(new_grid, request.current_player):
                winner = request.current_player
            
            # Réponse (JSON)
            response_data = {
                "grid": new_grid,
                "winner": winner,
                "current_player": "O" if request.current_player == "X" else "X",
                "move": {
                    "row": move_result["row"],
                    "col": move_result["col"],
                    "player": request.current_player
                }
            }
            
            return JSONResponse(content=response_data)
            
        else:
            logger.warning(f"Coup invalide: {move_result}")
            return JSONResponse(
                content={"error": f"Coup invalide: {move_result}"},
                status_code=400
            )
            
    except Exception as e:
        logger.error(f"Erreur make_move: {e}")
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )