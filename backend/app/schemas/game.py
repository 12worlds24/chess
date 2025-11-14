"""
Game-related Pydantic schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models.game import GameStatus


class GameCreate(BaseModel):
    """Schema for creating a new game."""
    white_player_id: Optional[int] = None
    black_player_id: Optional[int] = None
    is_bot_game: bool = False
    bot_difficulty: Optional[int] = Field(default=10, ge=0, le=20)


class MoveRequest(BaseModel):
    """Schema for making a move."""
    game_id: int
    move: str = Field(..., description="Move in UCI format (e.g., 'e2e4')")
    player_id: Optional[int] = None


class MoveResponse(BaseModel):
    """Schema for move response."""
    success: bool
    message: str
    new_fen: Optional[str] = None
    game_status: Optional[str] = None
    bot_move: Optional[str] = None
    move_history: Optional[List[str]] = None


class GameResponse(BaseModel):
    """Schema for game response."""
    id: int
    white_player_id: Optional[int]
    black_player_id: Optional[int]
    pgn: Optional[str]
    status: GameStatus
    started_at: datetime
    ended_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class GameSessionResponse(BaseModel):
    """Schema for game session response."""
    id: int
    game_id: int
    current_fen: str
    move_history: Optional[str]
    last_move_at: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


class GameAnalysisRequest(BaseModel):
    """Schema for game analysis request."""
    game_id: int
    depth: Optional[int] = Field(default=15, ge=1, le=30)


class GameAnalysisResponse(BaseModel):
    """Schema for game analysis response."""
    score: str
    depth: int
    best_moves: List[str]
    nodes: int
    time: float

