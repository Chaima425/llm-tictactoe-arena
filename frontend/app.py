from nicegui import ui
import random
import requests
import uuid
import sys
import os
from typing import List, Tuple

# Ajouter le répertoire parent au path pour importer le backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.game_engine import GameEngine

ROWS, COLS = 10, 10

# état global
global current_player, grid, scores, current_game_id
grid = [["" for _ in range(COLS)] for _ in range(ROWS)]
scores = {"X": 0, "O": 0}
current_player = "X"
current_game_id = None
log_lines: List[str] = []

# Variables globales pour le mode auto
auto_mode = False
auto_timer = None

# Variables globales pour suivre les statistiques
model_stats = {}

# Instance de GameEngine pour réutiliser la logique métier
game_engine = GameEngine()

# widgets des cellules – initialisées plus bas (une seule fois)
cells: List[List] = [[None for _ in range(COLS)] for _ in range(ROWS)]
cells_initialized = False

# URL de l'API
API_URL = "http://127.0.0.1:8000"

# ---------------- utilitaires ----------------
def append_log(text: str):
    log_lines.append(text)
    if len(log_lines) > 200:
        del log_lines[0: len(log_lines) - 200]
    try:
        logs_text.set_text("\n".join(log_lines[::-1]))
    except NameError:
        pass

def check_winner(player):
    """Utilise la logique métier de game_engine pour vérifier si un joueur a gagné"""
    backend_grid = []
    for r in range(ROWS):
        row = []
        for c in range(COLS):
            cell = grid[r][c]
            row.append(" " if cell == "" else cell)
        backend_grid.append(row)
    
    return game_engine.check_winner(backend_grid, player)

def update_model_stats(model_name, result):
    """Met à jour les statistiques d'un modèle"""
    if model_name not in model_stats:
        model_stats[model_name] = {"wins": 0, "losses": 0, "draws": 0, "total": 0}
    
    model_stats[model_name]["total"] += 1
    
    if result == "win":
        model_stats[model_name]["wins"] += 1
    elif result == "loss":
        model_stats[model_name]["losses"] += 1
    else:
        model_stats[model_name]["draws"] += 1
    
    display_model_stats()

def display_model_stats():
    """Affiche les statistiques des modèles"""
    stats_text = "Statistiques des modèles:\n"
    for model, stats in model_stats.items():
        total = stats["total"]
        win_rate = stats["wins"] / total * 100 if total > 0 else 0
        stats_text += f"{model}: {stats['wins']}V/{stats['losses']}D/{stats['draws']}N ({win_rate:.1f}%)\n"
    
    stats_label.set_text(stats_text)

def init_game():
    """Initialiser une nouvelle partie via l'API"""
    global grid, current_player, current_game_id
    
    # Si le mode auto est actif, on l'arrête pour commencer une nouvelle partie
    if auto_mode:
        toggle_auto_mode()
    
    try:
        api_url = api_input.value.strip() or API_URL
        start_url = f"{api_url}/api/game/start"
        
        append_log(f"Demande nouvelle partie -> {start_url}")
        resp = requests.post(start_url, timeout=10.0)
        resp.raise_for_status()
        game_data = resp.json()
        
        current_game_id = game_data["game_id"]
        backend_grid = game_data["grid"]
        current_player = game_data["current_player"]
        
        # Convertir la grille backend -> frontend
        for r in range(ROWS):
            for c in range(COLS):
                val = backend_grid[r][c]
                grid[r][c] = "" if val == " " else val
        
        # Mettre à jour l'affichage
        score_label.set_text(f"Score X: {scores['X']} | O: {scores['O']}")
        x_score_label.set_text(str(scores["X"]))
        o_score_label.set_text(str(scores["O"]))
        game_id_label.set_text(f"Game ID: {current_game_id}")
        
        # CORRECTION: Forcer le rafraîchissement de la grille
        update_grid_display()
        
        append_log("=== NOUVELLE PARTIE DÉMARRÉE ===")
        append_log(f"Game ID: {current_game_id}")
        append_log(f"Joueur courant: {current_player}")
        
    except Exception as e:
        append_log(f"Erreur initialisation: {e}")
        game_state = game_engine.create_new_game()
        current_game_id = game_state["game_id"]
        current_player = game_state["current_player"]
        
        for r in range(ROWS):
            for c in range(COLS):
                val = game_state["grid"][r][c]
                grid[r][c] = "" if val == " " else val
        
        game_id_label.set_text(f"Game ID: {current_game_id} (fallback)")
        update_grid_display()

