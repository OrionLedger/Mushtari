import time
from functools import wraps
from typing import Any, Dict, Optional
from infrastructure.logging.logger import get_logger

logger = get_logger("telemetry")

def log_execution_time(name: str):
    """
    Decorator to log the execution time of a function.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                duration = time.perf_counter() - start_time
                logger.info(f"telemetry: execution_time name={name} duration_seconds={duration:.4f} status=success")
                return result
            except Exception as e:
                duration = time.perf_counter() - start_time
                logger.error(f"telemetry: execution_time name={name} duration_seconds={duration:.4f} status=error error={str(e)}")
                raise
        return wrapper
    return decorator

def log_metric(name: str, value: Any, tags: Optional[Dict[str, str]] = None):
    """
    Log a simple metric with optional tags.
    """
    tag_str = " ".join([f"{k}={v}" for k, v in tags.items()]) if tags else ""
    logger.info(f"telemetry: metric name={name} value={value} {tag_str}")
