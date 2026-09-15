import time

import pytest

from models.db import get_db
from services.monitoring import start_monitor, sweep_offline


@pytest.mark.parametrize("field,threshold,kind,severity", [
    ("cpu_usage", 85, "cpu", "warning"),
    ("memory_usage", 90, "memory", "critical"),
    ("disk_usage", 90, "disk", "critical"),
])
def test_alert_episode(client, payload, field, threshold, kind, severity):
    client.post("/api/metrics", json={**payload, field: threshold})
    assert client.get("/api/alerts").json["total"] == 0
    for value in (threshold+1, threshold+2, threshold+3):
        client.post("/api/metrics", json={**payload, field: value})
    data = client.get("/api/alerts?status=active").json
    assert data["total"] == 1
    assert data["items"][0]["alert_type"] == kind
    assert data["items"][0]["severity"] == severity
    assert data["items"][0]["value"] == threshold+3
    client.post("/api/metrics", json={**payload, field: threshold})
    resolved = client.get("/api/alerts?status=resolved").json
    assert resolved["total"] == 1
    assert resolved["items"][0]["resolved_at"] is not None
    client.post("/api/metrics", json={**payload, field: threshold+1})
    assert client.get("/api/alerts").json["total"] == 2


def test_offline_boundary_reconnect(app, client, payload):
    client.post("/api/metrics", json=payload)
    with app.app_context():
        seen = get_db().execute("SELECT last_seen FROM virtual_machines").fetchone()[0]
        sweep_offline(seen+30)
        assert get_db().execute("SELECT status FROM virtual_machines").fetchone()[0] == "online"
        sweep_offline(seen+30.01)
        sweep_offline(seen+60)
    assert client.get("/api/dashboard").json["offline_vms"] == 1
    assert client.get("/api/alerts?status=active").json["total"] == 1
    client.post("/api/metrics", json=payload)
    assert client.get("/api/dashboard").json["online_vms"] == 1
    assert client.get("/api/alerts?status=resolved").json["total"] == 1


def test_background_detection_without_requests(app, client, payload):
    app.config["OFFLINE_TIMEOUT"] = 0.1
    client.post("/api/metrics", json=payload)
    stop, worker = start_monitor(app)
    try:
        deadline = time.monotonic()+3
        while time.monotonic() < deadline:
            with app.app_context():
                state = get_db().execute("SELECT status FROM virtual_machines").fetchone()[0]
            if state == "offline":
                break
            time.sleep(0.03)
        assert state == "offline"
    finally:
        stop.set()
        worker.join(timeout=2)
    assert not worker.is_alive()


def test_server_receipt_time_ignores_agent_clock(app, client, payload):
    client.post("/api/metrics", json={**payload, "timestamp": "2099-01-01T00:00:00Z"})
    with app.app_context():
        with get_db():
            get_db().execute("UPDATE virtual_machines SET last_seen=?", (time.time()-31,))
    assert client.get("/api/vms").json[0]["status"] == "offline"


def test_alert_filters_and_pagination(client, payload):
    client.post("/api/metrics", json={**payload, "cpu_usage": 99})
    client.post("/api/metrics", json={**payload, "hostname": "vm-02", "memory_usage": 99})
    assert client.get("/api/alerts?hostname=vm-01&severity=warning&status=active").json["total"] == 1
    assert client.get("/api/alerts?severity=critical").json["items"][0]["hostname"] == "vm-02"
    first = client.get("/api/alerts?limit=1").json
    second = client.get("/api/alerts?limit=1&offset=1").json
    assert first["total"] == 2
    assert first["items"][0]["id"] != second["items"][0]["id"]
    for query in ("severity=bad", "status=bad", "limit=0", "limit=x", "offset=-1"):
        assert client.get("/api/alerts?" + query).status_code == 400


def test_configurable_threshold(app, client, payload):
    app.config["CPU_THRESHOLD"] = 35
    client.post("/api/metrics", json=payload)
    assert client.get("/api/alerts").json["items"][0]["threshold"] == 35
