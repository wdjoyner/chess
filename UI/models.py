from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class PositionalMetrics:
    space_w: float = 0.0
    space_b: float = 0.0
    mobility_w: float = 0.0
    mobility_b: float = 0.0
    king_safety_w: float = 0.0
    king_safety_b: float = 0.0
    threats_w: float = 0.0
    threats_b: float = 0.0

@dataclass
class MoveAnalysis:
    ply: int
    san: str
    is_white: bool
    eval_cp: float
    best_move_san: str
    eval_loss: float
    classification: str
    fen_after: str
    positional_metrics: PositionalMetrics
    best_continuation: List[str] = field(default_factory=list)
    alternatives: List[str] = field(default_factory=list)

@dataclass
class CriticalPosition:
    ply: int
    move_san: str
    fen: str
    eval_score: float
    swing: float
    reason: str
    metrics: PositionalMetrics
    instead_of: List[str]
    best_continuation: List[str]

@dataclass
class PlayerStats:
    total_moves: int = 0
    accuracy: float = 100.0
    avg_centipawn_loss: float = 0.0
    classifications: Dict[str, int] = field(default_factory=lambda: {
        "best": 0, "excellent": 0, "good": 0, "inaccuracy": 0, "mistake": 0, "blunder": 0
    })

@dataclass
class GameReport:
    white: str
    black: str
    result: str
    white_stats: PlayerStats
    black_stats: PlayerStats
    moves: List[MoveAnalysis]
    critical_positions: List[CriticalPosition]