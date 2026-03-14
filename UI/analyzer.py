import math
import chess.engine
import chess.pgn
from models import GameReport, MoveAnalysis, CriticalPosition, PlayerStats
from evaluators import PositionalEvaluator
from engine_service import EngineClient

class GameAnalyzerFacade:
    def __init__(self, engine_client: EngineClient):
        self.engine = engine_client

    def _eval_to_cp(self, score: chess.engine.PovScore) -> float:
        white_score = score.white()
        if white_score.is_mate():
            mate_in = white_score.mate()
            return 10000 - abs(mate_in) * 10 if mate_in > 0 else -10000 + abs(mate_in) * 10
        return float(white_score.score() or 0)

    def _classify(self, loss: float) -> str:
        if loss < 5: return "best"
        elif loss < 15: return "excellent"
        elif loss < 30: return "good"
        elif loss < 60: return "inaccuracy"
        elif loss < 120: return "mistake"
        return "blunder"

    def analyze_game(self, game: chess.pgn.Game) -> GameReport:
        board = game.board()
        moves_data = []
        critical_positions = []
        
        # Initial evaluation
        info_init = self.engine.analyze_multipv(board, multipv=1)
        prev_eval = self._eval_to_cp(info_init[0]['score'])
        
        for node in game.mainline():
            ply = board.ply() + 1
            is_white = board.turn == chess.WHITE
            
            # 1. Analyze before move (Get best move & alternatives)
            info_before = self.engine.analyze_multipv(board, multipv=3)
            best_eval = self._eval_to_cp(info_before[0]['score'])
            best_move_san = board.san(info_before[0]['pv'][0])
            
            alternatives = []
            for alt in info_before[1:]:
                if 'pv' in alt and alt['pv']:
                    alternatives.append(board.san(alt['pv'][0]))

            # 2. Push move
            san_played = board.san(node.move)
            board.push(node.move)
            fen_after = board.fen()
            
            # 3. Analyze after move (Get current eval & continuation)
            info_after = self.engine.analyze_multipv(board, multipv=1)[0]
            current_eval = self._eval_to_cp(info_after['score'])
            
            continuation = []
            temp_board = board.copy()
            for pv_move in info_after.get('pv', [])[:5]:
                continuation.append(temp_board.san(pv_move))
                temp_board.push(pv_move)
            
            # 4. Calculate Loss & Swing
            eval_loss = max(0, best_eval - current_eval) if is_white else max(0, current_eval - best_eval)
            eval_loss = min(eval_loss, 1500) # Cap mate scores
            classification = self._classify(eval_loss)
            swing = abs(current_eval - prev_eval)
            
            # 5. Positional Heuristics
            pos_metrics = PositionalEvaluator.evaluate_board(board)
            
            # 6. Register Critical Positions (Swings > 100cp)
            if swing > 100:
                reason = f"{'White' if is_white else 'Black'} blunders (+{int(swing)}cp)" if classification == "blunder" else "Critical moment"
                critical_positions.append(CriticalPosition(
                    ply=ply, move_san=san_played, fen=fen_after, eval_score=current_eval,
                    swing=swing, reason=reason, metrics=pos_metrics,
                    instead_of=[best_move_san] + alternatives[:2],
                    best_continuation=continuation
                ))

            moves_data.append(MoveAnalysis(
                ply=ply, san=san_played, is_white=is_white, eval_cp=current_eval,
                best_move_san=best_move_san, eval_loss=eval_loss, classification=classification,
                fen_after=fen_after, positional_metrics=pos_metrics, 
                best_continuation=continuation, alternatives=alternatives
            ))
            
            prev_eval = current_eval

        # Generate aggregated stats
        white_stats = self._generate_stats([m for m in moves_data if m.is_white])
        black_stats = self._generate_stats([m for m in moves_data if not m.is_white])

        return GameReport(
            white=game.headers.get("White", "Unknown"),
            black=game.headers.get("Black", "Unknown"),
            result=game.headers.get("Result", "*"),
            white_stats=white_stats,
            black_stats=black_stats,
            moves=moves_data,
            critical_positions=sorted(critical_positions, key=lambda x: x.swing, reverse=True) # Sort by biggest swing
        )

    def _generate_stats(self, moves: List[MoveAnalysis]) -> PlayerStats:
        if not moves: return PlayerStats()
        avg_loss = sum(m.eval_loss for m in moves) / len(moves)
        accuracy = max(0.0, 100 * math.exp(-0.005 * avg_loss))
        
        stats = PlayerStats(total_moves=len(moves), accuracy=accuracy, avg_centipawn_loss=avg_loss)
        for m in moves:
            stats.classifications[m.classification] += 1
        return stats