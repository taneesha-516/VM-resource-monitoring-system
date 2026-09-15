# Viva notes

## 30-second project explanation

This system monitors several Ubuntu virtual machines from one web dashboard. Each VM runs a Python agent using psutil. Every five seconds the agent posts metrics to Flask. SQLite stores the readings. The server detects high resource usage and missing heartbeats, and the browser displays current values, history graphs and alerts.

## Questions and answers

### 1. What is virtualization?

Virtualization lets one physical computer run several isolated computing environments by sharing its hardware through software.

### 2. What is a virtual machine?

A VM is a software-defined computer with virtual CPU, memory, storage and network devices. It runs its own guest operating system.

### 3. What is a hypervisor?

A hypervisor creates and manages virtual machines and coordinates their use of physical hardware. Type 1 runs directly on hardware; type 2 runs with a host operating system.

### 4. What is VirtualBox?

VirtualBox is a hosted virtualization tool used here to run Ubuntu guests on a laptop. It supplies virtual hardware and networking.

### 5. What is the difference between host OS and guest OS?

The host OS runs on the physical laptop. The guest OS runs inside a VM. For example, Windows can be the host and Ubuntu the guest.

### 6. How does this project use virtualization?

Several Ubuntu guests share one laptop. Each guest sends its own measurements to a central Flask server. The demo generator can imitate that data flow but does not perform virtualization.

### 7. What is psutil?

psutil is a Python library that reads OS resource statistics, such as CPU activity, memory usage, filesystem capacity, network counters and boot time.

### 8. What is a REST API?

A REST-style API exposes resources through HTTP endpoints. In this project agents POST metrics and the dashboard GETs VM information, history and alerts as JSON.

### 9. Why Flask?

Flask makes small Python web applications easy to read. Blueprints separate API routes from page routes, and the built-in development server is enough for the local demonstration.

### 10. Why SQLite?

SQLite stores relational data in a local file without a separate database server. It supports SQL, transactions, indexes and foreign keys, which suit a small student project.

### 11. How does the monitoring agent communicate with the server?

The agent collects a dictionary, converts it to JSON using requests, and sends an HTTP POST to /api/metrics. A timeout prevents indefinite waiting.

### 12. How is offline status detected?

The server stores the time it last accepted a sample. More than 30 seconds without another sample means offline. A background thread checks at most every five seconds, and API requests also check.

### 13. How are alerts generated?

A rule compares a sample with configured thresholds. One active row exists per VM and alert type. High samples update it; recovery resolves it; a new high episode creates another row.

### 14. What are CPU, RAM, disk and network metrics?

CPU percentage measures processor activity over a sampling interval. RAM percentage measures memory utilization. Disk percentage describes the selected filesystem's used capacity. Network metrics count bytes sent and received.

### 15. What is polling?

Polling repeatedly requests information at an interval. The browser fetches updated JSON about every five seconds. The agents independently push samples at their configured interval.

### 16. What are the limitations?

The system cannot identify the cause of missing data, does not buffer failed samples, has no authentication or notifications, monitors one filesystem, and has no automatic history cleanup. It is intended for a small trusted lab.

### 17. How could this scale for a company?

Add agent authentication and HTTPS, a production web server, a dedicated monitoring worker, PostgreSQL or a time-series database, retention and aggregation, and efficient batched queries. Benchmark before selecting capacity targets.

### 18. How does VM monitoring differ from container monitoring?

A VM runs a guest kernel, while containers typically share the host kernel. This agent reads guest-wide metrics. Containers require awareness of cgroup limits and container identity to interpret resource usage correctly.

### 19. How do virtualization and cloud computing differ?

Virtualization is a technique for sharing hardware through virtual environments. Cloud computing delivers computing resources as a service, often using virtualization plus networking, automation, billing and managed services.

### 20. What is the future scope?

Email/Telegram notifications, cloud and container monitoring, Prometheus/Grafana integration, anomaly detection and carefully controlled scaling are future possibilities. They are not part of this implementation.

### 21. Why not use the agent timestamp for offline status?

Guest clocks can be wrong. The server's own receipt time is a reliable reference for whether it recently heard from an agent. The agent timestamp is retained separately.

### 22. Is an offline VM necessarily powered off?

No. A stopped agent, broken network or failed server communication can also produce an offline status.

### 23. How is network speed calculated?

Rate = (new counter − old counter) / (new receipt time − old receipt time). A counter decrease or reboot produces a gap instead of a negative rate.

### 24. How do you prevent SQL injection?

Untrusted values are passed as SQL parameters rather than joined into SQL strings. The dynamic metric column names are fixed application constants.

### 25. What is a foreign key?

A foreign key links a child row to its parent. metrics.vm_id and alerts.vm_id reference virtual_machines.id, preventing orphan records when enforcement is enabled.

### 26. What happens at exactly the threshold?

The comparison is strictly greater than. CPU at exactly 85% does not trigger the default CPU alert; a previously active CPU alert resolves at 85% or below.

### 27. What happens when the server is unavailable?

The agent logs the failed request and tries with a fresh sample at the next interval. It stays running, but undelivered samples are lost.

### 28. How are VMs identified?

The hostname is a unique database key. Cloned VMs must have unique hostnames or agent overrides. Changing a hostname registers a new VM.

### 29. Why does a disk alert stay active after the VM goes offline?

No healthy disk sample has arrived to prove recovery. Offline detection does not invent a new resource reading.

### 30. What is the difference between a counter and a gauge?

A gauge is a current measurement such as RAM percentage. A counter accumulates events such as bytes sent. Differences between counters can be converted into rates.

### 31. Why use transactions?

A transaction groups related database changes. VM registration, metric insertion and resource-alert updates either commit together or roll back together.

### 32. How did you test it?

pytest uses temporary databases to exercise valid/invalid API inputs, storage, history windows, alerts, offline detection and recovery. Browser checks verify cards, charts, filters, refresh and responsive layout. Additional Node checks test network-rate edge cases.
