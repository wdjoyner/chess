import chess.engine
import chess.pgn
from evaluators import PositionalEvaluator
from models import GameReport, MoveAnalysis

class EngineClient:
    """Wrapper for chess.engine to manage processes and limits cleanly."""
    def __init__(self, stockfish_path: str, depth: int = 20):
        self.engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
        self.limit = chess.engine.Limit(depth=depth)

    def analyze_multipv(self, board: chess.Board, multipv: int = 3):
        return self.engine.analyse(board, self.limit, multipv=multipv)

    def close(self):
        self.engine.quit()

class GameAnalyzerFacade:
    """Orchestrates parsing, engine evaluation, and heuristic calculation."""
    def __init__(self, engine_client: EngineClient):
        self.engine = engine_client

    def _eval_to_cp(self, score: chess.engine.PovScore) -> float:
        white_score = score.white()
        if white_score.is_mate():
            mate_in = white_score.mate()
            return 10000 - abs(mate_in) * 10 if mate_in > 0 else -10000 + abs(mate_in) * 10
        return float(white_score.score() or 0)

    def analyze_game(self, game: chess.pgn.Game) -> GameReport:
        board = game.board()
        moves_data = []
        
        for node in game.mainline():
            ply = board.ply() + 1
            is_white = board.turn == chess.WHITE
            
            # 1. Analyze before move (Multi-PV)
            info_before = self.engine.analyze_multipv(board)
            best_eval = self._eval_to_cp(info_before[0]['score'])
            best_move_san = board.san(info_before[0]['pv'][0])
            
            # 2. Push move
            san_played = board.san(node.move)
            board.push(node.move)
            
            # 3. Analyze after move
            info_after = self.engine.analyze_multipv(board, multipv=1)
            current_eval = self._eval_to_cp(info_after[0]['score'])
            
            # 4. Calculate Loss
            if is_white:
                eval_loss = max(0, best_eval - current_eval)
            else:
                eval_loss = max(0, current_eval - best_eval)
                
            # 5. Positional Heuristics
            pos_metrics = PositionalEvaluator.evaluate_board(board)
            
            moves_data.append(MoveAnalysis(
                ply=ply, san=san_played, is_white=is_white,
                eval_cp=current_eval, best_move_san=best_move_san,
                eval_loss=eval_loss, classification=self._classify(eval_loss),
                positional_metrics=pos_metrics
            ))
            
        return GameReport(
            white=game.headers.get("White", "Unknown"),
            black=game.headers.get("Black", "Unknown"),
            result=game.headers.get("Result", "*"),
            moves=moves_data
        )

    def _classify(self, loss: float) -> str:
        if loss < 15: return "excellent"
        elif loss < 30: return "good"
        elif loss < 60: return "inaccuracy"
        elif loss < 120: return "mistake"
        return "blunder"