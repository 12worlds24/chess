"""
Pydantic schemas.
"""
from app.schemas.game import (
    GameCreate,
    MoveRequest,
    MoveResponse,
    GameResponse,
    GameSessionResponse,
    GameAnalysisRequest,
    GameAnalysisResponse,
)
from app.schemas.puzzle import (
    PuzzleResponse,
    PuzzleAttemptRequest,
    PuzzleAttemptResponse,
    PuzzleStatsResponse,
)

__all__ = [
    "GameCreate",
    "MoveRequest",
    "MoveResponse",
    "GameResponse",
    "GameSessionResponse",
    "GameAnalysisRequest",
    "GameAnalysisResponse",
    "PuzzleResponse",
    "PuzzleAttemptRequest",
    "PuzzleAttemptResponse",
    "PuzzleStatsResponse",
]
