from loguru import logger
import sys
import os

# Define log directory
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Remove default handler (to avoid double logging)
logger.remove()

# Add console handler (colored output)
logger.add(
    sys.stdout,
    colorize=True,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
           "<level>{level: <8}</level> | "
           "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
           "<level>{message}</level>",
    level="INFO"
)

# Add file handler (keeps history)
logger.add(
    f"{LOG_DIR}/app.log",
    rotation="10 MB",      # rotate logs after 10 MB
    retention="7 days",    # keep logs for 7 days
    compression="zip",     # compress old logs
    level="DEBUG",         # file keeps detailed logs
    enqueue=True           # thread-safe
)

def get_logger(module_name: str):
    """Return a logger with module-specific context."""
    return logger.bind(module=module_name)
