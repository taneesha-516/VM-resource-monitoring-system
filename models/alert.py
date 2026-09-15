from models.db import get_db


def set_alert(vm, alert_type, value, threshold, severity, now, message):
    """An active episode has exactly one row; recovery permits a new episode."""
    get_db().execute(
        """INSERT INTO alerts(vm_id, alert_type, message, severity, value,
        threshold, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(vm_id, alert_type) WHERE resolved=0 DO UPDATE SET
        value=excluded.value, message=excluded.message""",
        (vm["id"], alert_type, message, severity, value, threshold, now),
    )


def resolve_alert(vm_id, alert_type, now):
    get_db().execute(
        "UPDATE alerts SET resolved=1, resolved_at=? "
        "WHERE vm_id=? AND alert_type=? AND resolved=0",
        (now, vm_id, alert_type),
    )
