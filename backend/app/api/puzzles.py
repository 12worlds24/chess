"""
Puzzle API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.schemas.puzzle import (
    PuzzleResponse,
    PuzzleAttemptRequest,
    PuzzleAttemptResponse,
    PuzzleStatsResponse,
)
from app.models.puzzle import PuzzleDifficulty
from app.services.puzzle_service import PuzzleService
from app.utils.logger import get_logger
from app.utils.recovery import recover_database

logger = get_logger(__name__)
router = APIRouter(prefix="/api/puzzles", tags=["puzzles"])

puzzle_service = PuzzleService()


@router.get("/random", response_model=PuzzleResponse)
@recover_database
def get_random_puzzle(
    difficulty: Optional[PuzzleDifficulty] = Query(None, description="Puzzle difficulty"),
    db: Session = Depends(get_db)
):
    """
    Get a random puzzle.
    
    Args:
        difficulty: Optional difficulty filter.
        db: Database session.
        
    Returns:
        Random puzzle.
    """
    try:
        puzzle = puzzle_service.get_random_puzzle(db, difficulty)
        if not puzzle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No puzzles found"
            )
        return puzzle
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting random puzzle: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get puzzle"
        )


@router.get("/{puzzle_id}", response_model=PuzzleResponse)
@recover_database
def get_puzzle(
    puzzle_id: int,
    db: Session = Depends(get_db)
):
    """
    Get puzzle by ID.
    
    Args:
        puzzle_id: Puzzle ID.
        db: Database session.
        
    Returns:
        Puzzle data.
    """
    puzzle = puzzle_service.get_puzzle(db, puzzle_id)
    if not puzzle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Puzzle not found"
        )
    return puzzle


@router.post("/attempt", response_model=PuzzleAttemptResponse)
@recover_database
def attempt_puzzle(
    attempt_data: PuzzleAttemptRequest,
    db: Session = Depends(get_db)
):
    """
    Attempt to solve a puzzle move.
    
    Args:
        attempt_data: Puzzle attempt data.
        db: Database session.
        
    Returns:
        Attempt response.
    """
    try:
        correct, message, next_move, is_complete = puzzle_service.attempt_puzzle(
            db=db,
            puzzle_id=attempt_data.puzzle_id,
            move_uci=attempt_data.move,
            user_id=attempt_data.user_id
        )
        
        return PuzzleAttemptResponse(
            correct=correct,
            message=message,
            next_move=next_move,
            is_complete=is_complete
        )
    except Exception as e:
        logger.error(f"Error attempting puzzle: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process puzzle attempt"
        )


@router.get("/stats/{user_id}", response_model=PuzzleStatsResponse)
@recover_database
def get_user_stats(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Get user puzzle statistics.
    
    Args:
        user_id: User ID.
        db: Database session.
        
    Returns:
        User statistics.
    """
    try:
        stats = puzzle_service.get_user_stats(db, user_id)
        return PuzzleStatsResponse(**stats)
    except Exception as e:
        logger.error(f"Error getting user stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get statistics"
        )

