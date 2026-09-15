"""Collect this machine's metrics and push them to the central server."""
import argparse
import ipaddress
import json
import logging
import math
import socket
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import psutil
import requests

LOGGER = logging.getLogger("vm-agent")


def load_config(path):
    with open(path, encoding="utf-8-sig") as source:
        config = json.load(source)
    parsed = urlparse(config.get("server_url", ""))
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError("server_url must be an http or https URL.")
    for field, default in (("metric_interval", 5), ("request_timeout", 4)):
        value = config.get(field, default)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{field} must be a positive number.")
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"{field} must be a positive finite number.")
        config[field] = value
    if config.get("ip_address"):
        ipaddress.ip_address(config["ip_address"])
    return config


def get_ip_address(server_url):
    """Find the interface used to reach the server without sending a packet."""
    parsed = urlparse(server_url)
    try:
        addresses = socket.getaddrinfo(
            parsed.hostname, parsed.port or (443 if parsed.scheme == "https" else 80),
            type=socket.SOCK_DGRAM,
        )
        family, kind, protocol, _, address = addresses[0]
        with socket.socket(family, kind, protocol) as connection:
            connection.connect(address)
            return connection.getsockname()[0]
    except OSError:
        try:
            return socket.gethostbyname(socket.gethostname())
        except OSError:
            return "127.0.0.1"


def collect_metrics(config):
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage(config.get("disk_path", "/"))
    network = psutil.net_io_counters()
    return {
        "hostname": config.get("hostname") or socket.gethostname(),
        "ip_address": config.get("ip_address") or get_ip_address(config["server_url"]),
        "cpu_usage": psutil.cpu_percent(interval=None),
        "memory_usage": memory.percent,
        "memory_used": memory.used,
        "memory_total": memory.total,
        "disk_usage": disk.percent,
        "disk_used": disk.used,
        "disk_total": disk.total,
        "network_sent": network.bytes_sent,
        "network_received": network.bytes_recv,
        "uptime": max(0, time.time() - psutil.boot_time()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def send_metrics(session, config, metrics):
    try:
        response = session.post(
            config["server_url"].rstrip("/") + "/api/metrics",
            json=metrics, timeout=config["request_timeout"],
        )
        response.raise_for_status()
        LOGGER.info("Sent metrics for %s", metrics["hostname"])
        return True
    except requests.RequestException as error:
        LOGGER.warning("Metrics not delivered; retrying next interval: %s", error)
        return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=str(Path(__file__).with_name("agent_config.json")))
    parser.add_argument("--once", action="store_true", help="Send one sample and exit.")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        config = load_config(args.config)
    except (OSError, ValueError, TypeError) as error:
        parser.error(str(error))
    psutil.cpu_percent(interval=None)  # Prime the CPU measurement.
    time.sleep(1)
    try:
        with requests.Session() as session:
            while True:
                started = time.monotonic()
                try:
                    success = send_metrics(session, config, collect_metrics(config))
                except (OSError, ValueError, psutil.Error) as error:
                    LOGGER.warning("Cannot collect metrics: %s", error)
                    success = False
                if args.once:
                    return 0 if success else 1
                time.sleep(max(0, config["metric_interval"] - (time.monotonic() - started)))
    except KeyboardInterrupt:
        LOGGER.info("Agent stopped.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
