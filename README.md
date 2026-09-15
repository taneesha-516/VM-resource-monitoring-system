# Virtual Machine Resource Monitoring and Alert System

A 3rd-year CSE mini-project for monitoring several Ubuntu virtual machines from one laptop. Python agents push samples to Flask; SQLite stores the history; a Bootstrap dashboard shows current readings, Chart.js graphs, and alerts.

## Problem statement

Checking CPU, memory and disk usage separately inside every VM becomes inconvenient as a lab grows. A VM can also stop sending data without anyone noticing. This project centralizes measurements and highlights resource pressure and missing heartbeats.

## Objectives

- Collect comparable metrics from multiple VMs every five seconds.
- Store readings so students can inspect recent trends.
- Detect threshold crossings and missing agents.
- Explain the complete data flow using a small, readable codebase.
- Demonstrate the dashboard before VMs are available using separate simulated data.

## Features

- Automatic VM registration by hostname, with IP and first/last receipt times.
- CPU percentage, RAM percentage/used/total, disk percentage/used/total.
- Cumulative network bytes sent/received and uptime.
- Online/offline badges and dashboard totals.
- CPU warning above 85%; RAM and disk critical above 90%.
- Offline critical alert after more than 30 seconds without accepted metrics.
- One active alert per VM and type; automatic resolution on recovery.
- VM detail pages with 10-minute, 30-minute and one-hour graphs.
- Network rate graphs in bytes/second, computed from consecutive counters.
- Alert filters by hostname, severity and active/resolved status, with pagination.
- Fetch-based refresh, responsive layout, and visible refresh failure messages.
- Locally bundled Bootstrap and Chart.js: no CDN needed at demonstration time.
- No remote commands, power controls, or resource modifications.

## Architecture

```text
Ubuntu VM 1: psutil agent --+
Ubuntu VM 2: psutil agent --+-- HTTP POST /api/metrics --> Flask server
Ubuntu VM 3: psutil agent --+                               |
                                                           +--> validation
                                                           +--> SQLite
                                                           +--> threshold rules
                                                           +--> offline sweep
                                                                  |
Browser: HTML + Bootstrap + Chart.js <-- JSON GET /api/... --------+
                    (poll approximately every 5 seconds)
```

The server normally runs on the laptop host. Agents run inside the guest VMs. The server does not need to connect into a VM: each agent initiates the HTTP request.

## Technologies used

| Technology | Role |
| --- | --- |
| VirtualBox | Runs the Ubuntu guests on the laptop |
| Ubuntu / Python 3 | Environment for each monitoring agent |
| psutil | Reads local OS resource counters |
| requests | Sends JSON metrics over HTTP |
| Flask | Serves HTML and REST endpoints |
| SQLite / Python sqlite3 | Stores VMs, samples and alert episodes |
| Bootstrap 5.3.3 | Responsive layout, forms, badges and progress bars |
| Chart.js 4.4.8 | Draws resource and network graphs |
| pytest | Tests API behavior, validation, persistence and monitoring rules |

## Requirements

- Python 3.10 or newer, with pip and virtual environments.
- Windows or Linux for the central server.
- VirtualBox and Ubuntu VMs for the real VM demonstration; optional for demo mode.
- Internet for initial Python dependency installation. Frontend libraries are included.
- Approximately 8 GB laptop RAM is a practical starting point for small Ubuntu Server VMs; reduce the number of VMs if the host is constrained.
- Node.js is optional and only needed for the additional JavaScript checks.

## Installation and backend setup

Open a terminal **inside this project folder**. All commands below assume that location unless a section says otherwise.

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

If PowerShell prevents activation, use the interpreter directly; no execution-policy change is needed:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

### Linux

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

