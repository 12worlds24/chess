"""
Puzzle models.
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.database import Base


class PuzzleDifficulty(str, enum.Enum):
    """Puzzle difficulty levels."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"


class Puzzle(Base):
    """Puzzle model."""
    __tablename__ = "puzzles"
    
    id = Column(Integer, primary_key=True, index=True)
    fen = Column(String(100), nullable=False)  # Starting position
    moves = Column(Text, nullable=False)  # JSON array of solution moves
    difficulty = Column(Enum(PuzzleDifficulty), nullable=False, index=True)
    theme = Column(String(100), nullable=True)  # e.g., "tactics", "endgame"
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<Puzzle(id={self.id}, difficulty={self.difficulty.value})>"


class UserPuzzle(Base):
    """User puzzle solving statistics."""
    __tablename__ = "user_puzzles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    puzzle_id = Column(Integer, ForeignKey("puzzles.id"), nullable=False, index=True)
    solved = Column(Integer, default=0, nullable=False)  # Number of times solved
    failed = Column(Integer, default=0, nullable=False)  # Number of times failed
    best_time_seconds = Column(Float, nullable=True)  # Best solving time
    last_attempted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", backref="puzzle_attempts")
    puzzle = relationship("Puzzle", backref="user_attempts")
    
    def __repr__(self):
        return f"<UserPuzzle(user_id={self.user_id}, puzzle_id={self.puzzle_id}, solved={self.solved})>"

