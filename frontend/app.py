from nicegui import ui
import random
import requests
from typing import List, Tuple

ROWS, COLS = 10, 10

# état global
global current_player, grid
grid = [["" for _ in range(COLS)] for _ in range(ROWS)]
scores = {"X": 0, "O": 0}
current_player = "X"  # X commence
log_lines: List[str] = []

# widgets des cellules — initialisées plus bas (une seule fois)
cells: List[List] = [[None for _ in range(COLS)] for _ in range(ROWS)]
cells_initialized = False

# URL de l'API (ton binôme)
API_URL = "http://127.0.0.1:8000/api/game/move"  # url api 

# ---------------- utilitaires ----------------
def append_log(text: str):
    log_lines.append(text)
    # on garde les 200 dernières lignes
    if len(log_lines) > 200:
        del log_lines[0: len(log_lines) - 200]
    # mettre à jour l'affichage (si le widget existe)
    try:
        logs_text.set_text("\n".join(log_lines[::-1]))  # newest first
    except NameError:
        pass

def check_five_in_a_row(g: List[List[str]], player: str) -> bool:
    """Retourne True si 'player' a 5 alignés (horiz, vert, diag)."""
    N, M = ROWS, COLS
    target = player

    # directions (dr, dc)
    dirs = [(0,1), (1,0), (1,1), (1,-1)]

    for r in range(N):
        for c in range(M):
            if g[r][c] != target:
                continue
            for dr, dc in dirs:
                count = 0
                rr, cc = r, c
                while 0 <= rr < N and 0 <= cc < M and g[rr][cc] == target:
                    count += 1
                    if count >= 5:
                        return True
                    rr += dr
                    cc += dc
    return False

# def parse_api_move(resp_json) -> Tuple[int,int] | None:
#     """Accepte [x,y] ou {"x":x,"y":y} ou {"col":x,"row":y}"""
#     if isinstance(resp_json, list) and len(resp_json) >= 2:
#         return int(resp_json[0]), int(resp_json[1])
#     if isinstance(resp_json, dict):
#         for a,b in (("x","y"), ("col","row"), ("c","r")):
#             if a in resp_json and b in resp_json:
#                 return int(resp_json[a]), int(resp_json[b])
#     return None
def parse_api_move(resp_json):
    m = resp_json.get("move")
    if not m:
        return None
    return m["col"], m["row"]

# ---------------- UI ----------------
with ui.column().style("""
    justify-content: center; 
    align-items: center; 
    width: 90%; 
    max-width: 800px; 
    margin: auto;
"""):

    # titre
    ui.label("Tic Tac Toe").style(
        "font-size: 28px; font-weight: bold; text-align:center; margin-bottom:20px; color:#4A5759;"
    )

    # zone de configuration (ou cacher si pas voulu) : model names + endpoint
    with ui.row().style("width:100%; justify-content:center; gap:8px; margin-bottom:10px;"):
        model_x_input = ui.input("model_x", value="model_x_name").props("placeholder='model_x'").style("width:40%")
        model_o_input = ui.input("model_o", value="model_o_name").props("placeholder='model_o'").style("width:40")
        api_input = ui.input("api_url", value=API_URL).props("placeholder='http://127.0.0.1:8000/play'").style("width:100%")

    # Conteneur principal scores + grille + scores
    with ui.row().style("""
        justify-content: space-between; 
        align-items: flex-start; 
        width: 100%;
        overflow-x: auto;
    """):

        # Score X (gauche)
        with ui.column().style("align-items: center;"):
            ui.label("X").style("color:red; font-weight:bold; font-size:22px;")
            x_score_label = ui.label(str(scores["X"])).style("font-size:22px; font-weight:bold; color:red;")

        # Grille et score (centre)
        with ui.column().style("align-items: center; flex-shrink:0;"):
            ui.label("Scores").style("font-size:20px; font-weight:bold; margin-bottom:5px; color:#4A5759;")
            score_label = ui.label(f"Score X: {scores['X']} | O: {scores['O']}").style(
                "font-size: 20px; font-weight: bold; margin-bottom:15px; text-align:center;"
            )

            # conteneur de la grille
            grid_container = ui.column().style("""
                align-items:center; 
                background-color:#F7E1D7; 
                padding:15px; 
                border-radius:10px; 
                box-shadow: 2px 2px 10px rgba(0,0,0,0.2);
                overflow-x:auto;
            """)
                # Score O (droite)
        with ui.column().style("align-items: center;"):
            ui.label("O").style("color:blue; font-weight:bold; font-size:22px;")
            o_score_label = ui.label(str(scores["O"])).style("font-size:22px; font-weight:bold; color:blue;")

    # zone des logs (affiche les échanges JSON)
    with ui.row().style("width:100%; justify-content:center; margin-top:12px;"):
        with ui.column().style("width:100%; max-width:800px;"):
            ui.label("Logs (dernier en haut)").style("font-size:13px; color:#666; margin-bottom:5px;")
            logs_text = ui.label("").style("white-space:pre-wrap; max-height:200px; overflow:auto; background:#fafafa; padding:8px; border-radius:6px; border:1px solid #eee;")

