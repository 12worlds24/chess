"""
Scheduler service for running scheduled tasks.
"""
import threading
import time
from datetime import datetime
from typing import Callable, Optional
from croniter import croniter
import pytz

from app.config import get_config
from app.utils.logger import get_logger
from app.utils.lock import lock
from app.utils.retry import retry_on_failure

logger = get_logger(__name__)


class Scheduler:
    """Scheduler for running periodic tasks."""
    
    def __init__(self):
        """Initialize scheduler."""
        self.config = get_config()
        self.enabled = self.config.scheduler.enabled
        self.run_on_startup = self.config.scheduler.run_on_startup
        self.cron_expression = self.config.scheduler.cron_expression
        self.timezone = pytz.timezone(self.config.scheduler.timezone)
        
        self.scheduler_thread: Optional[threading.Thread] = None
        self.stop_scheduler = threading.Event()
        self.tasks: list[dict] = []
        
        if self.enabled:
            self.start()
    
    def register_task(
        self,
        name: str,
        task_func: Callable,
        cron_expr: Optional[str] = None,
        run_on_startup: Optional[bool] = None
    ):
        """
        Register a scheduled task.
        
        Args:
            name: Task name.
            task_func: Task function to execute.
            cron_expr: Cron expression. If None, uses default.
            run_on_startup: Whether to run on startup. If None, uses config.
        """
        cron_expr = cron_expr or self.cron_expression
        run_on_startup = run_on_startup if run_on_startup is not None else self.run_on_startup
        
        self.tasks.append({
            "name": name,
            "func": task_func,
            "cron_expr": cron_expr,
            "run_on_startup": run_on_startup,
            "last_run": None,
            "next_run": None,
        })
        
        logger.info(f"Registered scheduled task: {name}")
    
    def _calculate_next_run(self, cron_expr: str, timezone: pytz.timezone) -> datetime:
        """
        Calculate next run time from cron expression.
        
        Args:
            cron_expr: Cron expression.
            timezone: Timezone.
            
        Returns:
            Next run datetime.
        """
        now = datetime.now(timezone)
        cron = croniter(cron_expr, now)
        return cron.get_next(datetime)
    
    def _run_task(self, task: dict):
        """
        Run a scheduled task with lock mechanism.
        
        Args:
            task: Task dictionary.
        """
        task_name = task["name"]
        lock_name = f"scheduler_{task_name}"
        
        try:
            # Try to acquire lock (non-blocking)
            with lock(lock_name, timeout=0):
                logger.info(f"Running scheduled task: {task_name}")
                
                try:
                    # Execute task with retry
                    @retry_on_failure()
                    def execute_task():
                        return task["func"]()
                    
                    execute_task()
                    
                    task["last_run"] = datetime.now(self.timezone)
                    logger.info(f"Completed scheduled task: {task_name}")
                    
                except Exception as e:
                    logger.error(f"Error executing scheduled task {task_name}: {e}", exc_info=True)
                    # Send alert for critical errors
                    from app.utils.email import get_email_service
                    email_service = get_email_service()
                    email_service.send_error_alert(
                        error_type="scheduled_task_failure",
                        error_message=str(e),
                        context={"task_name": task_name}
                    )
        except RuntimeError:
            # Lock acquisition failed - task is already running
            logger.warning(f"Scheduled task {task_name} is already running, skipping")
    
    def _scheduler_loop(self):
        """Main scheduler loop."""
        logger.info("Scheduler started")
        
        # Run tasks on startup if configured
        if self.run_on_startup:
            for task in self.tasks:
                if task["run_on_startup"]:
                    logger.info(f"Running task on startup: {task['name']}")
                    self._run_task(task)
        
        # Calculate initial next run times
        for task in self.tasks:
            task["next_run"] = self._calculate_next_run(task["cron_expr"], self.timezone)
            logger.info(
                f"Task {task['name']} next run: {task['next_run']}"
            )
        
        while not self.stop_scheduler.is_set():
            try:
                now = datetime.now(self.timezone)
                
                # Check each task
                for task in self.tasks:
                    if task["next_run"] and now >= task["next_run"]:
                        # Run task in separate thread to avoid blocking
                        task_thread = threading.Thread(
                            target=self._run_task,
                            args=(task,),
                            daemon=True,
                            name=f"Scheduler-{task['name']}"
                        )
                        task_thread.start()
                        
                        # Calculate next run time
                        task["next_run"] = self._calculate_next_run(
                            task["cron_expr"],
                            self.timezone
                        )
                        logger.debug(
                            f"Task {task['name']} next run scheduled: {task['next_run']}"
                        )
                
                # Sleep for a short interval
                time.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}", exc_info=True)
                time.sleep(60)  # Wait longer on error
        
        logger.info("Scheduler stopped")
    
    def start(self):
        """Start scheduler."""
        if not self.enabled:
            logger.info("Scheduler is disabled")
            return
        
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            logger.warning("Scheduler thread already running")
            return
        
        self.stop_scheduler.clear()
        self.scheduler_thread = threading.Thread(
            target=self._scheduler_loop,
            daemon=True,
            name="Scheduler"
        )
        self.scheduler_thread.start()
        logger.info("Scheduler thread started")
    
    def stop(self):
        """Stop scheduler."""
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.stop_scheduler.set()
            self.scheduler_thread.join(timeout=10)
            logger.info("Scheduler stopped")


# Global scheduler instance
_scheduler: Optional[Scheduler] = None


def get_scheduler() -> Scheduler:
    """
    Get global scheduler instance.
    
    Returns:
        Scheduler instance.
    """
    global _scheduler
    if _scheduler is None:
        _scheduler = Scheduler()
    return _scheduler


def register_scheduled_task(
    name: str,
    cron_expr: Optional[str] = None,
    run_on_startup: Optional[bool] = None
):
    """
    Decorator for registering scheduled tasks.
    
    Args:
        name: Task name.
        cron_expr: Cron expression.
        run_on_startup: Whether to run on startup.
        
    Returns:
        Decorator function.
    """
    def decorator(func: Callable) -> Callable:
        scheduler = get_scheduler()
        scheduler.register_task(name, func, cron_expr, run_on_startup)
        return func
    return decorator

