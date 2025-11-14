"""
Database connection and session management.
"""
from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from typing import Generator
import time

from app.config import get_config
from app.utils.logger import get_logger

logger = get_logger(__name__)

config = get_config()
engine = create_engine(
    config.database.connection_string,
    poolclass=QueuePool,
    pool_size=config.database.pool_size,
    max_overflow=config.database.max_overflow,
    pool_timeout=config.database.pool_timeout,
    pool_recycle=config.database.pool_recycle,
    echo=config.database.echo,
    connect_args={
        "connect_timeout": config.database.connection_timeout,
        "application_name": "santrac_backend"
    }
)

# Add connection pool event listeners for monitoring
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Set PostgreSQL connection parameters."""
    with dbapi_conn.cursor() as cur:
        # Optimize connection settings
        cur.execute("SET timezone = 'UTC'")
        cur.execute("SET statement_timeout = '30s'")
        cur.execute("SET lock_timeout = '10s'")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI to get database session.
    
    Yields:
        Database session.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}", exc_info=True)
        db.rollback()
        raise
    finally:
        db.close()


@contextmanager
def db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions.
    
    Yields:
        Database session.
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        logger.error(f"Database transaction error: {e}", exc_info=True)
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    """Initialize database - create all tables."""
    try:
        logger.info("Initializing database...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}", exc_info=True)
        raise


def check_db_connection() -> bool:
    """
    Check database connection health.
    
    Returns:
        True if connection is healthy, False otherwise.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False

