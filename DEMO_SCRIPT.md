# Five-minute demonstration script

## Before the presentation

1. Open two terminals in the project folder and activate the virtual environment.
2. Start `python app.py` in the first terminal.
3. Start `python demo_generator.py --scenario alerts --offline-after 20` in the second.
4. Open [the dashboard](http://127.0.0.1:5000).
5. For an empty history, choose a new DATABASE filename before starting the server. Do not run two generators for the same names.

## 0:00 — Explain the problem and architecture

> Administrators should not need to open every VM to check its health. My project collects CPU, memory, disk and network metrics in one dashboard. Each Ubuntu VM runs a Python agent. The agent sends JSON through HTTP to Flask, which stores it in SQLite.

Point to the architecture diagram in the README. State that this run uses the separate simulator; it does not create actual virtual machines.

## 0:30 — Show the dashboard

> These cards represent three monitored machines. Each card shows the latest sample. The green badge means the server recently received metrics. The page updates approximately every five seconds without reloading.

Show total/online/offline/active-alert counts and CPU/RAM/disk bars. Explain that disk is the selected filesystem and uptime is time since boot.

## 1:00 — Show resource alerts

Open Alerts and select Resolved if the first high episode has already recovered.

> CPU above 85 percent is a warning. RAM or disk above 90 percent is critical. Repeated high samples update the same active alert. A healthy sample resolves that episode.

Filter by vm-01 and Warning to show the CPU episode. Then clear filters and show RAM/disk alerts.

## 1:45 — Show history

Open vm-01. Show the four charts and select Last 30 minutes.

> The database keeps each accepted sample. Network counters are cumulative, so the graph subtracts consecutive counters and divides by elapsed seconds to obtain bytes per second.

Point out that a small demonstration only has a few minutes of data even when a longer window is selected.

## 2:30 — Show missing heartbeat

Return to the dashboard. vm-03 should be red while vm-01 and vm-02 remain green.

> The simulator deliberately stopped vm-03's samples after 20 seconds. The server marks it offline more than 30 seconds after its last sample. This proves missing-heartbeat detection, not necessarily that a real VM is powered off.

Open Alerts and select vm-03, Critical, Active. Explain why the old disk alert also remains active: no healthy sample arrived to resolve it.

## 3:30 — Show recovery

Stop the simulator with Ctrl+C and run:

```bash
python demo_generator.py
```

> New metrics make the VMs online again. Normal readings resolve the old resource alerts, and all old episodes remain in the history.

Wait for the next browser refresh.

## 4:15 — Show the implementation and tests

Open `agent/agent.py`, `routes/api.py`, `services/alerts.py` and `services/monitoring.py`.

Run `python -m pytest -q` in another activated terminal.

> The tests cover input validation, persistence, thresholds, duplicate prevention, offline detection and recovery. The project is intentionally small and read-only.

## Real VirtualBox variation

Use Ubuntu agent names such as ubuntu-01 and ubuntu-02, with the host-only IP in each configuration. Stop one agent using Ctrl+C, wait 30–40 seconds, then restart it. Do not mix simulator names with real-agent names. No artificial CPU or disk stress is needed to demonstrate the alert logic.

## Likely follow-up questions

- Why is the agent inside the VM?
- Why are server receipt times used?
- What happens if the server is unavailable?
- How are duplicate alerts prevented?
- Why is network traffic computed from counter differences?
- How does host-only networking differ from bridged networking?
- What would you change for a company with 1,000 VMs?

Answers are in VIVA_NOTES.md.
