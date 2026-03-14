import chess

class PositionalEvaluator:
    """Calculates heuristic positional metrics purely from board state."""
    
    @staticmethod
    def calculate_space(board: chess.Board, color: chess.Color) -> float:
        """Evaluates territorial control in the center and enemy territory."""
        space = 0
        ranks = [1, 2, 3] if color == chess.WHITE else [4, 5, 6]
        files = [2, 3, 4, 5]  # c, d, e, f files
        
        for r in ranks:
            for f in files:
                sq = chess.square(f, r)
                # Count squares attacked by our pawns and not occupied by enemies
                pawn_attackers = [a for a in board.attackers(color, sq) 
                                 if board.piece_at(a).piece_type == chess.PAWN]
                occ = board.piece_at(sq)
                if pawn_attackers and (not occ or occ.color == color):
                    space += 1
        return space / 10.0

    @staticmethod
    def calculate_mobility(board: chess.Board, color: chess.Color) -> float:
        """Evaluates the number of safe squares available to pieces."""
        mobility = 0
        for sq, piece in board.piece_map().items():
            if piece.color == color and piece.piece_type != chess.KING:
                for target in board.attacks(sq):
                    enemy_pawns = board.pieces(chess.PAWN, not color)
                    # Safe square: not attacked by enemy pawns
                    if not any(target in board.attacks(p) for p in enemy_pawns):
                        mobility += 0.1
        return mobility

    @staticmethod
    def calculate_king_safety(board: chess.Board, color: chess.Color) -> float:
        """Evaluates pawn shield strength and distance of enemy attackers."""
        king_sq = board.king(color)
        if king_sq is None: 
            return 0.0
            
        score = 0.0
        k_file = chess.square_file(king_sq)
        shield_rank = 1 if color == chess.WHITE else 6
        
        # 1. Evaluate Pawn Shield
        for f_off in [-1, 0, 1]:
            if 0 <= k_file + f_off <= 7:
                shield_sq = chess.square(k_file + f_off, shield_rank)
                p = board.piece_at(shield_sq)
                if p and p.piece_type == chess.PAWN and p.color == color:
                    score += 0.5
                    
        # 2. Penalize for attackers in the King Zone (radius of 2 squares)
        for sq in chess.SQUARES:
            if chess.square_distance(king_sq, sq) <= 2:
                if board.is_attacked_by(not color, sq):
                    score -= 0.2
                    
        return score

    @staticmethod
    def calculate_threats(board: chess.Board) -> tuple[float, float]:
        """
        Computes tactical tension (hanging pieces, safe checks, weak squares).
        Returns a tuple of (white_threats, black_threats).
        """
        white_threats = 0.0
        black_threats = 0.0
        
        piece_values = {
            chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3,
            chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 0
        }
        
        # 1. Hanging pieces & Pieces attacked by lower-value pieces
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece is None or piece.piece_type == chess.KING:
                continue
            
            attackers = board.attackers(not piece.color, square)
            defenders = board.attackers(piece.color, square)
            
            # Hanging piece (attacked but not defended)
            if attackers and not defenders:
                if piece.color == chess.WHITE:
                    black_threats += piece_values[piece.piece_type] * 2
                else:
                    white_threats += piece_values[piece.piece_type] * 2
                    
            # Attacked by lower value piece
            elif attackers:
                min_attacker_val = min(piece_values[board.piece_at(sq).piece_type] for sq in attackers)
                if min_attacker_val < piece_values[piece.piece_type]:
                    diff = piece_values[piece.piece_type] - min_attacker_val
                    if piece.color == chess.WHITE:
                        black_threats += diff
                    else:
                        white_threats += diff

        # 2. King zone pressure
        for color in [chess.WHITE, chess.BLACK]:
            king_sq = board.king(color)
            if king_sq is None: 
                continue
            
            king_file = chess.square_file(king_sq)
            king_rank = chess.square_rank(king_sq)
            king_zone = []
            
            for df in [-1, 0, 1]:
                for dr in [-1, 0, 1]:
                    f, r = king_file + df, king_rank + dr
                    if 0 <= f <= 7 and 0 <= r <= 7:
                        king_zone.append(chess.square(f, r))
            
            enemy_attacks = sum(1 for sq in king_zone if board.attackers(not color, sq))
            if color == chess.WHITE:
                black_threats += enemy_attacks
            else:
                white_threats += enemy_attacks

        # 3. Safe checks available
        for color in [chess.WHITE, chess.BLACK]:
            enemy_king_sq = board.king(not color)
            if enemy_king_sq is None: 
                continue
            
            safe_checks = 0
            for piece_type in [chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]:
                if piece_type == chess.KNIGHT:
                    check_squares = chess.SquareSet(chess.BB_KNIGHT_ATTACKS[enemy_king_sq])
                elif piece_type == chess.BISHOP:
                    check_squares = chess.SquareSet(chess.BB_DIAG_MASKS[enemy_king_sq])
                elif piece_type == chess.ROOK:
                    check_squares = chess.SquareSet(chess.BB_FILE_MASKS[enemy_king_sq] | chess.BB_RANK_MASKS[enemy_king_sq])
                else:  # QUEEN
                    check_squares = chess.SquareSet(
                        chess.BB_DIAG_MASKS[enemy_king_sq] | 
                        chess.BB_FILE_MASKS[enemy_king_sq] | 
                        chess.BB_RANK_MASKS[enemy_king_sq]
                    )
                
                for sq in check_squares:
                    p = board.piece_at(sq)
                    if p and p.color == color and p.piece_type == piece_type:
                        # Verify safe square that actually delivers check
                        if not board.is_attacked_by(not color, sq):
                            if board.is_attacked_by(color, enemy_king_sq):
                                safe_checks += 1
            
            if color == chess.WHITE:
                white_threats += safe_checks * 0.5
            else:
                black_threats += safe_checks * 0.5

        # 4. Weak squares (holes in pawn structure)
        for color in [chess.WHITE, chess.BLACK]:
            enemy_color = not color
            target_ranks = [4, 5, 6] if color == chess.WHITE else [1, 2, 3]
            
            holes = 0
            for rank in target_ranks:
                for file in range(8):
                    sq = chess.square(file, rank)
                    can_be_defended = False
                    
                    for adj_file in [file - 1, file + 1]:
                        if 0 <= adj_file <= 7:
                            if enemy_color == chess.WHITE:
                                for pawn_rank in range(rank):
                                    pawn_sq = chess.square(adj_file, pawn_rank)
                                    p = board.piece_at(pawn_sq)
                                    if p and p.piece_type == chess.PAWN and p.color == enemy_color:
                                        can_be_defended = True
                                        break
                            else:
                                for pawn_rank in range(rank + 1, 8):
                                    pawn_sq = chess.square(adj_file, pawn_rank)
                                    p = board.piece_at(pawn_sq)
                                    if p and p.piece_type == chess.PAWN and p.color == enemy_color:
                                        can_be_defended = True
                                        break
                        if can_be_defended: 
                            break
                    
                    if not can_be_defended:
                        if board.is_attacked_by(color, sq):
                            holes += 0.3
                        else:
                            holes += 0.1
            
            if color == chess.WHITE:
                white_threats += holes
            else:
                black_threats += holes

        # 5. Check threats (if side to move can give immediate check)
        check_moves = sum(1 for move in board.legal_moves if board.gives_check(move))
        if board.turn == chess.WHITE:
            white_threats += check_moves * 0.3
        else:
            black_threats += check_moves * 0.3

        return white_threats, black_threats

    @classmethod
    def evaluate_board(cls, board: chess.Board) -> 'PositionalMetrics':
        """Aggregates all heuristics into a single PositionalMetrics data object."""
        from models import PositionalMetrics  # Inline import to avoid circular dependency
        
        white_threats, black_threats = cls.calculate_threats(board)
        
        return PositionalMetrics(
            space_w=cls.calculate_space(board, chess.WHITE),
            space_b=cls.calculate_space(board, chess.BLACK),
            mobility_w=cls.calculate_mobility(board, chess.WHITE),
            mobility_b=cls.calculate_mobility(board, chess.BLACK),
            king_safety_w=cls.calculate_king_safety(board, chess.WHITE),
            king_safety_b=cls.calculate_king_safety(board, chess.BLACK),
            threats_w=white_threats,
            threats_b=black_threats
        )