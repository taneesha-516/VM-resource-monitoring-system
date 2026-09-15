# Project report notes

## Abstract

The Virtual Machine Resource Monitoring and Alert System provides a centralized view of a small Ubuntu VM lab. A Python agent in each guest gathers CPU, RAM, disk, network and uptime measurements using psutil and sends them to a Flask REST endpoint every five seconds. SQLite stores accepted samples and alert episodes. A Bootstrap dashboard displays availability and current readings, while Chart.js presents recent resource and network trends. Configurable rules detect high usage and missing heartbeats. Repeated high samples update a single active alert, and recovery is recorded without deleting previous episodes. A separate three-VM simulator supports demonstrations before a VirtualBox lab is available. The implementation emphasizes understandable modules, input validation and repeatable tests.

## Introduction

Virtual machines let students create several isolated Linux systems on one laptop. As the number of guests increases, manually checking each guest becomes repetitive. A centralized dashboard makes it easier to compare their latest resource readings and notice when measurements stop arriving. This project implements the collection-to-display path directly, allowing students to explain the operating-system measurements, HTTP requests, SQL storage and browser refresh behavior.

## Problem statement

A student running several VMs needs to know which ones are reporting, whether resources exceed acceptable limits, and how measurements changed recently. Individual terminal commands provide only local snapshots. They do not automatically combine multiple guests into a common view or retain alert history.

The project therefore needs a lightweight collector per VM and a central server that validates, stores and interprets samples.

## Objectives

1. Collect resource statistics from each guest without controlling the VM.
2. Send samples through a simple HTTP/JSON interface.
3. Register VMs automatically and maintain latest receipt times.
4. Store samples and inspect 10-, 30- and 60-minute histories.
5. Generate resource and offline alerts with duplicate prevention.
6. Present the results in a responsive web interface.
7. Verify behavior with automated tests and a reproducible simulator.

## Existing approach

The baseline in a small lab is to open each VM and run commands or a local system monitor. This is useful for inspecting one guest but requires repeated manual work. A spreadsheet of observations also becomes outdated quickly. Larger monitoring platforms address this problem, but configuring them can hide the underlying implementation details from a beginning full-stack student.

## Proposed system

Each guest runs agent.py. The server accepts POST /api/metrics and identifies the sender by hostname. A transaction updates the VM record, inserts the metric and evaluates threshold rules. A separate thread identifies VMs whose accepted samples are older than the configured timeout. Browser pages request JSON periodically and update cards, charts and alert tables.

No endpoint executes guest commands, changes resources or powers VMs on or off.

## System architecture

```text
Guest OS metrics
     |
     v
psutil -> Python agent -> HTTP JSON -> Flask validation
                                           |
                                           v
                                    SQLite transaction
                                     /             \
                              metrics history   alert episodes
                                     \             /
                                      v           v
                                      REST read API
                                           |
                                           v
                                  Bootstrap + Chart.js UI

Background offline thread -> compares server time with last_seen
                          -> updates VM status and offline alert
```

The laptop hosts Flask and SQLite. Host-only networking is the recommended lab link; a second NAT adapter can provide package-download access.

## Modules

| Module | Responsibility |
| --- | --- |
| config.py | Reads server settings from environment variables |
| agent/agent.py | Collects metrics, discovers an interface address and handles HTTP failures |
| models/db.py | Creates schema, opens connections and enables foreign keys/WAL |
| models/vm.py | Registers or updates VM identity and receipt times |
| models/metric.py | Inserts samples and retrieves latest/history readings |
| models/alert.py | Maintains active and resolved alert episodes |
| services/validation.py | Validates JSON fields and numeric ranges |
| services/alerts.py | Evaluates CPU, RAM and disk thresholds |
| services/monitoring.py | Detects missing heartbeats in the background |
| routes/api.py | Exposes ingestion, VM, history, alert and summary endpoints |
| routes/views.py | Renders dashboard, detail, alert and about pages |
| static/js/ | Polls the API, updates the DOM and calculates network rates |
| demo_generator.py | Generates realistic sample sequences and reproducible alert/offline scenarios |

## Database design

### virtual_machines

id is the primary key; hostname is unique. ip_address stores the reported address. first_seen and last_seen are server UTC Unix timestamps. status is online or offline.

### metrics

Each row belongs to a VM through vm_id. The row contains cpu_usage, memory_usage, memory_used, memory_total, disk_usage, disk_used, disk_total, network_sent, network_received and uptime. timestamp is server receipt time; agent_timestamp stores an optional timezone-aware timestamp from the guest.

Used/total fields are nullable so the minimal API example remains supported. The supplied agent always includes them.

### alerts

Each row references vm_id and records alert_type, message, severity, value, threshold, timestamp, resolved and resolved_at. A partial unique index on (vm_id, alert_type) for unresolved rows prevents duplicate active episodes.

### Relationships and integrity

