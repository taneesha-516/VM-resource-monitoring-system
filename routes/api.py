"""Small JSON API used by agents and the dashboard."""
import time

from flask import Blueprint, abort, current_app, jsonify, request

from models.db import get_db
from models.metric import insert_metric, latest_metric, metric_history
from models.vm import find_vm, register_vm
from services.validation import validate_metrics
from services.alerts import evaluate_resources
from services.monitoring import sweep_offline
from models.alert import resolve_alert

api = Blueprint("api", __name__, url_prefix="/api")


@api.before_request
def refresh_status():
    sweep_offline()


def vm_data(row):
    return {**dict(row), "metrics": latest_metric(row["id"])}


@api.post("/metrics")
def receive_metrics():
    if not request.is_json:
        abort(415, description="Content-Type must be application/json.")
    try:
        data = validate_metrics(request.get_json())
    except ValueError as error:
        abort(400, description=str(error))
    now = time.time()
    with get_db():
        vm = register_vm(data["hostname"], data["ip_address"], now)
        insert_metric(vm["id"], data, now)
        evaluate_resources(vm, data, now)
        resolve_alert(vm["id"], "offline", now)
    return jsonify(message="Metrics accepted", hostname=vm["hostname"]), 201


@api.get("/vms")
def list_vms():
    rows = get_db().execute("SELECT * FROM virtual_machines ORDER BY hostname")
    return jsonify([vm_data(row) for row in rows])


@api.get("/vms/<hostname>")
def vm_detail(hostname):
    vm = find_vm(hostname)
    if vm is None:
        abort(404, description="VM not found.")
    return jsonify(vm_data(vm))


@api.get("/vms/<hostname>/history")
def history(hostname):
    vm = find_vm(hostname)
    if vm is None:
        abort(404, description="VM not found.")
    try:
        minutes = int(request.args.get("minutes", "10"))
    except ValueError:
        abort(400, description="minutes must be 10, 30 or 60.")
    if minutes not in (10, 30, 60):
        abort(400, description="minutes must be 10, 30 or 60.")
    return jsonify(metric_history(vm["id"], time.time() - minutes * 60))


@api.get("/alerts")
def alerts():
    clauses, values = [], []
    hostname = request.args.get("hostname")
    if hostname:
        clauses.append("v.hostname=?")
        values.append(hostname)
    severity = request.args.get("severity")
    if severity:
        if severity not in ("warning", "critical"):
            abort(400, description="severity must be warning or critical.")
        clauses.append("a.severity=?")
        values.append(severity)
    status = request.args.get("status")
    if status:
        if status not in ("active", "resolved"):
            abort(400, description="status must be active or resolved.")
        clauses.append("a.resolved=?")
        values.append(int(status == "resolved"))
    try:
        limit = int(request.args.get("limit", 100))
        offset = int(request.args.get("offset", 0))
    except ValueError:
        abort(400, description="limit and offset must be integers.")
    if not 1 <= limit <= 500 or offset < 0:
        abort(400, description="limit must be 1–500 and offset must be nonnegative.")
    where = " WHERE " + " AND ".join(clauses) if clauses else ""
    query = " FROM alerts a JOIN virtual_machines v ON v.id=a.vm_id" + where
    total = get_db().execute("SELECT COUNT(*)" + query, values).fetchone()[0]
    rows = get_db().execute(
        "SELECT a.*, v.hostname" + query +
        " ORDER BY a.timestamp DESC, a.id DESC LIMIT ? OFFSET ?",
        (*values, limit, offset),
    )
    return jsonify(items=[dict(row) for row in rows], total=total)


@api.get("/dashboard")
def dashboard():
    connection = get_db()
    total = connection.execute("SELECT COUNT(*) FROM virtual_machines").fetchone()[0]
    online = connection.execute(
        "SELECT COUNT(*) FROM virtual_machines WHERE status='online'"
    ).fetchone()[0]
    active = connection.execute("SELECT COUNT(*) FROM alerts WHERE resolved=0").fetchone()[0]
    return jsonify(
        total_vms=total, online_vms=online, offline_vms=total-online,
        active_alerts=active, server_time=time.time(),
        thresholds={
            "cpu_usage": current_app.config["CPU_THRESHOLD"],
            "memory_usage": current_app.config["MEMORY_THRESHOLD"],
            "disk_usage": current_app.config["DISK_THRESHOLD"],
        },
        refresh_seconds=current_app.config["METRIC_INTERVAL"],
    )