def make_move():
    """Demande un coup au LLM pour le joueur actuel"""
    global current_player, grid, current_game_id
    
    # Vérifier si la partie est déjà terminée
    if check_winner("X"):
        append_log("X a déjà gagné ! Arrêt du mode auto.")
        if auto_mode: 
            toggle_auto_mode()
        return
    if check_winner("O"):
        append_log("O a déjà gagné ! Arrêt du mode auto.")
        if auto_mode: 
            toggle_auto_mode()
        return
    
    # Vérifier qu'on a un game_id
    if not current_game_id:
        ui.notify("Veuillez d'abord démarrer une nouvelle partie", color="warning")
        if auto_mode: toggle_auto_mode()
        return

    api_url = api_input.value.strip() or API_URL
    move_url = f"{api_url}/api/game/move"
    model_name = model_x_input.value.strip() if current_player == "X" else model_o_input.value.strip()

    # Convertir la grille frontend -> format backend
    backend_grid = []
    for r in range(ROWS):
        row = []
        for c in range(COLS):
            cell = grid[r][c]
            row.append(" " if cell == "" else cell)
        backend_grid.append(row)

    payload = {
        "game_id": current_game_id,
        "grid": backend_grid,
        "current_player": current_player,
        "model_name": model_name
    }

    append_log(f"REQUEST ({current_player}) -> ModÚle: {model_name}")

    try:
        resp = requests.post(move_url, json=payload, timeout=30.0)
        
        # Vérifier le statut HTTP
        if resp.status_code == 400:
            error_detail = resp.json().get('error', 'Bad Request')
            append_log(f"ERROR 400: {error_detail}")
            ui.notify(f"Erreur 400: {error_detail}", color="negative")
            if auto_mode: toggle_auto_mode()
            return
            
        elif resp.status_code == 500:
            error_detail = "Erreur interne du serveur"
            try:
                error_data = resp.json()
                error_detail = error_data.get('error', error_detail)
            except:
                pass
            append_log(f"ERROR 500: {error_detail}")
            ui.notify("Erreur serveur - Utilisation du fallback", color="warning")
            execute_local_fallback()
            update_display()
            return
            
        resp.raise_for_status()
        resp_json = resp.json()
        
        # Log du coup joué
        move_info = resp_json.get("move", {})
        append_log(f"{current_player} joue: ({move_info.get('row')}, {move_info.get('col')})")

        # Vérifier s'il y a un gagnant
        if resp_json.get("winner"):
            winner = resp_json["winner"]
            ui.notify(f"Le joueur {winner} a gagné !", color="green")
            scores[winner] += 1
            append_log(f"*** VICTOIRE {winner} ***")
            
            if winner == "X":
                update_model_stats(model_x_input.value.strip(), "win")
                update_model_stats(model_o_input.value.strip(), "loss")
            else:
                update_model_stats(model_o_input.value.strip(), "win")
                update_model_stats(model_x_input.value.strip(), "loss")
            
            # Arrêter le mode auto si actif
            if auto_mode:
                toggle_auto_mode()
        
        # Mettre à jour la grille frontend (convertir " " -> "")
        api_grid = resp_json.get("grid", backend_grid)
        for r in range(ROWS):
            for c in range(COLS):
                val = api_grid[r][c]
                grid[r][c] = "" if val == " " else val

        # Mettre à jour le joueur courant
        current_player = resp_json.get("current_player", "O" if current_player == "X" else "X")

        # Vérifier s'il y a match nul
        if game_engine.is_grid_full(backend_grid) and not resp_json.get("winner"):
            ui.notify("Match nul !", color="orange")
            append_log("*** MATCH NUL ***")
            
            update_model_stats(model_x_input.value.strip(), "draw")
            update_model_stats(model_o_input.value.strip(), "draw")
            
            if auto_mode:
                toggle_auto_mode()

    except requests.exceptions.HTTPError as e:
        if hasattr(e, 'response') and e.response.status_code == 500:
            append_log(f"HTTPError 500: {e} → fallback local")
            execute_local_fallback()
        else:
            append_log(f"HTTPError: {e}")
            ui.notify(f"Erreur HTTP", color="negative")
            if auto_mode: toggle_auto_mode()
            return
            
    except Exception as e:
        append_log(f"API error: {e} → fallback local")
        execute_local_fallback()

    # Mettre à jour l'affichage
    update_display()

