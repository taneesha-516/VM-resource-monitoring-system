"""Threshold evaluation, called in the same transaction as metric insertion."""
from flask import current_app

from models.alert import resolve_alert, set_alert


def evaluate_resources(vm, metrics, now):
    rules = (
        ('cpu_usage', 'cpu', 'CPU_THRESHOLD', 'CPU', 'warning'),
        ('memory_usage', 'memory', 'MEMORY_THRESHOLD', 'RAM', 'critical'),
        ('disk_usage', 'disk', 'DISK_THRESHOLD', 'Disk', 'critical'),
    )
    for field, kind, setting, label, severity in rules:
        value = metrics[field]
        threshold = current_app.config[setting]
        if value > threshold:
            message = (
                f"{vm['hostname']} {label} usage exceeded {threshold:g}%. "
                f"Current value: {value:g}%."
            )
            set_alert(vm, kind, value, threshold, severity, now, message)
        else:
            resolve_alert(vm['id'], kind, now)
