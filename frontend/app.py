# frontend/app.py
from nicegui import ui
import random

ROWS = 10
COLS = 10

# grille initiale
grid = [["" for _ in range(COLS)] for _ in range(ROWS)]

# scores
scores = {"X": 0, "O": 0}

# label pour les scores
score_label = ui.label(f"Score X: {scores['X']}  |  O: {scores['O']}").style(
    "font-size: 18px; font-weight: bold; margin-bottom:10px;"
)

# conteneur pour la grille
grid_container = ui.column()

# fonction pour afficher la grille
def display_grid():
    grid_container.clear()  # vide la grille précédente
    for r in range(ROWS):
        with ui.row():
            for c in range(COLS):
                cell = grid[r][c] or "-"
                ui.label(cell).style("width:30px; text-align:center; border:1px solid black; padding:5px;")

# fonction pour simuler un coup (à remplacer par le LLM plus tard)
def play_turn():
    empty_cells = [(r, c) for r in range(ROWS) for c in range(COLS) if grid[r][c] == ""]
    if empty_cells:
        r, c = random.choice(empty_cells)
        player = random.choice(["X", "O"])
        grid[r][c] = player
        scores[player] += 1  # incrémente score pour test
    score_label.set_text(f"Score X: {scores['X']}  |  O: {scores['O']}")
    display_grid()

# interface
ui.label("LLM Tic Tac Toe Arena").style("font-size: 24px; font-weight: bold; margin-bottom:10px;")
display_grid()
ui.button("Jouer", on_click=play_turn)

ui.run()
