"""
Retry mechanism with exponential backoff and jitter.
"""
import time
import random
from functools import wraps
from typing import Callable, TypeVar, Any, Optional
from app.config import get_config
from app.utils.logger import get_logger

logger = get_logger(__name__)

T = TypeVar('T')


def retry_on_failure(
    max_attempts: Optional[int] = None,
    initial_delay: Optional[float] = None,
    max_delay: Optional[float] = None,
    exponential_base: Optional[float] = None,
    jitter: Optional[bool] = None,
    exceptions: tuple = (Exception,)
):
    """
    Decorator for retrying functions on failure.
    
    Args:
        max_attempts: Maximum number of retry attempts. If None, uses config.
        initial_delay: Initial delay in seconds. If None, uses config.
        max_delay: Maximum delay in seconds. If None, uses config.
        exponential_base: Base for exponential backoff. If None, uses config.
        jitter: Whether to add random jitter. If None, uses config.
        exceptions: Tuple of exceptions to catch and retry on.
        
    Returns:
        Decorated function.
    """
    config_obj = get_config()
    
    max_attempts = max_attempts or config_obj.retry.max_attempts
    initial_delay = initial_delay or config_obj.retry.initial_delay_seconds
    max_delay = max_delay or config_obj.retry.max_delay_seconds
    exponential_base = exponential_base or config_obj.retry.exponential_base
    jitter = jitter if jitter is not None else config_obj.retry.jitter
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts:
                        logger.error(
                            f"Function {func.__name__} failed after {max_attempts} attempts: {e}",
                            exc_info=True
                        )
                        raise
                    
                    # Calculate delay with exponential backoff
                    delay = initial_delay * (exponential_base ** (attempt - 1))
                    delay = min(delay, max_delay)
                    
                    # Add jitter if enabled
                    if jitter:
                        jitter_amount = delay * 0.1 * random.random()
                        delay += jitter_amount
                    
                    logger.warning(
                        f"Function {func.__name__} failed (attempt {attempt}/{max_attempts}): {e}. "
                        f"Retrying in {delay:.2f} seconds..."
                    )
                    
                    time.sleep(delay)
            
            # Should never reach here, but just in case
            if last_exception:
                raise last_exception
            
            raise RuntimeError("Retry mechanism failed unexpectedly")
        
        return wrapper
    return decorator


def retry_async(
    max_attempts: Optional[int] = None,
    initial_delay: Optional[float] = None,
    max_delay: Optional[float] = None,
    exponential_base: Optional[float] = None,
    jitter: Optional[bool] = None,
    exceptions: tuple = (Exception,)
):
    """
    Decorator for retrying async functions on failure.
    
    Args:
        max_attempts: Maximum number of retry attempts. If None, uses config.
        initial_delay: Initial delay in seconds. If None, uses config.
        max_delay: Maximum delay in seconds. If None, uses config.
        exponential_base: Base for exponential backoff. If None, uses config.
        jitter: Whether to add random jitter. If None, uses config.
        exceptions: Tuple of exceptions to catch and retry on.
        
    Returns:
        Decorated async function.
    """
    import asyncio
    
    config_obj = get_config()
    
    max_attempts = max_attempts or config_obj.retry.max_attempts
    initial_delay = initial_delay or config_obj.retry.initial_delay_seconds
    max_delay = max_delay or config_obj.retry.max_delay_seconds
    exponential_base = exponential_base or config_obj.retry.exponential_base
    jitter = jitter if jitter is not None else config_obj.retry.jitter
    
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts:
                        logger.error(
                            f"Async function {func.__name__} failed after {max_attempts} attempts: {e}",
                            exc_info=True
                        )
                        raise
                    
                    # Calculate delay with exponential backoff
                    delay = initial_delay * (exponential_base ** (attempt - 1))
                    delay = min(delay, max_delay)
                    
                    # Add jitter if enabled
                    if jitter:
                        jitter_amount = delay * 0.1 * random.random()
                        delay += jitter_amount
                    
                    logger.warning(
                        f"Async function {func.__name__} failed (attempt {attempt}/{max_attempts}): {e}. "
                        f"Retrying in {delay:.2f} seconds..."
                    )
                    
                    await asyncio.sleep(delay)
            
            # Should never reach here, but just in case
            if last_exception:
                raise last_exception
            
            raise RuntimeError("Retry mechanism failed unexpectedly")
        
        return wrapper
    return decorator

