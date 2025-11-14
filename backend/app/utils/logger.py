"""
Advanced logging module with file rotation, zip backup, and Windows Event Log support.
"""
import logging
import logging.handlers
import sys
import zipfile
import gzip
from pathlib import Path
from datetime import datetime
from typing import Optional
import platform

try:
    import win32evtlog
    import win32evtlogutil
    import win32con
    WINDOWS_EVENT_LOG_AVAILABLE = True
except ImportError:
    WINDOWS_EVENT_LOG_AVAILABLE = False

from app.config import get_config


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'WARN': '\033[33m',       # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'
    }
    
    def format(self, record):
        """Format log record with colors."""
        if hasattr(record, 'levelname'):
            color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
            reset = self.COLORS['RESET']
            record.levelname = f"{color}{record.levelname}{reset}"
        return super().format(record)


class WindowsEventLogHandler(logging.Handler):
    """Handler for Windows Event Log."""
    
    def __init__(self, app_name: str = "Santrac"):
        super().__init__()
        self.app_name = app_name
        self.available = WINDOWS_EVENT_LOG_AVAILABLE and platform.system() == "Windows"
        
        if self.available:
            try:
                win32evtlogutil.AddSourceToRegistry(
                    self.app_name,
                    win32evtlogutil.EVENTLOG_ERROR_TYPE,
                    "SYSTEM\\CurrentControlSet\\Services\\EventLog\\Application"
                )
            except Exception:
                # Source might already exist
                pass
    
    def emit(self, record):
        """Emit log record to Windows Event Log."""
        if not self.available:
            return
        
        try:
            # Only log ERROR and CRITICAL to Event Log
            if record.levelno < logging.ERROR:
                return
            
            event_type = win32evtlogutil.EVENTLOG_ERROR_TYPE
            if record.levelno >= logging.CRITICAL:
                event_type = win32evtlogutil.EVENTLOG_ERROR_TYPE
            
            msg = self.format(record)
            win32evtlogutil.ReportEvent(
                self.app_name,
                record.levelno,
                0,
                win32con.EVENTLOG_ERROR_TYPE,
                [msg]
            )
        except Exception:
            # Silently fail if Event Log is not available
            pass


class ZipRotatingFileHandler(logging.handlers.RotatingFileHandler):
    """Rotating file handler that zips old log files."""
    
    def __init__(self, filename, maxBytes=0, backupCount=0, encoding=None, delay=False):
        super().__init__(filename, mode='a', maxBytes=maxBytes, backupCount=backupCount, encoding=encoding, delay=delay)
        self.log_dir = Path(filename).parent
    
    def doRollover(self):
        """Override to zip old log files."""
        if self.stream:
            self.stream.close()
            self.stream = None
        
        if self.backupCount > 0:
            # Zip existing backup files
            for i in range(self.backupCount - 1, 0, -1):
                sfn = self.rotation_filename("%s.%d" % (self.baseFilename, i))
                zip_fn = self.rotation_filename("%s.%d.zip" % (self.baseFilename, i))
                
                if Path(sfn).exists():
                    if Path(zip_fn).exists():
                        Path(zip_fn).unlink()
                    
                    # Create zip file
                    with zipfile.ZipFile(zip_fn, 'w', zipfile.ZIP_DEFLATED) as zf:
                        zf.write(sfn, Path(sfn).name)
                    
                    Path(sfn).unlink()
            
            # Rotate current file
            dfn = self.rotation_filename(self.baseFilename + ".1")
            if Path(self.baseFilename).exists():
                Path(self.baseFilename).rename(dfn)
                
                # Zip the rotated file
                zip_fn = self.rotation_filename(self.baseFilename + ".1.zip")
                with zipfile.ZipFile(zip_fn, 'w', zipfile.ZIP_DEFLATED) as zf:
                    zf.write(dfn, Path(dfn).name)
                
                Path(dfn).unlink()
        
        if not self.delay:
            self.stream = self._open()


def setup_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Setup and configure logger with file, console, and Windows Event Log handlers.
    
    Args:
        name: Logger name. If None, uses root logger.
        
    Returns:
        Configured logger instance.
    """
    config = get_config()
    logger = logging.getLogger(name or "santrac")
    logger.setLevel(getattr(logging, config.logging.level))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Console handler
    if config.logging.enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, config.logging.level))
        
        if config.logging.console_colors:
            console_handler.setFormatter(ColoredFormatter(
                '%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%H:%M:%S'
            ))
        else:
            console_handler.setFormatter(simple_formatter)
        
        logger.addHandler(console_handler)
    
    # File handler with rotation and zip backup
    if config.logging.enable_file:
        log_file_path = Path(config.logging.file_path) / config.logging.file_name
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        max_bytes = config.logging.max_file_size_mb * 1024 * 1024
        
        file_handler = ZipRotatingFileHandler(
            str(log_file_path),
            maxBytes=max_bytes,
            backupCount=config.logging.backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, config.logging.level))
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)
    
    # Windows Event Log handler (only for ERROR and CRITICAL)
    if config.logging.enable_windows_event_log and platform.system() == "Windows":
        event_log_handler = WindowsEventLogHandler("Santrac")
        event_log_handler.setLevel(logging.ERROR)
        event_log_handler.setFormatter(detailed_formatter)
        logger.addHandler(event_log_handler)
    
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get logger instance. Creates if not exists.
    
    Args:
        name: Logger name.
        
    Returns:
        Logger instance.
    """
    logger_name = name or "santrac"
    logger = logging.getLogger(logger_name)
    
    if not logger.handlers:
        logger = setup_logger(logger_name)
    
    return logger


# Initialize root logger
_root_logger = setup_logger()

