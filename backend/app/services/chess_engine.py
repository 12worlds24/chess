"""
Chess engine service using Stockfish.
"""
import chess
import chess.engine
from typing import Optional, List, Dict, Any
from pathlib import Path
import subprocess
import os

from app.config import get_config
from app.utils.logger import get_logger
from app.utils.retry import retry_on_failure

logger = get_logger(__name__)


class ChessEngine:
    """Chess engine wrapper for Stockfish."""
    
    def __init__(self):
        """Initialize chess engine."""
        self.config = get_config()
        self.engine_path = self.config.chess_engine.stockfish_path
        self.engine: Optional[chess.engine.SimpleEngine] = None
        self._initialize_engine()
    
    def _initialize_engine(self):
        """Initialize Stockfish engine."""
        try:
            # Check if Stockfish exists at configured path
            if not Path(self.engine_path).exists():
                # Try to find Stockfish in common locations
                possible_paths = [
                    "/usr/bin/stockfish",
                    "/usr/games/stockfish",
                    "/usr/local/bin/stockfish",
                ]
                
                # Also try to find in PATH
                try:
                    result = subprocess.run(
                        ["which", "stockfish"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        possible_paths.insert(0, result.stdout.strip())
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    pass
                
                # Try each possible path
                found = False
                for path in possible_paths:
                    if Path(path).exists():
                        self.engine_path = path
                        found = True
                        break
                
                if not found:
                    raise FileNotFoundError(
                        f"Stockfish not found. Tried: {possible_paths}. "
                        f"Please install Stockfish or update config.json"
                    )
            
            # Create engine
            self.engine = chess.engine.SimpleEngine.popen_uci(self.engine_path)
            
            # Configure engine (Depth is set via limit, not configure)
            self.engine.configure({
                "Skill Level": self.config.chess_engine.skill_level,
            })
            
            logger.info(f"Chess engine initialized: {self.engine_path}")
            
        except Exception as e:
            logger.error(f"Failed to initialize chess engine: {e}", exc_info=True)
            raise
    
    @retry_on_failure(exceptions=(chess.engine.EngineError, OSError))
    def get_best_move(self, board: chess.Board, time_limit_ms: Optional[int] = None) -> Optional[chess.Move]:
        """
        Get best move from engine.
        
        Args:
            board: Current chess board position.
            time_limit_ms: Time limit in milliseconds. If None, uses config.
            
        Returns:
            Best move or None if no move available.
        """
        if self.engine is None:
            self._initialize_engine()
        
        try:
            time_limit = time_limit_ms or self.config.chess_engine.time_limit_ms
            limit = chess.engine.Limit(time=time_limit / 1000.0)
            
            result = self.engine.play(board, limit)
            return result.move
            
        except Exception as e:
            logger.error(f"Error getting best move: {e}", exc_info=True)
            raise
    
    @retry_on_failure(exceptions=(chess.engine.EngineError, OSError))
    def analyze_position(self, board: chess.Board, depth: Optional[int] = None) -> Dict[str, Any]:
        """
        Analyze current position.
        
        Args:
            board: Current chess board position.
            depth: Analysis depth. If None, uses config.
            
        Returns:
            Analysis result with evaluation and best moves.
        """
        if self.engine is None:
            self._initialize_engine()
        
        try:
            analysis_depth = depth or self.config.chess_engine.depth
            limit = chess.engine.Limit(depth=analysis_depth)
            
            info = self.engine.analyse(board, limit)
            
            return {
                "score": str(info["score"]),
                "depth": info.get("depth", analysis_depth),
                "pv": [str(move) for move in info.get("pv", [])],
                "nodes": info.get("nodes", 0),
                "time": info.get("time", 0),
            }
            
        except Exception as e:
            logger.error(f"Error analyzing position: {e}", exc_info=True)
            raise
    
    def get_move_suggestions(self, board: chess.Board, num_moves: int = 3) -> List[Dict[str, Any]]:
        """
        Get multiple move suggestions.
        
        Args:
            board: Current chess board position.
            num_moves: Number of moves to suggest.
            
        Returns:
            List of move suggestions with evaluations.
        """
        if self.engine is None:
            self._initialize_engine()
        
        try:
            limit = chess.engine.Limit(depth=self.config.chess_engine.depth)
            
            with self.engine.analysis(board, limit) as analysis:
                suggestions = []
                for info in analysis:
                    if "pv" in info and "score" in info:
                        move = info["pv"][0] if info["pv"] else None
                        if move:
                            suggestions.append({
                                "move": str(move),
                                "score": str(info["score"]),
                                "depth": info.get("depth", 0),
                            })
                            
                            if len(suggestions) >= num_moves:
                                break
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error getting move suggestions: {e}", exc_info=True)
            return []
    
    def is_valid_move(self, board: chess.Board, move: str) -> bool:
        """
        Check if a move is valid.
        
        Args:
            board: Current chess board position.
            move: Move in UCI format (e.g., "e2e4").
            
        Returns:
            True if move is valid, False otherwise.
        """
        try:
            chess_move = chess.Move.from_uci(move)
            return chess_move in board.legal_moves
        except (ValueError, AttributeError):
            return False
    
    def make_move(self, board: chess.Board, move: str) -> Optional[chess.Board]:
        """
        Make a move on the board.
        
        Args:
            board: Current chess board position.
            move: Move in UCI format.
            
        Returns:
            New board state or None if move is invalid.
        """
        if not self.is_valid_move(board, move):
            return None
        
        try:
            chess_move = chess.Move.from_uci(move)
            board.push(chess_move)
            return board
        except Exception as e:
            logger.error(f"Error making move: {e}", exc_info=True)
            return None
    
    def get_game_result(self, board: chess.Board) -> Optional[str]:
        """
        Get game result.
        
        Args:
            board: Current chess board position.
            
        Returns:
            "white_won", "black_won", "draw", or None if game continues.
        """
        if board.is_checkmate():
            return "black_won" if board.turn == chess.WHITE else "white_won"
        elif board.is_stalemate():
            return "draw"
        elif board.is_insufficient_material():
            return "draw"
        elif board.is_repetition(count=3):
            return "draw"
        else:
            # Check for 75-move rule manually
            if board.halfmove_clock >= 150:  # 75 moves = 150 half-moves
                return "draw"
            return None
    
    def close(self):
        """Close engine connection."""
        if self.engine:
            try:
                self.engine.quit()
                logger.info("Chess engine closed")
            except Exception as e:
                logger.error(f"Error closing engine: {e}", exc_info=True)
            finally:
                self.engine = None
    
    def __del__(self):
        """Cleanup on deletion."""
        self.close()


# Global engine instance
_engine: Optional[ChessEngine] = None


def get_engine() -> ChessEngine:
    """
    Get global chess engine instance.
    
    Returns:
        ChessEngine instance.
    """
    global _engine
    if _engine is None:
        _engine = ChessEngine()
    return _engine

