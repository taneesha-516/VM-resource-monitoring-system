from unittest.mock import Mock

import requests

from agent.agent import collect_metrics, send_metrics
from services.validation import validate_metrics


def test_collect_real_metrics(tmp_path):
    metrics = collect_metrics({
        "server_url": "http://127.0.0.1:5000",
        "disk_path": str(tmp_path), "hostname": "test-agent", "ip_address": "127.0.0.1",
    })
    validate_metrics(metrics)
    assert metrics["memory_total"] > 0
    assert metrics["disk_total"] > 0


def test_network_failure_and_recovery():
    session = Mock()
    session.post.side_effect = [requests.ConnectionError("offline"), Mock()]
    config = {"server_url": "http://127.0.0.1:5000", "request_timeout": 1}
    assert send_metrics(session, config, {"hostname": "test"}) is False
    assert send_metrics(session, config, {"hostname": "test"}) is True
    assert session.post.call_count == 2
