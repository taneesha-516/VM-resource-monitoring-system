"""Detect missing heartbeats using server receipt time."""
import threading
import time

from models.alert import set_alert
from models.db import get_db


def sweep_offline(now=None):
    from flask import current_app

    now = time.time() if now is None else now
    timeout = current_app.config["OFFLINE_TIMEOUT"]
    connection = get_db()
    # Serialize the read/update with incoming samples to avoid stale decisions.
    with connection:
        connection.execute("BEGIN IMMEDIATE")
        rows = connection.execute(
            "SELECT * FROM virtual_machines WHERE status='online' AND last_seen < ?",
            (now - timeout,),
        ).fetchall()
        for vm in rows:
            elapsed = now - vm["last_seen"]
            connection.execute(
                "UPDATE virtual_machines SET status='offline' WHERE id=?", (vm["id"],)
            )
            set_alert(
                vm, "offline", elapsed, timeout, "critical", now,
                f"{vm['hostname']} is offline: no metrics for {elapsed:.1f} seconds.",
            )


def start_monitor(app):
    """Return a stop event and thread so shutdown can be graceful."""
    stopped = threading.Event()
    interval = min(5.0, app.config["OFFLINE_TIMEOUT"] / 2)

    def watch():
        while not stopped.wait(interval):
            try:
                with app.app_context():
                    sweep_offline()
            except Exception:
                app.logger.exception("Offline sweep failed; will retry")

    worker = threading.Thread(target=watch, daemon=True, name="offline-monitor")
    worker.start()
    return stopped, worker
