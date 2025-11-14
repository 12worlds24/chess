"""
Game models.
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.database import Base


class GameStatus(str, enum.Enum):
    """Game status enumeration."""
    IN_PROGRESS = "in_progress"
    WHITE_WON = "white_won"
    BLACK_WON = "black_won"
    DRAW = "draw"
    ABANDONED = "abandoned"


class Game(Base):
    """Game model."""
    __tablename__ = "games"
    
    id = Column(Integer, primary_key=True, index=True)
    white_player_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    black_player_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    pgn = Column(Text, nullable=True)  # Portable Game Notation
    status = Column(Enum(GameStatus), default=GameStatus.IN_PROGRESS, nullable=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    white_player = relationship("User", foreign_keys=[white_player_id])
    black_player = relationship("User", foreign_keys=[black_player_id])
    
    def __repr__(self):
        return f"<Game(id={self.id}, status={self.status.value})>"


class GameSession(Base):
    """Active game session model."""
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False, index=True)
    current_fen = Column(String(100), nullable=False)  # Current board position
    move_history = Column(Text, nullable=True)  # JSON array of moves
    last_move_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationship
    game = relationship("Game", backref="sessions")
    
    def __repr__(self):
        return f"<GameSession(id={self.id}, game_id={self.game_id})>"

