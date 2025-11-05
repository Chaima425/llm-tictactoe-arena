from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging

logging.basicConfig(
    level=logging.INFO
)
logger = logging.getLogger(__name__)


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

game_engine = GameEngine()

llm_client = LLMClient()

@app.get("/")
async def root():
    return {"message": "Tic-Tac-Toe LLM", "status": "running"}

@app.get("/api/models/")
async def get_models():
    models = llm_client.get_available_models()
    return {"models": models}

@app.post("/api/game/start", response_model=GameState):
async def start_game():
    game_state = game_engine.create_new_game()
    log_game_start(game_state)
    return game_state

@app.post("/api/game/move", response_model=MoveResponse):
async def make_move():
    logger.info(f"Demande de coup - Joueur: {request.current_player}, Modèle: {request.model_name}")

    if game_engine.check_winner(request.grid, "X"):
        return MoveResponse(grid=request.grid, winner="X", current_player=request.current_player, move={})
    if game_engine.check_winner(request.grid, "O"):
        return MoveResponse(grid=request.grid, winner="O", current_player=request.current_player, move={})
    
    move_result = llm_client.ask_move(request.grid, request.current_player, request.model_name)

    if game_engine.is_valid_move(request.grid,move_result["row"], move_result["col"]):
        new_grid = game_engine.make_move(request.grid, move_result["row"], move_result["col"], request.current_player)

        wiiner = None
        if game_engine.check_winner(new_grid, request.current_player):
            winner = request.current_player
            log_game_end(request.game_id, winner)

        log_move(request.game_id, request.current_player, move_result, request.model_name)

        return MoveResponse(
            grid=new_grid,
            winner=winner,
            current_player="O" if request.current_player == "X" else "X",
            move=move_result
        )
    
    else:
        logger.warning(f"Coup invalide: {move_result}")
        raise HTTPException(status_code=400, detail=f"Coup invalide: {move_result}")