One VM has many metrics and many alerts. Foreign keys reject orphan rows. An index on (vm_id, timestamp) supports history retrieval. Parameterized SQL handles untrusted input. Transactions ensure that an accepted sample and its associated updates are committed together. SQLite WAL mode supports this small concurrent workload with a ten-second connection timeout.

## Implementation

### Agent collection

The agent reads percentages and byte counters from psutil. CPU measurement is primed before the first sample. The selected disk path is configurable and defaults to the Ubuntu root filesystem. The network address is selected using the route toward the server, with a fallback when address discovery fails.

The send loop uses a configurable timeout and catches connection errors. It adjusts the remaining sleep for work already performed. Failed samples are dropped, and the next cycle sends a fresh sample.

### Validation and persistence

The API requires JSON and rejects invalid objects, missing required values, invalid IP strings, nonfinite numbers, out-of-range percentages and invalid byte counters. Used bytes cannot exceed a reported total. The body-size limit is 16 KiB.

The server registers unknown hostnames automatically. It uses its own receipt timestamp rather than relying on guest clocks.

### Resource alerts

The default rules are CPU >85%, RAM >90% and disk >90%. CPU is warning severity; RAM and disk are critical. Repeated high readings update the active episode's value and message while retaining its original start time. A reading at or below the threshold resolves the episode.

### Offline detection

A VM becomes offline when now − last_seen >30 seconds. The background worker checks at most every five seconds, and API requests also refresh status. A new valid sample changes the VM to online and resolves its offline alert. Resource alerts remain active until a recovered reading arrives.

### Dashboard and history

The browser fetches fresh JSON approximately every five seconds, without a full page reload. Summary counts and VM cards show current state. Detail pages show resource percentages, byte totals, uptime, IP and last receipt time. Four charts display CPU, RAM, disk and network rates.

Network rate is counter difference divided by elapsed receipt time. Counter decreases and reboots produce gaps. The first sample cannot produce a rate.

### Alert browsing

Filters select hostname, severity and active/resolved status. The server returns a total count and a bounded page of alerts. The UI uses 25 rows per page.

## Testing

Automated Python tests use a temporary SQLite database per test. They cover:

- Successful ingestion, VM registration, multiple hosts and stored rows.
- Foreign-key enforcement and optional byte-total fields.
- Invalid JSON, MIME type, oversized requests, unknown VMs and numeric boundaries.
- History ordering and all three time windows.
- CPU/RAM/disk threshold episodes, deduplication and recovery.
- Exact offline boundary, reconnection and a future-dated agent clock.
- Background offline detection without browser/API traffic.
- Alert filters and pagination.
- Real local psutil collection and simulated network failure/recovery.

Additional JavaScript tests exercise network-rate calculations, counter resets, reboot detection and zero time differences.

## Results

The implementation passed 38 automated Python tests in the development environment. JavaScript syntax and network-rate tests also passed. A live Flask server received the three-VM simulator's samples. Browser checks confirmed populated cards, visible historical charts, filtering, responsive layout, automatic refresh, offline detection for a stopped simulated VM and recovery when samples resumed.

These results demonstrate the application workflow on a Windows host using simulated VM identities and real local psutil collection. They do not establish Ubuntu guest installation success or large-scale performance; a real VirtualBox lab must still be demonstrated using the documented setup.

See docs/VERIFICATION.md for the verification record.

## Advantages

- Small modules connect OS metrics, networking, storage and frontend concepts.
- Local SQLite and vendored frontend assets reduce demonstration dependencies.
- Automatic registration avoids manual database setup for each VM.
- Alert episodes preserve useful history without inserting a row every five seconds.
- A dedicated simulator makes failure and recovery repeatable.
- Read-only monitoring keeps the project scope focused.

## Limitations

- No authentication, HTTPS termination, rate limiting or user roles.
- No buffering or backfill when delivery fails.
- Missing samples do not identify whether the VM, agent or network failed.
- No history retention or downsampling; the database grows continuously.
- No sustained-duration threshold rule or hysteresis.
- Only one filesystem and aggregate network counters per agent.
- Graph spacing follows sample order; irregular network delivery affects interpretation.
- SQLite, N-per-VM latest queries and the development server suit a small lab.
- The in-process worker requires python app.py for background operation.
- No measured production throughput, availability guarantee or cloud deployment.

## Future scope

The next practical improvements are agent authentication with HTTPS, history retention/aggregation, and email or Telegram notifications. Further work could include cloud VM discovery, Docker/cgroup monitoring, Prometheus export, Grafana dashboards, anomaly detection and carefully authorized resource scaling. These would require additional design and testing and are not implemented here.

## Conclusion

The project provides a functional monitoring path from per-machine resource collection to a central historical dashboard. It handles registration, validation, storage, alert episodes and missing-heartbeat detection with a small Python and JavaScript stack. The implementation and tests make it suitable for explaining full-stack and virtualization concepts in a third-year CSE mini-project, while the documented limitations define where a production system would need further work.
