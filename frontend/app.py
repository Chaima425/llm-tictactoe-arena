from nicegui import ui
import random

ROWS, COLS = 10, 10

# grille initiale
grid = [["" for _ in range(COLS)] for _ in range(ROWS)]

# scores
scores = {"X": 0, "O": 0}

# Titre
ui.label("LLM Tic Tac Toe Arena").style(
    "font-size: 28px; font-weight: bold; text-align:center; margin-bottom:20px; color:#4A5759;"
)

# Conteneur principal pour la grille et scores
with ui.row().style("justify-content: space-between; align-items: flex-start; width: 80%; margin:auto;"):

    # Score X à gauche
    with ui.column().style("align-items: center;"):
        ui.label("X").style("color:red; font-weight:bold; font-size:22px;")
        x_score_label = ui.label(str(scores["X"])).style("font-size:22px; font-weight:bold; color:red;")

    # Grille au centre
    with ui.column().style("align-items: center;"):
        score_label = ui.label(f"Score X: {scores['X']} | O: {scores['O']}").style(
            "font-size: 20px; font-weight: bold; margin-bottom:15px; text-align:center;"
        )
        grid_container = ui.column().style(
            "align-items:center; background-color:#F7E1D7; padding:15px; border-radius:10px; box-shadow: 2px 2px 10px rgba(0,0,0,0.2);"
        )

    # Score O à droite
    with ui.column().style("align-items: center;"):
        ui.label("O").style("color:blue; font-weight:bold; font-size:22px;")
        o_score_label = ui.label(str(scores["O"])).style("font-size:22px; font-weight:bold; color:blue;")

# fonction pour afficher la grille
def display_grid():
    grid_container.clear()
    for r in range(ROWS):
        with ui.row().style("justify-content:center;"):
            for c in range(COLS):
                cell = grid[r][c] or ""
                if cell == "X":
                    color = "white"
                    bg = "red"
                elif cell == "O":
                    color = "white"
                    bg = "blue"
                else:
                    color = "black"
                    bg = "#DEDBD2"
                ui.label(cell or "-").style(
                    f"width:35px; height:35px; text-align:center; border-radius:5px; border:1px solid #4A5759; color:{color}; background-color:{bg}; font-weight:bold; margin:2px;"
                )

# fonction pour jouer un tour aléatoire
def play_turn():
    empty_cells = [(r, c) for r in range(ROWS) for c in range(COLS) if grid[r][c] == ""]
    if empty_cells:
        r, c = random.choice(empty_cells)
        player = random.choice(["X", "O"])
        grid[r][c] = player
        scores[player] += 1
    score_label.set_text(f"Score X: {scores['X']} | O: {scores['O']}")
    x_score_label.set_text(str(scores["X"]))
    o_score_label.set_text(str(scores["O"]))
    display_grid()

# affichage initial
display_grid()

# Bouton Jouer centré sous la grille
with ui.row().style("justify-content:center; margin-top:20px;"):
    ui.button("Jouer", on_click=play_turn).style(
        "font-size:18px; padding:10px 25px; background-color:#B0C4B1; color:white; border-radius:5px;"
    )

# Footer centré
ui.label("© 2025 All rights reserved").style("text-align:center; margin-top:30px; color:gray;")

# Lancer le serveur (compatible Python 3.12)
if __name__ in {"__main__", "__mp_main__"}:
    ui.run()







# from nicegui import ui
# import random

# ROWS, COLS = 10, 10

# # grille initiale
# grid = [["" for _ in range(COLS)] for _ in range(ROWS)]

# # scores
# scores = {"X": 0, "O": 0}

# # Titre
# ui.label("LLM Tic Tac Toe Arena").style(
#     "font-size: 28px; font-weight: bold; text-align:center; margin-bottom:20px; color:#4A5759;"
# )

# # Conteneur principal pour la grille et scores
# with ui.row().style("justify-content: space-between; align-items: flex-start; width: 80%; margin:auto;"):

#     # Score X à gauche
#     with ui.column().style("align-items: center;"):
#         ui.label("X").style("color:red; font-weight:bold; font-size:22px;")
#         x_score_label = ui.label(str(scores["X"])).style("font-size:22px; font-weight:bold; color:red;")

#     # Grille au centre
#     with ui.column().style("align-items: center;"):
#         score_label = ui.label(f"Score X: {scores['X']} | O: {scores['O']}").style(
#             "font-size: 20px; font-weight: bold; margin-bottom:15px; text-align:center;"
#         )
#         grid_container = ui.column().style("align-items:center; background-color:#F7E1D7; padding:15px; border-radius:10px; box-shadow: 2px 2px 10px rgba(0,0,0,0.2);")

#     # Score O à droite
#     with ui.column().style("align-items: center;"):
#         ui.label("O").style("color:blue; font-weight:bold; font-size:22px;")
#         o_score_label = ui.label(str(scores["O"])).style("font-size:22px; font-weight:bold; color:blue;")

# # fonction pour afficher la grille
# def display_grid():
#     grid_container.clear()
#     for r in range(ROWS):
#         with ui.row().style("justify-content:center;"):
#             for c in range(COLS):
#                 cell = grid[r][c] or ""
#                 if cell == "X":
#                     color = "white"
#                     bg = "red"
#                 elif cell == "O":
#                     color = "white"
#                     bg = "blue"
#                 else:
#                     color = "black"
#                     bg = "#DEDBD2"
#                 ui.label(cell or "-").style(
#                     f"width:35px; height:35px; text-align:center; border-radius:5px; border:1px solid #4A5759; color:{color}; background-color:{bg}; font-weight:bold; margin:2px;"
#                 )

# # fonction pour jouer un tour aléatoire
# def play_turn():
#     empty_cells = [(r, c) for r in range(ROWS) for c in range(COLS) if grid[r][c] == ""]
#     if empty_cells:
#         r, c = random.choice(empty_cells)
#         player = random.choice(["X", "O"])
#         grid[r][c] = player
#         scores[player] += 1
#     score_label.set_text(f"Score X: {scores['X']} | O: {scores['O']}")
#     x_score_label.set_text(str(scores["X"]))
#     o_score_label.set_text(str(scores["O"]))
#     display_grid()

# # affichage initial
# display_grid()

# # Bouton Jouer centré sous la grille
# with ui.row().style("justify-content:center; margin-top:20px;"):
#     ui.button("Jouer", on_click=play_turn).style(
#         "font-size:18px; padding:10px 25px; background-color:#B0C4B1; color:white; border-radius:5px;"
#     )

# # Footer centré
# ui.label("© 2025 All rights reserved").style("text-align:center; margin-top:30px; color:gray;")

# ui.run()
