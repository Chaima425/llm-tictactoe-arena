from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List
import random

ROWS, COLS = 10, 10
WIN_LENGTH = 5

app = FastAPI()

# CORS pour permettre les requêtes depuis NiceGUI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

def check_five_in_a_row(grid: List[List[str]], player: str) -> bool:
    dirs = [(0,1),(1,0),(1,1),(1,-1)]
    for r in range(ROWS):
        for c in range(COLS):
            if grid[r][c] != player:
                continue
            for dr, dc in dirs:
                count = 0
                rr, cc = r, c
                while 0 <= rr < ROWS and 0 <= cc < COLS and grid[rr][cc] == player:
                    count += 1
                    if count >= WIN_LENGTH:
                        return True
                    rr += dr
                    cc += dc
    return False

@app.post("/play")
def play(payload: dict):
    grid = payload.get("grid", [["" for _ in range(COLS)] for _ in range(ROWS)])
    player = payload.get("player", "X")

    # Choisir un coup aléatoire parmi les cellules vides
    empty_cells = [(r, c) for r in range(ROWS) for c in range(COLS) if grid[r][c] == ""]
    if not empty_cells:
        return JSONResponse(content={"grid": grid, "winner": None, "move": {}, "current_player": player})

    row, col = random.choice(empty_cells)
    grid[row][col] = player

    winner = player if check_five_in_a_row(grid, player) else None

    return JSONResponse(content={
        "grid": grid,
        "winner": winner,
        "current_player": "O" if player == "X" else "X",
        "move": {"row": row, "col": col, "player": player}
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
