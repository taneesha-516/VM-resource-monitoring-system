from models.db import get_db

FIELDS = (
    "cpu_usage", "memory_usage", "memory_used", "memory_total", "disk_usage",
    "disk_used", "disk_total", "network_sent", "network_received", "uptime",
)


def insert_metric(vm_id, data, now):
    columns = ", ".join(FIELDS)
    placeholders = ", ".join("?" for _ in FIELDS)
    get_db().execute(
        f"INSERT INTO metrics(vm_id, {columns}, timestamp, agent_timestamp) "
        f"VALUES (?, {placeholders}, ?, ?)",
        (vm_id, *(data.get(field) for field in FIELDS), now, data.get("timestamp")),
    )


def latest_metric(vm_id):
    row = get_db().execute(
        "SELECT * FROM metrics WHERE vm_id=? ORDER BY timestamp DESC, id DESC LIMIT 1",
        (vm_id,),
    ).fetchone()
    return dict(row) if row else None


def metric_history(vm_id, since):
    # A one-hour view contains approximately 720 samples at the default interval.
    rows = get_db().execute(
        """SELECT * FROM (SELECT * FROM metrics WHERE vm_id=? AND timestamp>=?
        ORDER BY timestamp DESC, id DESC LIMIT 10000) ORDER BY timestamp, id""",
        (vm_id, since),
    ).fetchall()
    return [dict(row) for row in rows]
