from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import time
from datetime import datetime
from typing import Dict, Any

from game_engine import GameEngine
from llm_client import LLMClient
from azure_client import AzureClient
from game_logger import GameLogger

app = FastAPI(title="Tic-Tac-Toe LLM")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

game_engine = GameEngine()
llm_client = LLMClient()
azure_client = AzureClient()
game_logger = GameLogger()

active_games: Dict[str, Dict[str, Any]] = {}
class MoveRequest(BaseModel):
    game_id: str
    model_name: str
    grid: list
    current_player: str

@app.get("/")
async def root():
    return {"message": "Tic-Tac-Toe LLM", "status": "running"}

@app.get("/api/models")
async def get_models():
    all_models = llm_client.get_available_models()
    return {"models": all_models}

@app.post("/api/game/start")
async def start_game():
    game_state = game_engine.create_new_game()

    active_games[game_state['game_id']] = {
        "start_time": time.time(),
        "model_x": None,
        "model_o": None,
        "moves": []
    }

    return {
        "grid": game_state["grid"],
        "current_player": game_state["current_player"],
        "game_id": game_state["game_id"],
        "winner": game_state["winner"],
        "move_count": game_state["move_count"]
    }

@app.post("/api/game/move")
async def make_move(request: MoveRequest):
    if game_engine.check_winner(request.grid, "X") or game_engine.check_winner(request.grid, "O"):
        return {"grid": request.grid, "winner": request.current_player, "current_player": request.current_player, "move": {}}
    
    move_result = llm_client.ask_move(request.grid, request.current_player, request.model_name)
    
    if not move_result.get("valid", False):
        raise HTTPException(status_code=400, detail="Coup invalide")
    
    new_grid = game_engine.make_move(request.grid, move_result['row'], move_result['col'], request.current_player)
    winner = request.current_player if game_engine.check_winner(new_grid, request.current_player) else None

    # Mettre à jour les infos de jeu pour les logs
    if request.game_id in active_games:
        # Enregistrer le modèle utilisé pour ce joueur
        if request.current_player == "X":
            active_games[request.game_id]["model_x"] = request.model_name
        else:
            active_games[request.game_id]["model_o"] = request.model_name
        
        active_games[request.game_id]["moves"].append({
            "player": request.current_player,
            "row": move_result['row'],
            "col": move_result['col'],
            "model": request.model_name
        })
    
    game_over = winner is not None or game_engine.is_grid_full(new_grid)

    if game_over and request.game_id in active_games:
        game_data = {
            "game_id": request.game_id,
            "winner": winner,
            "start_time": active_games[request.game_id]['start_time'],
            "end_time": time.time(),
            "duration_seconds": time.time() - active_games[request.game_id]['start_time'],
            "model_x": active_games[request.game_id]['model_x'],
            "model_o": active_games[request.game_id]['model_o'],
            "move_count": len(active_games[request.game_id]['moves']),
            "final_grid": new_grid
        }

        # Journaliser la partie
        game_logger.log_game(game_data)

        # Supprimer le jeu des jeux actifs
        del active_games[request.game_id]
    
    return {
        "grid": new_grid,
        "winner": winner,
        "current_player": "O" if request.current_player == "X" else "X",
        "move": {"row": move_result['row'], "col": move_result['col'], "player": request.current_player}
    }