Open [the dashboard](http://127.0.0.1:5000). SQLite tables are created automatically in `database/monitoring.db`. An empty dashboard is expected before an agent sends metrics.

Stop the server with Ctrl+C. Use `python app.py` so the independent offline-monitor thread starts. Importing `create_app()` alone creates the application but does not start that thread; API requests still refresh offline states.

### Configuration

Set environment variables **before** starting the server:

| Variable | Default | Meaning |
| --- | --- | --- |
| SERVER_HOST | 0.0.0.0 | Interface to bind; allows guest connections |
| SERVER_PORT | 5000 | HTTP port |
| METRIC_INTERVAL | 5 | Browser refresh interval and demo default, seconds |
| OFFLINE_TIMEOUT | 30 | Seconds since last accepted sample before offline |
| CPU_THRESHOLD | 85 | CPU warning boundary, percent |
| MEMORY_THRESHOLD | 90 | RAM critical boundary, percent |
| DISK_THRESHOLD | 90 | Disk critical boundary, percent |
| DATABASE | project/database/monitoring.db | SQLite file path |

Windows example:

```powershell
$env:SERVER_PORT = "5001"
$env:CPU_THRESHOLD = "80"
python app.py
```

Linux example:

```bash
SERVER_PORT=5001 CPU_THRESHOLD=80 python app.py
```

Update the agent/demo server URL when changing the port. The agent interval is independently configured in its JSON file; changing the server interval does not reconfigure remote agents. Keep OFFLINE_TIMEOUT comfortably larger than the agent interval and request timeout.

For a fresh demonstration without deleting existing records, stop the server and choose a new database filename:

```powershell
$env:DATABASE = "database/fresh-demo.db"
python app.py
```

Linux equivalent: `DATABASE=database/fresh-demo.db python app.py`.

## Demo mode

In a **second terminal**, activate the same environment, then run:

```bash
python demo_generator.py
```

Three simulated hosts (`vm-01`, `vm-02`, `vm-03`) appear. Wait at least 10 seconds for multiple graph points.

For a deterministic alert/offline demonstration:

```bash
python demo_generator.py --scenario alerts --offline-after 20
```

- During the first 30 seconds of each minute, vm-01 has high CPU, vm-02 high RAM and vm-03 high disk.
- During the next 30 seconds, sending VMs recover and their resource alerts resolve.
- After 20 seconds, vm-03 stops sending. Its last sample is typically near 15 seconds.
- It becomes offline about 30–35 seconds after that last sample. Browser refresh may add up to another five seconds.
- Its disk alert stays active because the server has no healthy sample proving recovery.
- Ctrl+C stops the generator. Run normal demo mode again to bring all three VMs online and resolve the resource/offline alerts.

Other options:

```bash
python demo_generator.py --server-url http://127.0.0.1:5001 --interval 5
python demo_generator.py --scenario alerts --duration 90 --seed 42
```

Run only one generator for these names at a time. Give real agents different names if using both simultaneously. Simulated IP addresses are labels; the demo does not create real VMs.

## Agent setup inside each Ubuntu VM

Copy the entire `agent/` folder into the VM, for example to `~/vm-agent`. It is self-contained and needs only its own requirements file.

```bash
cd ~/vm-agent
sudo apt update
sudo apt install python3 python3-venv python3-pip
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
nano agent_config.json
```

Example configuration:

```json
{
  "server_url": "http://192.168.56.1:5000",
  "metric_interval": 5,
  "request_timeout": 4,
  "hostname": "ubuntu-01",
  "ip_address": null,
  "disk_path": "/"
}
```

Use the **host laptop's reachable address**, not `127.0.0.1` and not the VM's own address. The example address must be checked against your actual host-only adapter.

- `hostname: null` uses the OS hostname. Give cloned VMs unique names or overrides such as ubuntu-01/02/03.
- `ip_address: null` selects the interface used to reach the server. An explicit IP override is available for unusual networking.
- `disk_path` selects one filesystem. On Ubuntu, `/` monitors the root filesystem, not every attached disk.
- Agent failures are logged; the next interval tries again. Failed samples are not queued or resent.
- The agent primes CPU measurement for one second before its first sample.

Start and test:

```bash
python agent.py --once
python agent.py
```

From the project root, the equivalent is `python agent/agent.py --config agent/agent_config.json`. Stop with Ctrl+C. The script reads only local metrics; it never accepts commands from the server.

## VirtualBox networking

### Recommended laptop lab: NAT + Host-only Adapter

1. Shut down the guest before changing its adapters.
2. In VirtualBox Manager, open the Network tool (in recent versions: File → Tools → Network Manager).
3. Create a host-only network. Enable its DHCP server. Inspect the host adapter address and subnet.
4. A common example is host `192.168.56.1/24` and DHCP guests `192.168.56.101` onward; your actual configuration may differ.
5. In each VM's Settings → Network, keep Adapter 1 as NAT for package downloads.
6. Enable Adapter 2 as Host-only Adapter and select the network you created. Ensure Cable Connected is checked.
7. Boot Ubuntu and inspect `ip -br address`. The second interface should obtain a host-only address; if it has no address, enable DHCP for that interface in Ubuntu network settings.
8. On Windows, inspect `ipconfig` for the VirtualBox host-only adapter. On Linux, inspect `ip -br address`.
9. Set the agent server URL to that host adapter address and the server port.
10. Run the server, then verify from Ubuntu:

```bash
curl http://192.168.56.1:5000/api/dashboard
```

Host-only networking connects the laptop and selected guests. NAT on the other adapter supplies guest internet access for package installation. This arrangement keeps the monitoring path independent of the physical Wi-Fi network.

### Bridged Adapter alternative

Choose Bridged Adapter and select the host's active network interface when VMs need to join the physical LAN. Obtain the host and guest LAN IPs and use the host LAN IP as the server URL. Network policies or Wi-Fi isolation can prevent guest communication, making host-only simpler for a portable college demo.

These networking modes and the Network Manager location are described in [Oracle's VirtualBox networking guide](https://docs.oracle.com/en/virtualization/virtualbox/7.2/user/networkingdetails.html).

### Firewall and connection troubleshooting

- Keep Flask bound to `0.0.0.0` or the reachable host-only address, not just loopback.
- If the host firewall blocks TCP 5000, create a narrowly scoped inbound rule for the host-only subnet/adapter. Keep the firewall enabled.
- Check the URL and port with `curl` from Ubuntu; ping alone does not prove the HTTP port is reachable.
- For refused connections, check the server process and port. For timeouts, check routing, Cable Connected and firewall rules.
- If only one card appears despite multiple VMs, check for duplicate hostnames.
- If graphs are empty, wait for two samples and select a window containing data.
- When running an agent on Windows for testing, set `disk_path` to an existing drive root.
- Restart the server after editing Python code or configuration; debug/reload mode is intentionally off.

## Data and alert semantics

- A VM is identified by its unique, case-sensitive hostname. A hostname change registers a different VM.
- Server UTC Unix seconds are stored for first_seen, last_seen and metric timestamp. Optional agent ISO 8601 timestamps are retained as `agent_timestamp`.
- Offline detection uses **server receipt time**, so a future agent clock cannot keep a VM online.
- A sample is accepted only after validation. Invalid samples do not refresh the heartbeat.
- Online means a valid sample was received within 30 seconds, including exactly 30. Offline means strictly more than 30 seconds.
- Background detection runs at most every five seconds. API requests also sweep before responding.
- Threshold comparisons are strict: 85% CPU does not trigger the default CPU alert; 85.1% does.
- Alert timestamp is the episode's start. While active, value and message track the latest high reading. Recovery sets resolved and resolved_at. Subsequent high usage creates a new episode.
- Resource alerts remain active while a VM is offline until a sample proves recovery.
- Network cards display cumulative OS counters. Graphs show average bytes/second between adjacent samples. Counter decreases or uptime decreases produce gaps; the first sample has no rate.
- CPU is measured between agent polls. RAM and disk are point-in-time OS measurements. RAM percentage may not equal used/total exactly because OS memory accounting handles reclaimable caches specially.
- Browser dates use the browser's local timezone.
- Each history response returns at most 10,000 recent samples in the selected window. Alert queries are paginated. Stored history is not automatically deleted.
- Graph points are spaced by sample order; labels show receipt times. With irregular delivery, interpret rates as interval averages rather than instantaneous speed.

## REST API

| Method / path | Response |
| --- | --- |
| POST /api/metrics | 201 with message and hostname |
| GET /api/vms | Array of VM records with latest `metrics` |
| GET /api/vms/<hostname> | One VM, or 404 |
| GET /api/vms/<hostname>/history?minutes=10 | Chronological metric array; minutes must be 10, 30 or 60 |
| GET /api/alerts | Object with `items` and `total` |
| GET /api/dashboard | Counts, thresholds, refresh interval and server time |

Alert query parameters: `hostname`, `severity=warning|critical`, `status=active|resolved`, `limit=1..500` (default 100), `offset>=0`. The UI uses pages of 25.

Example minimal input:

```json
{
  "hostname": "ubuntu-01",
  "ip_address": "192.168.56.101",
  "cpu_usage": 45.3,
  "memory_usage": 61.2,
  "disk_usage": 42.8,
  "network_sent": 1234567,
  "network_received": 3456789,
  "uptime": 5820
}
```

Optional fields: `memory_used`, `memory_total`, `disk_used`, `disk_total` (integer bytes), `timestamp` (timezone-aware ISO 8601 string). The supplied agent always sends them.

Percentages must be finite numbers between 0 and 100. Byte counts must be nonnegative integers within SQLite's signed 64-bit range; reported used bytes cannot exceed reported total bytes. Uptime is a nonnegative number. IP must be a valid address string. Hostnames contain 1–253 letters/digits/dots/underscores/hyphens and begin/end with a letter or digit.

Errors return JSON `{"error": "..."}` with 400 for invalid input, 404 for unknown VMs, 413 for bodies over 16 KiB, 415 for non-JSON ingestion, and 503 for database failures. SQL queries use parameters for untrusted values.

## Testing

With the virtual environment active:

```bash
python -m pytest -q
```

Tests use temporary SQLite databases and do not modify your monitoring database. Coverage includes ingestion, registration, multiple VMs, validation, foreign keys, history ranges, all threshold types, alert deduplication/recovery, offline/reconnection, background detection without requests, filters and agent failure handling.

Optional JavaScript checks (Node.js):

```bash
node --check static/js/common.js
node --check static/js/dashboard.js
node --check static/js/vm_detail.js
node --check static/js/alerts.js
node tests/test_network_rates.cjs
```

See [verification notes](docs/VERIFICATION.md) for the checks actually performed, including browser testing and remaining environment limitations.

## Security and limitations

This first version is intended for a trusted local lab. It has no user login, agent authentication, TLS termination, or rate limiting. Any client able to reach the server can submit metrics or view the dashboard. Keep it on the lab network; do not publish it directly to the internet.

The monitoring interface has no remote command execution or VM control. JSON validation, HTML escaping, size limits, parameterized SQL and transactions reduce common input failures.

Other limitations:

- A missing heartbeat cannot distinguish a powered-off VM from a stopped agent or broken network.
- Samples missed during a server outage are lost.
- Threshold noise near a boundary can create repeated episodes; no hysteresis or sustained-duration rule.
- SQLite and per-VM latest-value queries target a small lab, not thousands of machines.
- Database growth has no automatic retention policy: three VMs at five seconds create about 51,840 rows/day.
- One root filesystem per agent; no per-process or per-interface breakdown.
- The Flask development server and in-process monitor are for this local demonstration.
- Alerts are visible in the web UI only. No email or Telegram delivery.

## Demo presentation

See [DEMO_SCRIPT.md](DEMO_SCRIPT.md) for a short professor-facing script and a sequence that shows thresholds, history, offline detection, and recovery.

## Documentation and folder tree

- [Viva questions and answers](VIVA_NOTES.md)
- [Project report material](PROJECT_REPORT_NOTES.md)
- [Phase-by-phase development record](docs/DEVELOPMENT_LOG.md)
- [Complete source folder tree](docs/FOLDER_TREE.md)

## Future enhancements

Three useful next steps are authenticated agents with HTTPS, database retention/downsampling, and email/Telegram notifications.

Longer-term scope: cloud VM monitoring, Docker monitoring, Prometheus integration, Grafana integration, machine-learning anomaly detection, and automatic resource scaling. These are proposals only; none is implemented in this read-only first version.
