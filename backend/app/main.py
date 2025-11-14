"""
FastAPI main application.
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import time
import traceback

from app.config import get_config
from app.utils.logger import get_logger, setup_logger
from app.database import init_db, check_db_connection
from app.api import games, puzzles
from app.services.scheduler import get_scheduler
from app.utils.metrics import get_metrics_collector
from app.utils.email import get_email_service

# Setup logger
logger = setup_logger("santrac")

# Initialize config
config = get_config()

# Create FastAPI app
app = FastAPI(
    title="Santrac API",
    description="Chess learning platform API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.api.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add request processing time header."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions."""
    logger.warning(f"HTTP {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    # Send alert for critical errors
    try:
        email_service = get_email_service()
        email_service.send_error_alert(
            error_type="unhandled_exception",
            error_message=str(exc),
            error_details=traceback.format_exc(),
            context={
                "path": str(request.url),
                "method": request.method,
            }
        )
    except Exception as e:
        logger.error(f"Failed to send error alert: {e}")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )


# Include routers
app.include_router(games.router)
app.include_router(puzzles.router)


# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        Health status.
    """
    db_healthy = check_db_connection()
    
    return {
        "status": "healthy" if db_healthy else "unhealthy",
        "database": "connected" if db_healthy else "disconnected",
        "timestamp": time.time()
    }


# Metrics endpoint
@app.get("/metrics")
async def get_metrics():
    """
    Get system metrics.
    
    Returns:
        System metrics summary.
    """
    try:
        metrics_collector = get_metrics_collector()
        return metrics_collector.get_metrics_summary()
    except Exception as e:
        logger.error(f"Error getting metrics: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Starting Santrac API...")
    
    try:
        # Initialize database
        logger.info("Initializing database...")
        init_db()
        logger.info("Database initialized")
        
        # Check database connection
        if not check_db_connection():
            logger.error("Database connection check failed")
            raise RuntimeError("Database connection failed")
        
        # Start metrics collector
        logger.info("Starting metrics collector...")
        metrics_collector = get_metrics_collector()
        metrics_collector.start_monitoring()
        logger.info("Metrics collector started")
        
        # Start scheduler
        logger.info("Starting scheduler...")
        scheduler = get_scheduler()
        scheduler.start()
        logger.info("Scheduler started")
        
        logger.info("Santrac API started successfully")
        
    except Exception as e:
        logger.error(f"Startup error: {e}", exc_info=True)
        # Send alert
        try:
            email_service = get_email_service()
            email_service.send_error_alert(
                error_type="startup_failure",
                error_message=str(e),
                error_details=traceback.format_exc()
            )
        except Exception:
            pass
        raise


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down Santrac API...")
    
    try:
        # Stop scheduler
        scheduler = get_scheduler()
        scheduler.stop()
        
        # Stop metrics collector
        metrics_collector = get_metrics_collector()
        metrics_collector.stop()
        
        # Close chess engine
        from app.services.chess_engine import _engine
        if _engine:
            _engine.close()
        
        logger.info("Santrac API shut down successfully")
    except Exception as e:
        logger.error(f"Shutdown error: {e}", exc_info=True)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Santrac Chess Learning Platform API",
        "version": "1.0.0",
        "docs": "/docs"
    }