def execute_local_fallback():
    """Exécuter un fallback local en utilisant la logique métier de game_engine"""
    global current_player, grid
    
    # Convertir la grille frontend vers le format backend
    backend_grid = []
    for r in range(ROWS):
        row = []
        for c in range(COLS):
            cell = grid[r][c]
            row.append(" " if cell == "" else cell)
        backend_grid.append(row)
    
    # Utiliser la logique métier pour trouver un coup stratégique
    empty_cells = [(r, c) for r in range(ROWS) for c in range(COLS) if backend_grid[r][c] == " "]
    if empty_cells:
        # Utiliser la logique de game_engine pour trouver un coup stratégique
        strategic_move = game_engine._select_strategic_move(empty_cells, "local_fallback")
        y_row, x_col = strategic_move["row"], strategic_move["col"]
        
        # Appliquer le coup en utilisant la logique métier
        backend_grid = game_engine.make_move(backend_grid, y_row, x_col, current_player)
        
        # Convertir la grille backend -> frontend
        for r in range(ROWS):
            for c in range(COLS):
                val = backend_grid[r][c]
                grid[r][c] = "" if val == " " else val
        
        append_log(f"Local fallback: {current_player} at ({y_row},{x_col})")
        
        # Vérifier victoire en utilisant la logique métier
        if game_engine.check_winner(backend_grid, current_player):
            ui.notify(f"Le joueur {current_player} a gagné !", color="green")
            scores[current_player] += 1
            append_log(f"WIN detected for {current_player}")
            
            if current_player == "X":
                update_model_stats(model_x_input.value.strip(), "win")
                update_model_stats(model_o_input.value.strip(), "loss")
            else:
                update_model_stats(model_o_input.value.strip(), "win")
                update_model_stats(model_x_input.value.strip(), "loss")
            
            if auto_mode:
                toggle_auto_mode()
        
        # Passer au joueur suivant
        current_player = "O" if current_player == "X" else "X"
    else:
        ui.notify("Match nul ! Grille pleine.", color="orange")
        append_log("MATCH NUL - Grille pleine")
        
        update_model_stats(model_x_input.value.strip(), "draw")
        update_model_stats(model_o_input.value.strip(), "draw")
        
        if auto_mode:
            toggle_auto_mode()

def update_display():
    """Mettre à jour l'affichage"""
    score_label.set_text(f"Score X: {scores['X']} | O: {scores['O']}")
    x_score_label.set_text(str(scores["X"]))
    o_score_label.set_text(str(scores["O"]))
    update_grid_display()

def update_grid_display():
    """CORRECTION: Mise à jour forcée de la grille"""
    CELL = 35
    
    for r in range(ROWS):
        for c in range(COLS):
            if cells[r][c] is not None:
                cell = grid[r][c] or ""
                if cell == "X":
                    color = "white"; bg = "red"; text = "X"
                elif cell == "O":
                    color = "white"; bg = "blue"; text = "O"
                else:
                    color = "black"; bg = "#DEDBD2"; text = "-"
                
                # Mise à jour du texte et du style
                cells[r][c].set_text(text)
                cells[r][c].style(
                    f"width:{CELL}px; height:{CELL}px; line-height:{CELL}px;"
                    f"text-align:center; border-radius:5px; border:1px solid #4A5759;"
                    f"font-weight:bold; margin:2px;"
                    f"background-color:{bg}; color:{color};"
                )

def toggle_auto_mode():
    """Active ou désactive le mode automatique"""
    global auto_mode, auto_timer
    
    auto_mode = not auto_mode
    
    if auto_mode:
        auto_button.text = "Arrêter Auto"
        auto_button.style("background-color:#E74C3C;")
        append_log("=== MODE AUTO ACTIVÉ ===")
        # Démarrer un timer répétitif
        auto_timer = ui.timer(10.0, auto_play)
    else:
        auto_button.text = "Mode Auto"
        auto_button.style("background-color:#3498DB;")
        append_log("=== MODE AUTO DÉSACTIVÉ ===")
        # Arrêter et détruire le timer
        if auto_timer:
            auto_timer.cancel()
            auto_timer.deactivate()
            auto_timer = None

def auto_play():
    """Joue automatiquement les coups jusqu'à la fin de la partie"""
    # Vérifier si la partie est terminée AVANT de jouer un coup
    backend_grid = []
    for r in range(ROWS):
        row = []
        for c in range(COLS):
            cell = grid[r][c]
            row.append(" " if cell == "" else cell)
        backend_grid.append(row)
    
    if (game_engine.check_winner(backend_grid, "X") or 
        game_engine.check_winner(backend_grid, "O") or 
        game_engine.is_grid_full(backend_grid)):
        # La partie est finie, on arrête le mode auto
        append_log("Partie terminée - Arrêt du mode auto")
        toggle_auto_mode()
        return
    
    # Si la partie n'est pas finie, on joue un coup
    make_move()

