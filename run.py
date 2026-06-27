"""
run.py — Entry point for PyInstaller standalone executable.

This script is the main entry point when packaged with PyInstaller.
It:
  1. Loads .env configuration (placed next to the executable)
  2. Sets sensible defaults for local / pilot mode
  3. Starts the Uvicorn server
  4. Opens the default browser to the docs page

Usage (development):
    python run.py

Usage (packaged):
    moshtari.exe            # Uses .env next to the executable
"""
import os
import sys
import webbrowser
import threading
import time

# ── Ensure the app root is on sys.path ──────────────────────────────────
# (critical for PyInstaller bundles where _MEIPASS is the temp extraction dir)
if getattr(sys, "frozen", False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

os.chdir(BASE_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


# ── Load .env before anything else ──────────────────────────────────────
def _load_dotenv(path: str):
    """Minimal .env loader (no dependency on python-dotenv)."""
    if not os.path.isfile(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip("\"'").strip()
            if key and not os.environ.get(key):
                os.environ[key] = val


def _ensure_defaults():
    """Set defaults for local / pilot mode if not already configured."""
    os.environ.setdefault("DATABASE_TYPE", "sqlite")
    current_db = os.getenv("DATABASE_TYPE", "sqlite").lower().strip()
    if current_db == "sqlite":
        os.environ.setdefault("DATABASE_URL", "sqlite:///./data/moshtari.db")
    os.environ.setdefault("HOST", "0.0.0.0")
    os.environ.setdefault("PORT", "8000")
    os.environ.setdefault("MODELS_DIR", os.path.join(BASE_DIR, "models"))
    os.environ.setdefault("LOG_LEVEL", "INFO")

    # Ensure data directory exists
    data_dir = os.path.join(BASE_DIR, "data")
    os.makedirs(data_dir, exist_ok=True)

    # Ensure logs directory exists
    logs_dir = os.path.join(BASE_DIR, "logs")
    os.makedirs(logs_dir, exist_ok=True)


def _start_server():
    """Start Uvicorn in a separate thread."""
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))

    sep = "=" * 56
    spacer = "-" * 52
    lines = [
        sep,
        f"  Moshtari - Demand Forecasting",
        f"  {spacer}",
        f"  Database:  {os.getenv('DATABASE_TYPE', 'sqlite'):<37s}",
        f"  Server:    http://{host}:{port}/docs",
        f"  Frontend:  http://{host}:{port}/app",
        f"  {spacer}",
        f"  Press Ctrl+C to stop",
        sep,
    ]
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    print("\n".join(lines))

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        log_level=os.getenv("LOG_LEVEL", "INFO").lower(),
        reload=False,
        workers=1,
    )


def _open_browser(host: str, port: int, delay: float = 2.0):
    """Open the default browser to the docs page after a short delay."""

    def _open():
        time.sleep(delay)
        url = f"http://{host}:{port}/docs"
        try:
            webbrowser.open(url)
        except Exception:
            pass

    t = threading.Thread(target=_open, daemon=True)
    t.start()


def main():
    # Resolve .env location: next to the executable or in the project root
    env_path = os.path.join(BASE_DIR, ".env")
    if not os.path.isfile(env_path):
        # Also check next to the PyInstaller executable
        exe_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        exe_env = os.path.join(exe_dir, ".env")
        if os.path.isfile(exe_env):
            env_path = exe_env

    _load_dotenv(env_path)
    _ensure_defaults()

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))

    # Open browser after server starts
    _open_browser(host, port)

    # Start the server (blocking)
    _start_server()


if __name__ == "__main__":
    main()
