from nicegui import ui
from typing import List, Optional, Any
from config import API_URL
from utils import fetch_models, safe_post, format_cell, validate_grid

ROWS, COLS = 10, 10

class TicTacToeApp:
    def __init__(self):
        self.grid = [["" for _ in range(COLS)] for _ in range(ROWS)]
        self.scores = {"X": 0, "O": 0}
        self.current_player = "X"
        self.current_game_id: Optional[str] = None
        self.auto_mode = False
        self.auto_timer: Optional[Any] = None
        self.cells: List[List[Optional[ui.label]]] = [[None for _ in range(COLS)] for _ in range(ROWS)]
        self.winner: Optional[str] = None

        # Récupérer les modèles
        self.available_models = fetch_models(API_URL)
        self.setup_ui()

    def setup_ui(self):
        # Header
        with ui.row().style("width: 100%; justify-content: center; gap: 16px; margin-bottom: 10px;"):
            ui.label("Tic Tac Toe - LLM Battle").style("font-size: 28px; font-weight: bold; margin-bottom: 20px;")
        
        # Dropdown pour modèles
        with ui.row().style("width: 100%; justify-content: center; gap: 16px; margin-bottom: 10px;"):
            default_model = self.available_models[0] if self.available_models else "phi3"
            self.model_x_input = ui.select(self.available_models, value=default_model, label="Model X").style("width: 150px;")
            self.model_o_input = ui.select(self.available_models, value=default_model, label="Model O").style("width: 150px;")
        
        # Game ID
        with ui.row().style("width: 100%; justify-content: center; gap: 16px; margin-bottom: 10px;"):
            self.game_id_label = ui.label("Game ID: (non démarré)").style("font-size: 12px; color: #666;")
        
        # Scores et colonnes X/O
        with ui.row().style("width: 100%; justify-content: center;"):
            with ui.column().style("align-items: center;"):
                ui.label("X").style("color: red; font-weight: bold; font-size: 22px;")
                self.moves_x_label = ui.label("Coups joués: 0").style("font-size: 14px; color: red;")
            with ui.column().style("align-items: center; flex-shrink: 0;"):
                ui.label("Scores").style("font-size: 20px; font-weight: bold; margin-bottom: 5px;")
                with ui.row().style("align-items: center; flex-shrink: 0;"):
                    self.x_score_label = ui.label("0").style("font-size: 22px; font-weight: bold; color: red;")
                    self.o_score_label = ui.label("0").style("font-size: 22px; font-weight: bold; color: blue;")
                self.setup_grid()
            with ui.column().style("align-items: center;"):
                ui.label("O").style("color: blue; font-weight: bold; font-size: 22px;")
                self.moves_o_label = ui.label("Coups joués: 0").style("font-size: 14px; color: blue;")
        
        # Logs et stats
        self.logs_text = ui.label("").style("white-space: pre-wrap; max-height: 200px; overflow: auto; background: #fafafa; padding: 8px; border-radius: 6px; border: 1px solid #eee; width: 100%;")
        self.stats_label = ui.label("Statistiques des modèles:").style("white-space: pre-wrap; max-height: 200px; overflow: auto; background: #fafafa; padding: 8px; border-radius: 6px; border: 1px solid #eee; width: 100%;")
        
        # Boutons
        with ui.row().style("position: fixed; bottom: 0; width: 100%; padding: 10px 0; background-color: white; justify-content: center; gap: 10px;"):
            ui.button("Nouvelle Partie", on_click=self.init_game).style("font-size: 18px; padding: 10px 25px; background-color: #4A5759; color: white; border-radius: 5px;")
            ui.button("Jouer un coup", on_click=self.make_move).style("font-size: 18px; padding: 10px 25px; background-color: #B0C4B1; color: white; border-radius: 5px;")
            self.auto_button = ui.button("Mode Auto", on_click=self.toggle_auto_mode).style("font-size: 18px; padding: 10px 25px; background-color: #3498DB; color: white; border-radius: 5px;")

    def setup_grid(self):
        CELL = 35
        self.grid_container = ui.column().style(
            "align-items: center; padding: 20px; border-radius: 10px; "
            "box-shadow: 2px 2px 10px rgba(0,0,0,0.2); background: white;"
        )

        with self.grid_container:
            for r in range(ROWS):
                with ui.row().style("justify-content: center; align-items: center;"):
                    for c in range(COLS):
                        # format_cell pour initialiser chaque case
                        text, color, bg = format_cell(" ")
                        lbl = ui.label(text).style(
                            f"width: {CELL}px; height: {CELL}px; line-height: {CELL}px; "
                            f"text-align: center; border-radius: 5px; border: 1px solid #4A5759; "
                            f"font-weight: bold; margin: 2px; background-color: {bg}; color: {color};"
                        )
                        self.cells[r][c] = lbl


    def init_game(self):
        resp = safe_post(f"{API_URL}/api/game/start", {})
        if not resp:
            ui.notify("Erreur: impossible de démarrer la partie", color="negative")
            return
        self.current_game_id = resp.get("game_id")
        self.current_player = resp.get("current_player", "X")
        self.move_count = 0
        self.move_x = 0
        self.move_y = 0
        self.grid = resp.get("grid", self.grid)
        self.winner = None  # réinitialiser à chaque nouvelle partie
        self.update_display()
        self.game_id_label.set_text(f"Game ID: {self.current_game_id}")

    def make_move(self):
        # Vérifie si la partie est déjà terminée
        if getattr(self, "winner", None):
            ui.notify("La partie est terminée", color="warning")
            return

        if not self.current_game_id:
            ui.notify("Démarrez d'abord une partie", color="warning")
            return

        model_name = self.model_x_input.value if self.current_player == "X" else self.model_o_input.value
        backend_grid = [[" " if cell == "" else cell for cell in row] for row in self.grid]
        resp = safe_post(f"{API_URL}/api/game/move", {
            "game_id": self.current_game_id,
            "grid": backend_grid,
            "current_player": self.current_player,
            "model_name": model_name
        })
        if not resp:
            ui.notify("Erreur lors du coup", color="negative")
            return

        self.grid = resp.get("grid", self.grid)
        self.current_player = resp.get("current_player", self.current_player)
        winner = resp.get("winner")
        if winner:
            self.winner = winner  # ← stocker le gagnant
            self.scores[winner] += 1
            ui.notify(f"Le joueur {winner} a gagné !", color="positive")
            if self.auto_mode:
                self.toggle_auto_mode()
        self.update_display()


    def update_display(self):
        self.x_score_label.set_text(str(self.scores["X"]))
        self.o_score_label.set_text(str(self.scores["O"]))
        self.moves_x_label.set_text(f"Coups joués: {getattr(self, 'move_x', 0)}")
        self.moves_o_label.set_text(f"Coups joués: {getattr(self, 'move_y', 0)}")
        for r in range(ROWS):
            for c in range(COLS):
                text, color, bg = format_cell(self.grid[r][c])
                cell_widget = self.cells[r][c]
                if cell_widget:
                    cell_widget.set_text(text)
                    cell_widget.style(f"background-color: {bg}; color: {color}")

    def toggle_auto_mode(self):
        self.auto_mode = not self.auto_mode
        if self.auto_mode:
            self.auto_button.text = "Arrêter Auto"
            self.auto_button.style("background-color: #E74C3C;")
            self.auto_timer = ui.timer(2.0, self.safe_auto_move)
        else:
            self.auto_button.text = "Mode Auto"
            self.auto_button.style("background-color: #3498DB;")
            if self.auto_timer: 
                self.auto_timer.cancel()

    def safe_auto_move(self):
        try:
            # Si un joueur a déjà gagné, stop le mode auto
            if self.current_game_id is None:
                return
            # Vérifie s'il y a un gagnant
            if any(score > 0 for score in self.scores.values()):
                self.toggle_auto_mode()
                return
            self.make_move()
        except Exception as e:
            print(f"[AutoMode] Erreur: {e}")


if __name__ in {"__main__", "__mp_main__"}:
    app = TicTacToeApp()
    ui.run(reconnect_timeout=120)