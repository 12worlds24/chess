"""
Game service for managing chess games.
"""
import chess
import chess.pgn
from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.game import Game, GameSession, GameStatus
from app.services.chess_engine import get_engine
from app.utils.logger import get_logger
from app.utils.recovery import recover_database

logger = get_logger(__name__)


class GameService:
    """Service for managing chess games."""
    
    def __init__(self):
        """Initialize game service."""
        self.engine = get_engine()
    
    @recover_database
    def create_game(
        self,
        db: Session,
        white_player_id: Optional[int] = None,
        black_player_id: Optional[int] = None,
        is_bot_game: bool = False
    ) -> Game:
        """
        Create a new game.
        
        Args:
            db: Database session.
            white_player_id: White player user ID.
            black_player_id: Black player user ID.
            is_bot_game: Whether this is a bot game.
            
        Returns:
            Created Game instance.
        """
        game = Game(
            white_player_id=white_player_id,
            black_player_id=black_player_id,
            status=GameStatus.IN_PROGRESS
        )
        db.add(game)
        db.commit()
        db.refresh(game)
        
        # Create initial game session
        board = chess.Board()
        session = GameSession(
            game_id=game.id,
            current_fen=board.fen(),
            move_history="[]"
        )
        db.add(session)
        db.commit()
        
        logger.info(f"Created game {game.id}")
        return game
    
    @recover_database
    def get_game(self, db: Session, game_id: int) -> Optional[Game]:
        """
        Get game by ID.
        
        Args:
            db: Database session.
            game_id: Game ID.
            
        Returns:
            Game instance or None.
        """
        return db.query(Game).filter(Game.id == game_id).first()
    
    @recover_database
    def get_game_session(self, db: Session, game_id: int) -> Optional[GameSession]:
        """
        Get current game session.
        
        Args:
            db: Database session.
            game_id: Game ID.
            
        Returns:
            GameSession instance or None.
        """
        return db.query(GameSession).filter(
            GameSession.game_id == game_id
        ).order_by(GameSession.created_at.desc()).first()
    
    def make_move(
        self,
        db: Session,
        game_id: int,
        move_uci: str,
        player_id: Optional[int] = None
    ) -> tuple[bool, str, Optional[str], Optional[str]]:
        """
        Make a move in the game.
        
        Args:
            db: Database session.
            game_id: Game ID.
            move_uci: Move in UCI format.
            player_id: Player ID making the move.
            
        Returns:
            Tuple of (success, message, new_fen, bot_move).
        """
        game = self.get_game(db, game_id)
        if not game:
            return False, "Game not found", None, None
        
        if game.status != GameStatus.IN_PROGRESS:
            return False, "Game is not in progress", None, None
        
        session = self.get_game_session(db, game_id)
        if not session:
            return False, "Game session not found", None, None
        
        # Parse current position
        try:
            board = chess.Board(session.current_fen)
        except ValueError:
            return False, "Invalid board position", None, None
        
        # Validate move
        try:
            move = chess.Move.from_uci(move_uci)
            logger.debug(f"Validating move: {move_uci}, legal moves count: {len(list(board.legal_moves))}")
            if move not in board.legal_moves:
                logger.warning(f"Invalid move: {move_uci} not in legal moves")
                return False, "Invalid move", None, None
        except ValueError as e:
            logger.error(f"Invalid move format: {move_uci}, error: {e}")
            return False, "Invalid move format", None, None
        
        # Make move
        board.push(move)
        new_fen = board.fen()
        
        # Update session
        import json
        move_history = json.loads(session.move_history or "[]")
        move_history.append(move_uci)
        session.current_fen = new_fen
        session.move_history = json.dumps(move_history)
        session.last_move_at = datetime.now()
        db.commit()
        
        # Check game result
        game_result = self.engine.get_game_result(board)
        bot_move = None
        
        if game_result:
            # Game ended
            if game_result == "white_won":
                game.status = GameStatus.WHITE_WON
            elif game_result == "black_won":
                game.status = GameStatus.BLACK_WON
            else:
                game.status = GameStatus.DRAW
            
            game.ended_at = datetime.now()
            
            # Generate PGN
            pgn = self._generate_pgn(board, move_history)
            game.pgn = pgn
            
            db.commit()
            return True, f"Game ended: {game_result}", new_fen, None
        
        # If it's a bot game and it's bot's turn, get bot move
        # Bot is black (black_player_id is None) and it's black's turn
        if game.black_player_id is None and not board.turn:  # Bot is black, and it's black's turn
            try:
                logger.info(f"Bot's turn - current position: {board.fen()}, turn: {board.turn}")
                bot_move_obj = self.engine.get_best_move(board)
                if bot_move_obj:
                    bot_move = bot_move_obj.uci()
                    board.push(bot_move_obj)
                    new_fen = board.fen()  # Update new_fen with bot's move
                    
                    logger.info(f"Bot played: {bot_move}, new position: {new_fen}")
                    
                    # Update session with bot move
                    move_history.append(bot_move)
                    session.current_fen = new_fen
                    session.move_history = json.dumps(move_history)
                    session.last_move_at = datetime.now()
                    db.commit()
                    
                    # Check if bot move ended the game
                    game_result = self.engine.get_game_result(board)
                    if game_result:
                        if game_result == "black_won":
                            game.status = GameStatus.BLACK_WON
                        elif game_result == "white_won":
                            game.status = GameStatus.WHITE_WON
                        else:
                            game.status = GameStatus.DRAW
                        
                        game.ended_at = datetime.now()
                        pgn = self._generate_pgn(board, move_history)
                        game.pgn = pgn
                        db.commit()
                        return True, f"Game ended: {game_result}", new_fen, bot_move
                else:
                    logger.warning("Bot could not find a move")
            except Exception as e:
                logger.error(f"Error getting bot move: {e}", exc_info=True)
        else:
            logger.info(f"Not bot's turn - black_player_id: {game.black_player_id}, board.turn: {board.turn}, is_bot_game: {game.black_player_id is None}")
        
        return True, "Move successful", new_fen, bot_move
    
    @recover_database
    def undo_move(
        self,
        db: Session,
        game_id: int,
        num_moves: int = 1
    ) -> tuple[bool, str, Optional[str]]:
        """
        Undo last move(s) in the game.
        
        Args:
            db: Database session.
            game_id: Game ID.
            num_moves: Number of moves to undo (default: 1).
            
        Returns:
            Tuple of (success, message, new_fen).
        """
        game = self.get_game(db, game_id)
        if not game:
            return False, "Game not found", None
        
        session = self.get_game_session(db, game_id)
        if not session:
            return False, "Game session not found", None
        
        # Parse move history
        import json
        move_history = json.loads(session.move_history or "[]")
        
        if len(move_history) < num_moves:
            return False, f"Not enough moves to undo. Only {len(move_history)} moves available.", None
        
        # Reconstruct board from initial position
        board = chess.Board()
        
        # Replay moves except the last num_moves
        for move_uci in move_history[:-num_moves]:
            try:
                move = chess.Move.from_uci(move_uci)
                board.push(move)
            except ValueError:
                return False, "Invalid move in history", None
        
        new_fen = board.fen()
        new_move_history = move_history[:-num_moves]
        
        # Update session
        session.current_fen = new_fen
        session.move_history = json.dumps(new_move_history)
        session.last_move_at = datetime.now()
        
        # Reset game status if game was ended
        if game.status != GameStatus.IN_PROGRESS:
            game.status = GameStatus.IN_PROGRESS
            game.ended_at = None
            game.pgn = None
        
        db.commit()
        
        logger.info(f"Undid {num_moves} move(s) in game {game_id}")
        return True, f"Undid {num_moves} move(s)", new_fen
    
    def _generate_pgn(self, board: chess.Board, move_history: list) -> str:
        """
        Generate PGN from move history.
        
        Args:
            board: Final board position.
            move_history: List of moves in UCI format.
            
        Returns:
            PGN string.
        """
        game = chess.pgn.Game()
        node = game
        
        # Reconstruct game from moves
        temp_board = chess.Board()
        for move_uci in move_history:
            move = chess.Move.from_uci(move_uci)
            if move in temp_board.legal_moves:
                temp_board.push(move)
                node = node.add_variation(move)
        
        return str(game)

