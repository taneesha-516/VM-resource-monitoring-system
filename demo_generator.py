"""Simulate three VMs; use --offline-after 20 to stop vm-03 after 20 seconds."""
import argparse
import math
import random
import time
from datetime import datetime, timezone

import requests

from agent.agent import send_metrics
from config import Config


def sample(index, elapsed, state, scenario, rng):
    phase = elapsed / 12 + index * 1.7
    cpu = max(2, min(99, 38 + index * 9 + 22 * math.sin(phase) + rng.uniform(-3, 3)))
    memory = max(0, min(100, 48 + index * 8 + 8 * math.sin(phase / 2)))
    disk = 35 + index * 12 + 0.2 * math.sin(phase)
    # Every minute has a high episode and a recovery episode.
    if scenario == "alerts" and elapsed % 60 < 30:
        if index == 0:
            cpu = 94
        elif index == 1:
            memory = 96
        else:
            disk = 95
    delta = max(0, elapsed - state["elapsed"])
    state["sent"] += int(delta * (45000 + index * 10000 + rng.random() * 10000))
    state["received"] += int(delta * (85000 + index * 12000 + rng.random() * 15000))
    state["elapsed"] = elapsed
    memory_total = (4 + index * 2) * 1024**3
    disk_total = 40 * 1024**3
    return {
        "hostname": f"vm-{index+1:02d}", "ip_address": f"192.168.56.{101+index}",
        "cpu_usage": round(cpu, 1), "memory_usage": round(memory, 1),
        "memory_used": int(memory_total * memory / 100), "memory_total": memory_total,
        "disk_usage": round(disk, 1), "disk_used": int(disk_total * disk / 100),
        "disk_total": disk_total, "network_sent": state["sent"],
        "network_received": state["received"], "uptime": 7200 + elapsed,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def positive(value):
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError("Must be positive and finite.")
    return number


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--server-url", default="http://127.0.0.1:5000")
    parser.add_argument("--interval", type=positive, default=Config.METRIC_INTERVAL)
    parser.add_argument("--scenario", choices=["normal", "alerts"], default="normal")
    parser.add_argument(
        "--offline-after", type=positive,
        help="Stop sending vm-03 after N seconds.",
    )
    parser.add_argument(
        "--duration", type=positive,
        help="Exit after N seconds; default runs until Ctrl+C.",
    )
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    config = {"server_url": args.server_url, "request_timeout": 4}
    rng = random.Random(args.seed)
    states = [{"sent": 1000000, "received": 2000000, "elapsed": 0} for _ in range(3)]
    started = time.monotonic()
    print("Demo running: vm-01, vm-02, vm-03. Press Ctrl+C to stop.", flush=True)
    try:
        with requests.Session() as session:
            while True:
                cycle = time.monotonic()
                elapsed = cycle - started
                if args.duration and elapsed >= args.duration:
                    return
                for index, state in enumerate(states):
                    if index == 2 and args.offline_after and elapsed >= args.offline_after:
                        continue
                    metrics = sample(index, elapsed, state, args.scenario, rng)
                    if send_metrics(session, config, metrics):
                        print(
                            f"{metrics['hostname']}: CPU {metrics['cpu_usage']}%, "
                            f"RAM {metrics['memory_usage']}%, "
                            f"disk {metrics['disk_usage']}%", flush=True,
                        )
                time.sleep(max(0, args.interval - (time.monotonic() - cycle)))
    except KeyboardInterrupt:
        print("\nDemo stopped.")


if __name__ == "__main__":
    main()
