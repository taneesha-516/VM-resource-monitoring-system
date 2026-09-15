"""Validate untrusted agent input before opening a database transaction."""
import ipaddress
import math
import re
from datetime import datetime

from models.metric import FIELDS


def validate_metrics(data):
    if not isinstance(data, dict):
        raise ValueError("Request body must be a JSON object.")
    hostname = data.get("hostname")
    if not isinstance(hostname, str) or not re.fullmatch(
        r"[A-Za-z0-9](?:[A-Za-z0-9_.-]{0,251}[A-Za-z0-9])?", hostname
    ):
        raise ValueError(
            "hostname must contain 1-253 letters, digits, dots, underscores "
            "or hyphens, starting and ending with a letter or digit."
        )
    if not isinstance(data.get("ip_address"), str):
        raise ValueError("ip_address must be a string.")
    try:
        ipaddress.ip_address(data.get("ip_address", ""))
    except (ValueError, TypeError):
        raise ValueError("ip_address must be a valid IPv4 or IPv6 address.") from None
    clean = {"hostname": hostname, "ip_address": data["ip_address"]}
    optional = {"memory_used", "memory_total", "disk_used", "disk_total"}
    percentages = {"cpu_usage", "memory_usage", "disk_usage"}
    for field in FIELDS:
        value = data.get(field)
        if value is None and field in optional:
            clean[field] = None
            continue
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{field} must be a number.")
        if value < 0 or value > 2**63 - 1 or not math.isfinite(value):
            raise ValueError(f"{field} must be finite, nonnegative and fit in SQLite.")
        if field in percentages and value > 100:
            raise ValueError(f"{field} must be between 0 and 100.")
        if field not in percentages | {"uptime"} and not isinstance(value, int):
            raise ValueError(f"{field} must be an integer byte count.")
        clean[field] = value
    for prefix in ("memory", "disk"):
        used, total = clean[f"{prefix}_used"], clean[f"{prefix}_total"]
        if used is not None and total is not None and used > total:
            raise ValueError(f"{prefix}_used cannot exceed {prefix}_total.")
    if "timestamp" in data:
        timestamp = data["timestamp"]
        if not isinstance(timestamp, str) or len(timestamp) > 64:
            raise ValueError("timestamp must be an ISO 8601 string with timezone.")
        try:
            parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                raise ValueError()
        except ValueError:
            raise ValueError("timestamp must be an ISO 8601 string with timezone.") from None
        clean["timestamp"] = timestamp
    return clean
