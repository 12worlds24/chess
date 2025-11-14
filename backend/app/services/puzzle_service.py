"""
Puzzle service for managing chess puzzles.
"""
import json
import chess
from typing import Optional, List
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.puzzle import Puzzle, UserPuzzle, PuzzleDifficulty
from app.utils.logger import get_logger
from app.utils.recovery import recover_database

logger = get_logger(__name__)


class PuzzleService:
    """Service for managing chess puzzles."""
    
    @recover_database
    def get_puzzle(
        self,
        db: Session,
        puzzle_id: int
    ) -> Optional[Puzzle]:
        """
        Get puzzle by ID.
        
        Args:
            db: Database session.
            puzzle_id: Puzzle ID.
            
        Returns:
            Puzzle instance or None.
        """
        return db.query(Puzzle).filter(Puzzle.id == puzzle_id).first()
    
    @recover_database
    def get_random_puzzle(
        self,
        db: Session,
        difficulty: Optional[PuzzleDifficulty] = None
    ) -> Optional[Puzzle]:
        """
        Get a random puzzle.
        
        Args:
            db: Database session.
            difficulty: Optional difficulty filter.
            
        Returns:
            Random Puzzle instance or None.
        """
        query = db.query(Puzzle)
        if difficulty:
            query = query.filter(Puzzle.difficulty == difficulty)
        
        import random
        puzzles = query.all()
        if puzzles:
            return random.choice(puzzles)
        return None
    
    @recover_database
    def attempt_puzzle(
        self,
        db: Session,
        puzzle_id: int,
        move_uci: str,
        user_id: Optional[int] = None
    ) -> tuple[bool, str, Optional[str], bool]:
        """
        Attempt to solve a puzzle move.
        
        Args:
            db: Database session.
            puzzle_id: Puzzle ID.
            move_uci: Move in UCI format.
            user_id: Optional user ID.
            
        Returns:
            Tuple of (correct, message, next_move, is_complete).
        """
        puzzle = self.get_puzzle(db, puzzle_id)
        if not puzzle:
            return False, "Puzzle not found", None, False
        
        # Parse solution moves
        try:
            solution_moves = json.loads(puzzle.moves)
        except (json.JSONDecodeError, TypeError):
            solution_moves = []
        
        if not solution_moves:
            return False, "Invalid puzzle data", None, False
        
        # Create board from starting position
        try:
            board = chess.Board(puzzle.fen)
        except ValueError:
            return False, "Invalid puzzle position", None, False
        
        # Replay solution moves to find current position
        current_move_index = 0
        for i, sol_move in enumerate(solution_moves):
            try:
                move = chess.Move.from_uci(sol_move)
                if move in board.legal_moves:
                    board.push(move)
                    current_move_index = i + 1
                else:
                    break
            except ValueError:
                break
        
        # Check if user's move matches solution
        if current_move_index >= len(solution_moves):
            return False, "Puzzle already solved", None, True
        
        expected_move = solution_moves[current_move_index]
        
        try:
            user_move = chess.Move.from_uci(move_uci)
            if user_move.uci() == expected_move:
                # Correct move
                board.push(user_move)
                current_move_index += 1
                
                # Check if puzzle is complete
                is_complete = current_move_index >= len(solution_moves)
                next_move = solution_moves[current_move_index] if not is_complete else None
                
                # Update user statistics
                if user_id:
                    self._update_user_stats(db, user_id, puzzle_id, success=True)
                
                return True, "Correct move!", next_move, is_complete
            else:
                # Incorrect move
                if user_id:
                    self._update_user_stats(db, user_id, puzzle_id, success=False)
                
                return False, "Incorrect move. Try again!", None, False
        except ValueError:
            return False, "Invalid move format", None, False
    
    @recover_database
    def _update_user_stats(
        self,
        db: Session,
        user_id: int,
        puzzle_id: int,
        success: bool
    ):
        """
        Update user puzzle statistics.
        
        Args:
            db: Database session.
            user_id: User ID.
            puzzle_id: Puzzle ID.
            success: Whether the attempt was successful.
        """
        user_puzzle = db.query(UserPuzzle).filter(
            UserPuzzle.user_id == user_id,
            UserPuzzle.puzzle_id == puzzle_id
        ).first()
        
        if not user_puzzle:
            user_puzzle = UserPuzzle(
                user_id=user_id,
                puzzle_id=puzzle_id,
                solved=0,
                failed=0
            )
            db.add(user_puzzle)
        
        if success:
            user_puzzle.solved += 1
        else:
            user_puzzle.failed += 1
        
        user_puzzle.last_attempted_at = datetime.now()
        db.commit()
    
    @recover_database
    def get_user_stats(
        self,
        db: Session,
        user_id: int
    ) -> dict:
        """
        Get user puzzle statistics.
        
        Args:
            db: Database session.
            user_id: User ID.
            
        Returns:
            Statistics dictionary.
        """
        user_puzzles = db.query(UserPuzzle).filter(
            UserPuzzle.user_id == user_id
        ).all()
        
        total_solved = sum(up.solved for up in user_puzzles)
        total_failed = sum(up.failed for up in user_puzzles)
        total_attempts = total_solved + total_failed
        success_rate = (total_solved / total_attempts * 100) if total_attempts > 0 else 0.0
        
        best_time = min(
            (up.best_time_seconds for up in user_puzzles if up.best_time_seconds),
            default=None
        )
        
        # Group by difficulty
        puzzles_by_difficulty = {}
        for up in user_puzzles:
            puzzle = self.get_puzzle(db, up.puzzle_id)
            if puzzle:
                diff = puzzle.difficulty.value
                if diff not in puzzles_by_difficulty:
                    puzzles_by_difficulty[diff] = {"solved": 0, "failed": 0}
                puzzles_by_difficulty[diff]["solved"] += up.solved
                puzzles_by_difficulty[diff]["failed"] += up.failed
        
        return {
            "user_id": user_id,
            "total_solved": total_solved,
            "total_failed": total_failed,
            "success_rate": round(success_rate, 2),
            "best_time_seconds": best_time,
            "puzzles_by_difficulty": puzzles_by_difficulty,
        }

