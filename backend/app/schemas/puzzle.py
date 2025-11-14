"""
Puzzle-related Pydantic schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models.puzzle import PuzzleDifficulty


class PuzzleResponse(BaseModel):
    """Schema for puzzle response."""
    id: int
    fen: str
    moves: str
    difficulty: PuzzleDifficulty
    theme: Optional[str]
    description: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class PuzzleAttemptRequest(BaseModel):
    """Schema for puzzle attempt."""
    puzzle_id: int
    move: str = Field(..., description="Move in UCI format")
    user_id: Optional[int] = None


class PuzzleAttemptResponse(BaseModel):
    """Schema for puzzle attempt response."""
    correct: bool
    message: str
    next_move: Optional[str] = None
    is_complete: bool = False


class PuzzleStatsResponse(BaseModel):
    """Schema for puzzle statistics."""
    user_id: int
    total_solved: int
    total_failed: int
    success_rate: float
    best_time_seconds: Optional[float]
    puzzles_by_difficulty: dict

