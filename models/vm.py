from models.db import get_db


def register_vm(hostname, ip_address, now):
    connection = get_db()
    connection.execute(
        """INSERT INTO virtual_machines(hostname, ip_address, first_seen, last_seen)
        VALUES (?, ?, ?, ?) ON CONFLICT(hostname) DO UPDATE SET
        ip_address=excluded.ip_address, last_seen=excluded.last_seen,
        status='online'""", (hostname, ip_address, now, now)
    )
    return connection.execute(
        "SELECT * FROM virtual_machines WHERE hostname = ?", (hostname,)
    ).fetchone()


def find_vm(hostname):
    return get_db().execute(
        "SELECT * FROM virtual_machines WHERE hostname = ?", (hostname,)
    ).fetchone()
