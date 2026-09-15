"""Regression tests for ingestion, persistence, history and validation."""
import sqlite3

import pytest

from models.db import get_db


def test_registration_and_database_insertion(app, client, payload):
    assert client.post("/api/metrics", json=payload).status_code == 201
    assert client.post("/api/metrics", json={**payload, "cpu_usage": 52}).status_code == 201
    vms = client.get("/api/vms").json
    assert len(vms) == 1
    assert vms[0]["metrics"]["cpu_usage"] == 52
    assert vms[0]["status"] == "online"
    with app.app_context():
        assert get_db().execute("SELECT COUNT(*) FROM metrics").fetchone()[0] == 2
        assert get_db().execute("PRAGMA foreign_keys").fetchone()[0] == 1
        with pytest.raises(sqlite3.IntegrityError):
            get_db().execute("INSERT INTO alerts(vm_id,alert_type,message,severity,value,threshold,timestamp) VALUES(999,'cpu','test','warning',99,85,0)")


def test_minimal_sample_and_multiple_vms(client, payload):
    for field in ("memory_used", "memory_total", "disk_used", "disk_total", "timestamp"):
        payload.pop(field)
    for hostname in ("vm-01", "vm-02", "vm-03"):
        assert client.post("/api/metrics", json={**payload, "hostname": hostname}).status_code == 201
    assert client.get("/api/dashboard").json["total_vms"] == 3
    assert client.get("/api/vms/vm-01").json["metrics"]["memory_total"] is None


@pytest.mark.parametrize("field,value", [
    ("cpu_usage", -1), ("cpu_usage", 101), ("cpu_usage", True),
    ("memory_usage", "50"), ("disk_usage", None), ("cpu_usage", float("nan")),
    ("uptime", float("inf")), ("network_sent", -1), ("network_sent", 1.5),
    ("network_sent", 10**400), ("hostname", "<script>"), ("hostname", ""),
    ("ip_address", "not-an-ip"), ("ip_address", 123),
    ("timestamp", "yesterday"), ("timestamp", "2026-09-15T10:00:00"),
    ("memory_used", 1001), ("disk_total", -1),
])
def test_rejects_invalid_values(client, payload, field, value):
    response = client.post("/api/metrics", json={**payload, field: value})
    assert response.status_code == 400
    assert "error" in response.json
    assert client.get("/api/vms").json == []


@pytest.mark.parametrize("body", [[], None, 1, "hello", {}])
def test_requires_object_and_fields(client, body):
    assert client.post("/api/metrics", json=body, content_type="application/json").status_code == 400


def test_http_errors(client):
    assert client.post("/api/metrics", data="text").status_code == 415
    assert client.post("/api/metrics", data="{", content_type="application/json").status_code == 400
    assert client.post("/api/metrics", data="x" * 17000, content_type="application/json").status_code == 413
    assert client.get("/api/vms/missing").status_code == 404
    assert client.get("/api/vms/missing/history").status_code == 404
    assert client.delete("/api/vms/vm-01").status_code == 405


def test_history_window_and_order(app, client, payload):
    for cpu in (10, 20, 30):
        client.post("/api/metrics", json={**payload, "cpu_usage": cpu})
    with app.app_context():
        with get_db():
            get_db().execute("UPDATE metrics SET timestamp=timestamp-1200 WHERE id=1")
            get_db().execute("UPDATE metrics SET timestamp=timestamp-2400 WHERE id=2")
    assert [m["cpu_usage"] for m in client.get("/api/vms/vm-01/history?minutes=10").json] == [30]
    assert [m["cpu_usage"] for m in client.get("/api/vms/vm-01/history?minutes=30").json] == [10, 30]
    assert [m["cpu_usage"] for m in client.get("/api/vms/vm-01/history?minutes=60").json] == [20, 10, 30]
    for value in ("abc", "0", "100"):
        assert client.get("/api/vms/vm-01/history?minutes=" + value).status_code == 400


def test_templates_and_assets(client, payload):
    client.post("/api/metrics", json=payload)
    for path in ("/", "/vms", "/vms/vm-01", "/alerts", "/about",
                 "/static/vendor/bootstrap.min.css", "/static/vendor/chart.umd.js",
                 "/static/js/common.js", "/static/js/dashboard.js",
                 "/static/js/vm_detail.js", "/static/js/alerts.js"):
        assert client.get(path).status_code == 200, path
