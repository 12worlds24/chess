"""
Error recovery strategies for database, file system, and network.
"""
import time
from typing import Callable, TypeVar, Any, Optional
from functools import wraps

from app.config import get_config
from app.utils.logger import get_logger
from app.utils.email import get_email_service
from app.database import check_db_connection

logger = get_logger(__name__)
T = TypeVar('T')


class RecoveryStrategy:
    """Base recovery strategy."""
    
    def __init__(self, strategy_type: str):
        """
        Initialize recovery strategy.
        
        Args:
            strategy_type: Type of recovery strategy (database, file_system, network).
        """
        self.strategy_type = strategy_type
        self.config = get_config()
        self.recovery_config = getattr(self.config.recovery, strategy_type)
        self.enabled = self.recovery_config.enabled
        self.max_retries = self.recovery_config.max_retries
        self.retry_delay = self.recovery_config.retry_delay_seconds
    
    def recover(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """
        Execute function with recovery strategy.
        
        Args:
            func: Function to execute.
            *args: Function arguments.
            **kwargs: Function keyword arguments.
            
        Returns:
            Function result.
            
        Raises:
            Exception: If recovery fails after max retries.
        """
        if not self.enabled:
            return func(*args, **kwargs)
        
        last_exception = None
        
        for attempt in range(1, self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                logger.warning(
                    f"{self.strategy_type} error (attempt {attempt}/{self.max_retries}): {e}"
                )
                
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)
                    # Attempt recovery action
                    self._attempt_recovery()
                else:
                    logger.error(
                        f"{self.strategy_type} recovery failed after {self.max_retries} attempts: {e}",
                        exc_info=True
                    )
                    self._send_alert(e)
        
        if last_exception:
            raise last_exception
        
        raise RuntimeError("Recovery strategy failed unexpectedly")
    
    def _attempt_recovery(self):
        """Attempt recovery action (override in subclasses)."""
        pass
    
    def _send_alert(self, error: Exception):
        """Send alert for recovery failure."""
        email_service = get_email_service()
        email_service.send_error_alert(
            error_type=f"{self.strategy_type}_recovery_failure",
            error_message=str(error),
            context={"strategy_type": self.strategy_type, "max_retries": self.max_retries}
        )


class DatabaseRecoveryStrategy(RecoveryStrategy):
    """Database recovery strategy."""
    
    def __init__(self):
        """Initialize database recovery strategy."""
        super().__init__("database")
    
    def _attempt_recovery(self):
        """Attempt database recovery."""
        logger.info("Attempting database recovery...")
        
        # Check connection
        if not check_db_connection():
            logger.warning("Database connection check failed, attempting to reconnect...")
            # Connection will be retried on next attempt
        else:
            logger.info("Database connection is healthy")


class FileSystemRecoveryStrategy(RecoveryStrategy):
    """File system recovery strategy."""
    
    def __init__(self):
        """Initialize file system recovery strategy."""
        super().__init__("file_system")
    
    def _attempt_recovery(self):
        """Attempt file system recovery."""
        logger.info("Attempting file system recovery...")
        # File system recovery actions can be added here
        # e.g., checking disk space, permissions, etc.


class NetworkRecoveryStrategy(RecoveryStrategy):
    """Network recovery strategy."""
    
    def __init__(self):
        """Initialize network recovery strategy."""
        super().__init__("network")
    
    def _attempt_recovery(self):
        """Attempt network recovery."""
        logger.info("Attempting network recovery...")
        # Network recovery actions can be added here
        # e.g., checking connectivity, DNS resolution, etc.


def with_recovery(strategy_type: str):
    """
    Decorator for applying recovery strategy to functions.
    
    Args:
        strategy_type: Type of recovery strategy (database, file_system, network).
        
    Returns:
        Decorated function.
    """
    strategies = {
        "database": DatabaseRecoveryStrategy,
        "file_system": FileSystemRecoveryStrategy,
        "network": NetworkRecoveryStrategy,
    }
    
    if strategy_type not in strategies:
        raise ValueError(f"Unknown recovery strategy: {strategy_type}")
    
    strategy_class = strategies[strategy_type]
    strategy = strategy_class()
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            return strategy.recover(func, *args, **kwargs)
        
        return wrapper
    return decorator


# Convenience functions
def recover_database(func: Callable[..., T]) -> Callable[..., T]:
    """Apply database recovery to function."""
    return with_recovery("database")(func)


def recover_file_system(func: Callable[..., T]) -> Callable[..., T]:
    """Apply file system recovery to function."""
    return with_recovery("file_system")(func)


def recover_network(func: Callable[..., T]) -> Callable[..., T]:
    """Apply network recovery to function."""
    return with_recovery("network")(func)

