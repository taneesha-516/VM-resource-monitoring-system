"""Settings can be overridden using environment variables."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


class Config:
    DATABASE = os.getenv("DATABASE", str(BASE_DIR / "database" / "monitoring.db"))
    SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
    SERVER_PORT = int(os.getenv("SERVER_PORT", "5000"))
    METRIC_INTERVAL = float(os.getenv("METRIC_INTERVAL", "5"))
    OFFLINE_TIMEOUT = float(os.getenv("OFFLINE_TIMEOUT", "30"))
    CPU_THRESHOLD = float(os.getenv("CPU_THRESHOLD", "85"))
    MEMORY_THRESHOLD = float(os.getenv("MEMORY_THRESHOLD", "90"))
    DISK_THRESHOLD = float(os.getenv("DISK_THRESHOLD", "90"))
    MAX_CONTENT_LENGTH = 16 * 1024
