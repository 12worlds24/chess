"""
Lock mechanism to prevent concurrent execution of scheduled tasks.
"""
import os
import time
import platform
from pathlib import Path
from typing import Optional
from contextlib import contextmanager
from app.config import get_config
from app.utils.logger import get_logger

# fcntl is only available on Unix systems
if platform.system() != 'Windows':
    import fcntl
else:
    fcntl = None  # type: ignore

logger = get_logger(__name__)


class FileLock:
    """File-based lock implementation."""
    
    def __init__(self, lock_file_path: str = "./locks/santrac.lock"):
        """
        Initialize file lock.
        
        Args:
            lock_file_path: Path to lock file.
        """
        self.lock_file_path = Path(lock_file_path)
        self.lock_file_path.parent.mkdir(parents=True, exist_ok=True)
        self.lock_file = None
        self.is_locked = False
    
    def acquire(self, timeout: Optional[float] = None) -> bool:
        """
        Acquire lock.
        
        Args:
            timeout: Maximum time to wait for lock in seconds. None = no timeout.
            
        Returns:
            True if lock acquired, False otherwise.
        """
        if fcntl is None:
            # Windows fallback: use file existence as lock
            start_time = time.time()
            while True:
                try:
                    if not self.lock_file_path.exists():
                        self.lock_file_path.parent.mkdir(parents=True, exist_ok=True)
                        self.lock_file = open(self.lock_file_path, 'w')
                        self.lock_file.write(f"{os.getpid()}\n")
                        self.lock_file.flush()
                        self.is_locked = True
                        logger.debug(f"Lock acquired: {self.lock_file_path}")
                        return True
                    else:
                        # Check if lock file is stale (process doesn't exist)
                        try:
                            with open(self.lock_file_path, 'r') as f:
                                pid = int(f.read().strip())
                            # Check if process exists
                            try:
                                os.kill(pid, 0)  # Signal 0 just checks if process exists
                            except (OSError, ProcessLookupError):
                                # Process doesn't exist, remove stale lock
                                self.lock_file_path.unlink()
                                continue
                        except (ValueError, FileNotFoundError):
                            # Invalid lock file, remove it
                            if self.lock_file_path.exists():
                                self.lock_file_path.unlink()
                            continue
                        
                        if timeout is not None:
                            elapsed = time.time() - start_time
                            if elapsed >= timeout:
                                logger.warning(f"Failed to acquire lock within {timeout} seconds")
                                return False
                            time.sleep(0.1)
                        else:
                            logger.warning("Lock is held by another process")
                            return False
                except Exception as e:
                    logger.error(f"Error acquiring lock: {e}", exc_info=True)
                    return False
        
        # Unix/Linux implementation using fcntl
        start_time = time.time()
        
        while True:
            try:
                # Open lock file in append mode
                self.lock_file = open(self.lock_file_path, 'a')
                
                # Try to acquire exclusive lock (non-blocking)
                fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                
                # Write PID to lock file
                self.lock_file.write(f"{os.getpid()}\n")
                self.lock_file.flush()
                
                self.is_locked = True
                logger.debug(f"Lock acquired: {self.lock_file_path}")
                return True
                
            except (IOError, OSError) as e:
                # Lock is held by another process
                if self.lock_file:
                    self.lock_file.close()
                    self.lock_file = None
                
                if timeout is not None:
                    elapsed = time.time() - start_time
                    if elapsed >= timeout:
                        logger.warning(f"Failed to acquire lock within {timeout} seconds")
                        return False
                    
                    # Wait a bit before retrying
                    time.sleep(0.1)
                else:
                    logger.warning(f"Lock is held by another process: {e}")
                    return False
    
    def release(self):
        """Release lock."""
        if self.is_locked:
            try:
                if self.lock_file:
                    if fcntl is not None:
                        fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_UN)
                    self.lock_file.close()
                    self.lock_file = None
                
                self.is_locked = False
                
                # Remove lock file if it exists
                if self.lock_file_path.exists():
                    try:
                        self.lock_file_path.unlink()
                    except Exception:
                        pass
                
                logger.debug(f"Lock released: {self.lock_file_path}")
            except Exception as e:
                logger.error(f"Error releasing lock: {e}", exc_info=True)
    
    def __enter__(self):
        """Context manager entry."""
        if not self.acquire():
            raise RuntimeError("Failed to acquire lock")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.release()
    
    def __del__(self):
        """Cleanup on deletion."""
        if self.is_locked:
            self.release()


class LockManager:
    """Manager for multiple locks."""
    
    def __init__(self):
        """Initialize lock manager."""
        self.locks: dict[str, FileLock] = {}
        self.lock_dir = Path("./locks")
        self.lock_dir.mkdir(parents=True, exist_ok=True)
    
    def get_lock(self, name: str) -> FileLock:
        """
        Get or create a lock by name.
        
        Args:
            name: Lock name.
            
        Returns:
            FileLock instance.
        """
        if name not in self.locks:
            lock_path = self.lock_dir / f"{name}.lock"
            self.locks[name] = FileLock(str(lock_path))
        
        return self.locks[name]
    
    def acquire_lock(self, name: str, timeout: Optional[float] = None) -> bool:
        """
        Acquire a lock by name.
        
        Args:
            name: Lock name.
            timeout: Maximum time to wait.
            
        Returns:
            True if acquired, False otherwise.
        """
        lock = self.get_lock(name)
        return lock.acquire(timeout)
    
    def release_lock(self, name: str):
        """
        Release a lock by name.
        
        Args:
            name: Lock name.
        """
        if name in self.locks:
            self.locks[name].release()
    
    @contextmanager
    def lock(self, name: str, timeout: Optional[float] = None):
        """
        Context manager for acquiring and releasing a lock.
        
        Args:
            name: Lock name.
            timeout: Maximum time to wait.
            
        Yields:
            Lock instance.
            
        Raises:
            RuntimeError: If lock cannot be acquired.
        """
        lock = self.get_lock(name)
        if not lock.acquire(timeout):
            raise RuntimeError(f"Failed to acquire lock: {name}")
        
        try:
            yield lock
        finally:
            lock.release()


# Global lock manager instance
_lock_manager = LockManager()


def get_lock(name: str) -> FileLock:
    """
    Get a lock by name.
    
    Args:
        name: Lock name.
        
    Returns:
        FileLock instance.
    """
    return _lock_manager.get_lock(name)


def acquire_lock(name: str, timeout: Optional[float] = None) -> bool:
    """
    Acquire a lock by name.
    
    Args:
        name: Lock name.
        timeout: Maximum time to wait.
        
    Returns:
        True if acquired, False otherwise.
    """
    return _lock_manager.acquire_lock(name, timeout)


def release_lock(name: str):
    """
    Release a lock by name.
    
    Args:
        name: Lock name.
    """
    _lock_manager.release_lock(name)


@contextmanager
def lock(name: str, timeout: Optional[float] = None):
    """
    Context manager for acquiring and releasing a lock.
    
    Args:
        name: Lock name.
        timeout: Maximum time to wait.
        
    Yields:
        Lock instance.
        
    Raises:
        RuntimeError: If lock cannot be acquired.
    """
    with _lock_manager.lock(name, timeout):
        yield

