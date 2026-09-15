"""One SQLite connection per Flask request or background sweep."""
import sqlite3
from pathlib import Path

from flask import current_app, g

SCHEMA = """
CREATE TABLE IF NOT EXISTS virtual_machines (
    id INTEGER PRIMARY KEY,
    hostname TEXT NOT NULL UNIQUE,
    ip_address TEXT NOT NULL,
    first_seen REAL NOT NULL,
    last_seen REAL NOT NULL,
    status TEXT NOT NULL DEFAULT 'online'
);
CREATE TABLE IF NOT EXISTS metrics (
    id INTEGER PRIMARY KEY,
    vm_id INTEGER NOT NULL REFERENCES virtual_machines(id),
    cpu_usage REAL NOT NULL,
    memory_usage REAL NOT NULL,
    memory_used INTEGER,
    memory_total INTEGER,
    disk_usage REAL NOT NULL,
    disk_used INTEGER,
    disk_total INTEGER,
    network_sent INTEGER NOT NULL,
    network_received INTEGER NOT NULL,
    uptime REAL NOT NULL,
    timestamp REAL NOT NULL,
    agent_timestamp TEXT
);
CREATE INDEX IF NOT EXISTS metrics_vm_time ON metrics(vm_id, timestamp);
CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY,
    vm_id INTEGER NOT NULL REFERENCES virtual_machines(id),
    alert_type TEXT NOT NULL,
    message TEXT NOT NULL,
    severity TEXT NOT NULL CHECK(severity IN ('warning', 'critical')),
    value REAL NOT NULL,
    threshold REAL NOT NULL,
    timestamp REAL NOT NULL,
    resolved INTEGER NOT NULL DEFAULT 0,
    resolved_at REAL
);
CREATE UNIQUE INDEX IF NOT EXISTS one_active_alert
    ON alerts(vm_id, alert_type) WHERE resolved = 0;
"""


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"], timeout=10)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(error=None):
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()


def init_db():
    Path(current_app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)
    connection = get_db()
    connection.execute("PRAGMA journal_mode = WAL")
    connection.executescript(SCHEMA)
    connection.commit()
