"""
Configuration management module.
Loads and validates configuration from config.json file.
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings


class DatabaseConfig(BaseModel):
    """Database configuration."""
    host: str = "postgres"
    port: int = 5432
    database: str = "santrac"
    username: str = "santrac_user"
    password: str = "santrac_password"
    connection_timeout: int = Field(default=30, ge=1, le=300)
    pool_size: int = Field(default=10, ge=1, le=50)
    max_overflow: int = Field(default=20, ge=0, le=100)
    pool_timeout: int = Field(default=30, ge=1, le=300)
    pool_recycle: int = Field(default=3600, ge=300, le=7200)
    echo: bool = False

    @property
    def connection_string(self) -> str:
        """Generate optimized PostgreSQL connection string."""
        return (
            f"postgresql://{self.username}:{self.password}@"
            f"{self.host}:{self.port}/{self.database}?"
            f"connect_timeout={self.connection_timeout}"
        )


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARN|ERROR)$")
    file_path: str = "./logs"
    file_name: str = "santrac.log"
    max_file_size_mb: int = Field(default=10, ge=1, le=100)
    backup_count: int = Field(default=5, ge=1, le=50)
    enable_console: bool = True
    enable_file: bool = True
    enable_windows_event_log: bool = True
    console_colors: bool = True


class RetryConfig(BaseModel):
    """Retry mechanism configuration."""
    max_attempts: int = Field(default=3, ge=1, le=10)
    initial_delay_seconds: float = Field(default=1.0, ge=0.1, le=60.0)
    max_delay_seconds: float = Field(default=60.0, ge=1.0, le=300.0)
    exponential_base: float = Field(default=2.0, ge=1.1, le=10.0)
    jitter: bool = True


class SchedulerConfig(BaseModel):
    """Scheduler configuration."""
    enabled: bool = True
    run_on_startup: bool = True
    cron_expression: str = "0 */6 * * *"
    timezone: str = "Europe/Istanbul"


class SMTPConfig(BaseModel):
    """SMTP configuration for email alerts."""
    enabled: bool = True
    host: str = "smtp.gmail.com"
    port: int = Field(default=587, ge=1, le=65535)
    use_tls: bool = True
    username: str = ""
    password: str = ""
    from_email: str = "noreply@santrac.com"
    from_name: str = "Santrac Platform"
    to_emails: list[str] = Field(default_factory=list)


class ResourcesConfig(BaseModel):
    """Resource limits configuration."""
    max_threads: int = Field(default=4, ge=1, le=32)
    max_cpu_percent: int = Field(default=80, ge=1, le=100)
    max_memory_mb: int = Field(default=2048, ge=256, le=16384)
    cpu_cores: Optional[int] = Field(default=None, ge=1, le=64)


class ChessEngineConfig(BaseModel):
    """Chess engine configuration."""
    stockfish_path: str = "/usr/bin/stockfish"
    skill_level: int = Field(default=10, ge=0, le=20)
    depth: int = Field(default=15, ge=1, le=30)
    time_limit_ms: int = Field(default=2000, ge=100, le=30000)


class APIConfig(BaseModel):
    """API server configuration."""
    host: str = "0.0.0.0"
    port: int = Field(default=8000, ge=1024, le=65535)
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    rate_limit_per_minute: int = Field(default=60, ge=1, le=1000)


class RecoveryConfig(BaseModel):
    """Recovery strategy configuration."""
    enabled: bool = True
    max_retries: int = Field(default=5, ge=1, le=20)
    retry_delay_seconds: int = Field(default=5, ge=1, le=60)


class RecoveryConfigs(BaseModel):
    """All recovery configurations."""
    database: RecoveryConfig
    file_system: RecoveryConfig
    network: RecoveryConfig


class MetricsConfig(BaseModel):
    """Performance metrics configuration."""
    enabled: bool = True
    memory_monitoring_interval_seconds: int = Field(default=60, ge=10, le=3600)
    memory_leak_detection: bool = True
    historical_data_retention_days: int = Field(default=7, ge=1, le=90)


class Config(BaseModel):
    """Main configuration model."""
    database: DatabaseConfig
    logging: LoggingConfig
    retry: RetryConfig
    scheduler: SchedulerConfig
    smtp: SMTPConfig
    resources: ResourcesConfig
    chess_engine: ChessEngineConfig
    api: APIConfig
    recovery: RecoveryConfigs
    metrics: MetricsConfig

    @classmethod
    def load_from_file(cls, config_path: Optional[str] = None) -> "Config":
        """
        Load configuration from JSON file.
        
        Args:
            config_path: Path to config.json file. If None, searches in common locations.
            
        Returns:
            Config instance.
            
        Raises:
            FileNotFoundError: If config file not found.
            ValueError: If config validation fails.
        """
        if config_path is None:
            # Search in common locations
            possible_paths = [
                Path("config.json"),
                Path("backend/config.json"),
                Path(__file__).parent.parent / "config.json",
                Path(os.getenv("SANTRAC_CONFIG", "")),
            ]
            
            for path in possible_paths:
                if path and path.exists():
                    config_path = str(path)
                    break
            else:
                raise FileNotFoundError(
                    "config.json not found. Please specify config_path or place "
                    "config.json in the project root or backend directory."
                )
        
        config_path = Path(config_path)
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)
            
            # Validate and create config
            config = cls(**config_data)
            
            # Create log directory if it doesn't exist
            log_dir = Path(config.logging.file_path)
            log_dir.mkdir(parents=True, exist_ok=True)
            
            return config
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file: {e}")
        except Exception as e:
            raise ValueError(f"Error loading config: {e}")


# Global config instance (lazy loaded)
_config: Optional[Config] = None


def get_config() -> Config:
    """
    Get global configuration instance.
    Loads config on first call.
    
    Returns:
        Config instance.
    """
    global _config
    if _config is None:
        _config = Config.load_from_file()
    return _config


def reload_config() -> Config:
    """
    Reload configuration from file.
    
    Returns:
        New Config instance.
    """
    global _config
    _config = Config.load_from_file()
    return _config