# ---------------- UI ----------------
with ui.column().style("""
    justify-content: center; 
    align-items: center; 
    width: 90%; 
    max-width: 800px; 
    margin: auto;
"""):

    ui.label("Tic Tac Toe - LLM Battle").style(
        "font-size: 28px; font-weight: bold; text-align:center; margin-bottom:20px; color:#4A5759;"
    )

    with ui.row().style("width:100%; justify-content:center; gap:8px; margin-bottom:10px;"):
        model_x_input = ui.input("Model X", value="phi3").props("placeholder='Model for X'").style("width:40%")
        model_o_input = ui.input("Model O", value="phi3").props("placeholder='Model for O'").style("width:40%")
        api_input = ui.input("API URL", value=API_URL).props("placeholder='http://127.0.0.1:8000'").style("width:100%")

    with ui.row().style("width:100%; justify-content:center; margin-bottom:10px;"):
        game_id_label = ui.label("Game ID: (non démarré)").style("font-size:12px; color:#666;")

    with ui.row().style("""
        justify-content: space-between; 
        align-items: flex-start; 
        width: 100%;
        overflow-x: auto;
    """):

        with ui.column().style("align-items: center;"):
            ui.label("X").style("color:red; font-weight:bold; font-size:22px;")
            x_score_label = ui.label(str(scores["X"])).style("font-size:22px; font-weight:bold; color:red;")

        with ui.column().style("align-items: center; flex-shrink:0;"):
            ui.label("Scores").style("font-size:20px; font-weight:bold; margin-bottom:5px; color:#4A5759;")
            score_label = ui.label(f"Score X: {scores['X']} | O: {scores['O']}").style(
                "font-size: 20px; font-weight: bold; margin-bottom:15px; text-align:center;"
            )

            grid_container = ui.column().style("""
                align-items:center; 
                padding:15px; 
                border-radius:10px; 
                box-shadow: 2px 2px 10px rgba(0,0,0,0.2);
                overflow-x:auto;
            """)
            
        with ui.column().style("align-items: center;"):
            ui.label("O").style("color:blue; font-weight:bold; font-size:22px;")
            o_score_label = ui.label(str(scores["O"])).style("font-size:22px; font-weight:bold; color:blue;")

    with ui.row().style("width:100%; justify-content:center; margin-top:12px;"):
        with ui.column().style("width:100%; max-width:800px;"):
            ui.label("Logs (dernier en haut)").style("font-size:13px; color:#666; margin-bottom:5px;")
            logs_text = ui.label("").style("white-space:pre-wrap; max-height:200px; overflow:auto; background:#fafafa; padding:8px; border-radius:6px; border:1px solid #eee;")
    
    with ui.row().style("width:100%; justify-content:center; margin-top:12px;"):
        with ui.column().style("width:100%; max-width:800px;"):
            ui.label("Statistiques des modèles").style("font-size:13px; color:#666; margin-bottom:5px;")
            stats_label = ui.label("Statistiques des modèles:").style(
                "white-space:pre-wrap; max-height:200px; overflow:auto; background:#fafafa; padding:8px; border-radius:6px; border:1px solid #eee;"
            )

def display_grid():
    global cells_initialized

    CELL = 35

    if not cells_initialized:
        grid_container.clear()
        for r in range(ROWS):
            with grid_container:
                with ui.row().style("justify-content: center; align-items: center; width: 100%;"):
                    for c in range(COLS):
                        cell_value = grid[r][c] or ""
                        lbl = ui.label(cell_value or "-").style(
                            f"width:{CELL}px; height:{CELL}px; line-height:{CELL}px;"
                            f"text-align:center; border-radius:5px; border:1px solid #4A5759;"
                            f"font-weight:bold; margin:2px; background-color:#DEDBD2; color:black;"
                        )
                        cells[r][c] = lbl
        cells_initialized = True

    # Mise à jour initiale
    update_grid_display()

with ui.column().style(
    "align-items:center; position: fixed; bottom: 0; width: 100%; padding: 10px 0; background-color:#fff;"
):
    with ui.row().style("gap: 10px;"):
        ui.button("Nouvelle Partie", on_click=init_game).style(
            "font-size:18px; padding:10px 25px; background-color:#4A5759; color:white; border-radius:5px;"
        )
        ui.button("Jouer un coup", on_click=make_move).style(
            "font-size:18px; padding:10px 25px; background-color:#B0C4B1; color:white; border-radius:5px;"
        )
        auto_button = ui.button("Mode Auto", on_click=toggle_auto_mode).style(
            "font-size:18px; padding:10px 25px; background-color:#3498DB; color:white; border-radius:5px;"
        )
    
    ui.label("© 2025 All rights reserved").style("text-align:center; margin-top:10px; color:gray;")

display_grid()

if __name__ in {"__main__", "__mp_main__"}:
    ui.run()