# Fonction d'affichage de la grille (10x10)
def display_grid():
    global cells_initialized

    CELL = 35

    if not cells_initialized:
        grid_container.clear()  # on vide juste au premier rendu
        for r in range(ROWS):
            with ui.row().style("""
    justify-content: center;  /* centre horizontalement */
    align-items: center;      /* centre verticalement */
    width: 100%;
"""):
                for c in range(COLS):
                    cell_value = grid[r][c] or ""
                    lbl = ui.label(cell_value or "-").style(
                        f"width:{CELL}px; height:{CELL}px; line-height:{CELL}px;"
                        f"text-align:center; border-radius:5px; border:1px solid #4A5759;"
                        f"font-weight:bold; margin:2px;"
                    )
                    cells[r][c] = lbl
        cells_initialized = True

    # mise à jour du texte & style
    for r in range(ROWS):
        for c in range(COLS):
            lbl = cells[r][c]
            cell = grid[r][c] or ""
            if cell == "X":
                color = "white"; bg = "red"; text = "X"
            elif cell == "O":
                color = "white"; bg = "blue"; text = "O"
            else:
                color = "black"; bg = "#DEDBD2"; text = "-"
            try:
                lbl.set_text(text)
                lbl.style(f"background-color:{bg}; color:{color};")
            except Exception:
                pass
def reset_grid():
    global current_player, API_URL, grid
    API_URL = api_input.value.strip() or API_URL
    model_name = model_x_input.value.strip() if current_player == "X" else model_o_input.value.strip()

    payload = {
        "grid": grid,
        "current_player": current_player,
        "model_name": model_name
    }

    append_log(f"REQUEST ({current_player}) -> {API_URL} payload keys: grid[{len(grid)}x{len(grid[0])}], model={model_name}")

    # essayer l'API
    try:
        resp = requests.post(API_URL, json=payload, timeout=8.0)
        resp.raise_for_status()
        resp_json = resp.json()
        append_log(f"RESPONSE raw: {resp_json}")

        # si l'API renvoie une grille complète, on la prend comme source de vérité
        if isinstance(resp_json, dict) and "grid" in resp_json:
            api_grid = resp_json.get("grid")
            # normaliser les espaces potentiels (" " vs "" ) -> on remet "" pour frontend
            for r in range(ROWS):
                for c in range(COLS):
                    val = api_grid[r][c]
                    # convertir " " (backend) en "" (frontend)
                    grid[r][c] = "" if val in (None, " ", ".") else val

        # récupérer le move (col,row)
        move = parse_api_move(resp_json)
        if move is None:
            append_log("RESPONSE non standard, fallback aléatoire.")
            raise ValueError("move parse failed")
        x_col, y_row = move

    except Exception as e:
        append_log(f"API error: {e} → fallback aléatoire")
        # fallback : choix aléatoire dans la grille existante
        empty_cells = [(r, c) for r in range(ROWS) for c in range(COLS) if grid[r][c] == ""]
        if not empty_cells:
            append_log("Aucune cellule vide — match nul / grille pleine.")
            # si grille pleine -> on la vide et on recommence sur la même grille
            for r in range(ROWS):
                for c in range(COLS):
                    grid[r][c] = ""
            current_player = "X"
            display_grid()
            return
        y_row, x_col = random.choice(empty_cells)

    # protéger indices et appliquer coup sur la grille EXISTANTE
    if 0 <= y_row < ROWS and 0 <= x_col < COLS and grid[y_row][x_col] == "":
        grid[y_row][x_col] = current_player
        append_log(f"Applied move: player={current_player} at (col={x_col}, row={y_row})")
        # vérifier victoire
        if check_five_in_a_row(grid, current_player):
            ui.notify(f"Le joueur {current_player} a gagné !", color="green")
            append_log(f"WIN detected for {current_player}")
            scores[current_player] += 1
        # switch player
        current_player = "O" if current_player == "X" else "X"
    else:
        append_log(f"Move invalide ou cellule occupée: ({x_col},{y_row}).")

    # update affichage et scores
    score_label.set_text(f"Score X: {scores['X']} | O: {scores['O']}")
    x_score_label.set_text(str(scores["X"]))
    o_score_label.set_text(str(scores["O"]))
    display_grid()

    
# Mettre le footer dans une colonne séparée en bas
with ui.column().style(
    "align-items:center; position: fixed; bottom: 0; width: 100%; padding: 10px 0; background-color:#fff;"
):

    ui.button("Jouer", on_click=reset_grid).style(
        "font-size:18px; padding:10px 25px; background-color:#B0C4B1; color:white; border-radius:5px;"
    )
    ui.label("© 2025 All rights reserved").style("text-align:center; margin-top:10px; color:gray;")


# ---------------- lancement ----------------

display_grid()  # affichage initial de la grille
# run
if __name__ in {"__main__", "__mp_main__"}:
    ui.run()