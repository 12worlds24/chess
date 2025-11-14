"""
Game API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.schemas.game import (
    GameCreate,
    GameResponse,
    MoveRequest,
    MoveResponse,
    GameSessionResponse,
    GameAnalysisRequest,
    GameAnalysisResponse,
)
from app.services.game_service import GameService
from app.services.chess_engine import get_engine
from app.utils.logger import get_logger
from app.utils.recovery import recover_database

logger = get_logger(__name__)
router = APIRouter(prefix="/api/games", tags=["games"])

game_service = GameService()


@router.post("/", response_model=GameResponse, status_code=status.HTTP_201_CREATED)
@recover_database
def create_game(
    game_data: GameCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new game.
    
    Args:
        game_data: Game creation data.
        db: Database session.
        
    Returns:
        Created game.
    """
    try:
        # If it's a bot game, set black_player_id to None
        black_player_id = None if game_data.is_bot_game else game_data.black_player_id
        
        game = game_service.create_game(
            db=db,
            white_player_id=game_data.white_player_id,
            black_player_id=black_player_id,
            is_bot_game=game_data.is_bot_game
        )
        
        # Set bot difficulty if it's a bot game
        if game_data.is_bot_game and game_data.bot_difficulty is not None:
            from app.services.chess_engine import get_engine
            engine = get_engine()
            engine.engine.configure({"Skill Level": game_data.bot_difficulty})
            logger.info(f"Bot difficulty set to {game_data.bot_difficulty} for game {game.id}")
        
        return game
    except Exception as e:
        logger.error(f"Error creating game: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create game"
        )


@router.get("/{game_id}", response_model=GameResponse)
@recover_database
def get_game(
    game_id: int,
    db: Session = Depends(get_db)
):
    """
    Get game by ID.
    
    Args:
        game_id: Game ID.
        db: Database session.
        
    Returns:
        Game data.
    """
    game = game_service.get_game(db, game_id)
    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game not found"
        )
    return game


@router.get("/{game_id}/session", response_model=GameSessionResponse)
@recover_database
def get_game_session(
    game_id: int,
    db: Session = Depends(get_db)
):
    """
    Get current game session.
    
    Args:
        game_id: Game ID.
        db: Database session.
        
    Returns:
        Game session data.
    """
    session = game_service.get_game_session(db, game_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Game session not found"
        )
    return session


@router.post("/move", response_model=MoveResponse)
@recover_database
def make_move(
    move_data: MoveRequest,
    db: Session = Depends(get_db)
):
    """
    Make a move in the game.
    
    Args:
        move_data: Move data.
        db: Database session.
        
    Returns:
        Move response.
    """
    try:
        success, message, new_fen, bot_move = game_service.make_move(
            db=db,
            game_id=move_data.game_id,
            move_uci=move_data.move,
            player_id=move_data.player_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
        
        # Get game status
        game = game_service.get_game(db, move_data.game_id)
        game_status = game.status.value if game else None
        
        # Get move history from session
        session = game_service.get_game_session(db, move_data.game_id)
        move_history = []
        if session and session.move_history:
            import json
            move_history = json.loads(session.move_history)
        
        return MoveResponse(
            success=True,
            message=message,
            new_fen=new_fen,
            game_status=game_status,
            bot_move=bot_move,
            move_history=move_history
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error making move: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to make move"
        )


@router.post("/{game_id}/analyze", response_model=GameAnalysisResponse)
@recover_database
def analyze_position(
    game_id: int,
    analysis_data: GameAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    Analyze current game position.
    
    Args:
        game_id: Game ID.
        analysis_data: Analysis request data.
        db: Database session.
        
    Returns:
        Analysis result.
    """
    try:
        session = game_service.get_game_session(db, game_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Game session not found"
            )
        
        import chess
        board = chess.Board(session.current_fen)
        engine = get_engine()
        
        analysis = engine.analyze_position(board, depth=analysis_data.depth)
        
        return GameAnalysisResponse(
            score=analysis["score"],
            depth=analysis["depth"],
            best_moves=analysis["pv"],
            nodes=analysis["nodes"],
            time=analysis["time"]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing position: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze position"
        )


@router.post("/{game_id}/suggest-move")
@recover_database
def suggest_move(
    game_id: int,
    db: Session = Depends(get_db)
):
    """
    Get move suggestion for current position.
    
    Args:
        game_id: Game ID.
        db: Database session.
        
    Returns:
        Best move suggestion.
    """
    try:
        session = game_service.get_game_session(db, game_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Game session not found"
            )
        
        import chess
        board = chess.Board(session.current_fen)
        engine = get_engine()
        
        # Get best move
        best_move = engine.get_best_move(board)
        if not best_move:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No legal moves available"
            )
        
        # Analyze position for evaluation
        analysis = engine.analyze_position(board, depth=10)
        
        return {
            "suggested_move": best_move.uci(),
            "evaluation": str(analysis["score"]),
            "depth": analysis["depth"]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error suggesting move: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to suggest move"
        )


@router.post("/{game_id}/undo")
@recover_database
def undo_move(
    game_id: int,
    num_moves: int = Query(default=1, ge=1, le=10),
    db: Session = Depends(get_db)
):
    """
    Undo last move(s) in the game.
    
    Args:
        game_id: Game ID.
        num_moves: Number of moves to undo (default: 1).
        db: Database session.
        
    Returns:
        Updated game state.
    """
    try:
        success, message, new_fen = game_service.undo_move(
            db=db,
            game_id=game_id,
            num_moves=num_moves
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
        
        # Get updated session
        session = game_service.get_game_session(db, game_id)
        move_history = []
        if session and session.move_history:
            import json
            move_history = json.loads(session.move_history)
        
        # Get game status
        game = game_service.get_game(db, game_id)
        game_status = game.status.value if game else None
        
        return {
            "success": True,
            "message": message,
            "new_fen": new_fen,
            "game_status": game_status,
            "move_history": move_history
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error undoing move: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to undo move"
        )

