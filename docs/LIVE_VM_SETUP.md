# Monitor the Ubuntu VM on this desktop

## Connection and readings

- VirtualBox VM name / monitoring label: `taneesha_ubantu`.
- Guest Linux hostname: `taneeshaubantu` (the installer does not rename Ubuntu).
- Network: existing NAT adapter; no extra adapters or port forwarding needed.
- Ubuntu agent URL: `http://10.0.2.2:5000`.
- Windows dashboard: `http://127.0.0.1:5000`.
- Database: `database/ubuntu-vm.db`, separate from existing demo data.
- Samples: every 5 seconds; offline alert after 30 seconds without a sample.
- Alerts: CPU above 85%, RAM above 90%, disk above 90%, or missing heartbeats.
- Graphs: CPU, RAM, disk and network transfer rates; real readings from Ubuntu.

Oracle documents NAT access to the host loopback interface in its
[VirtualBox networking guide](https://docs.oracle.com/en/virtualization/virtualbox/7.2/user/networkingdetails.html).
The VM's NAT adapter must permit localhost access (enabled in this VM).

## Start the Windows server

From the project root in PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\scripts\Start-Monitoring.ps1
```

The launcher starts `server.py` with Waitress in a hidden background process,
checks `/api/health`, and opens the dashboard. Running it again reuses a running
project server. An unrelated process on port 5000 produces an error instead of
being stopped. `-NoBrowser` starts/checks the server without opening a browser.

Logs are in `runtime/server-output.log` and `runtime/server-error.log`.
`runtime/server.pid` records the launched process. To stop it, first verify the
PID belongs to this project's `server.py`, then stop that process. Start the
launcher again after Windows restarts; the Ubuntu service keeps retrying until
it can reach Windows. A desktop shortcut does not install a Windows boot service.

## Install or update the Ubuntu agent

First build the self-contained bundle on Windows:

```powershell
.\.venv\Scripts\python.exe scripts\build_ubuntu_bundle.py
```

The archive includes only the guest agent, configuration, requirements and
installer. It does not include databases, Windows environment files or Git data.
Keep the Windows server running. In Ubuntu's terminal:

```bash
mkdir -p ~/vm-monitor-setup
cd ~/vm-monitor-setup
curl --fail --connect-timeout 5 --max-time 30 -o ubuntu-agent.tar.gz \
  http://10.0.2.2:5000/static/downloads/ubuntu-agent.tar.gz
tar -xzf ubuntu-agent.tar.gz
sudo bash vm-agent/install.sh
```

The installer installs Ubuntu's `python3-psutil` and `python3-requests` packages
only if missing. It copies the agent to `/opt/vm-monitor`, creates a restricted
`vm-monitor` service account, and enables `vm-monitor-agent.service`. The agent
reads OS metrics and makes outbound HTTP requests; it accepts no commands from
the server. It runs without root privileges and has no write access to the
system or users' home directories. Re-running the installer updates this agent.

For another VM, build with `--hostname another-ubuntu`. For host-only or bridged
networking, also pass `--server-url http://HOST_IP:5000` and bind the server to
the intended host interface. The default Windows launcher intentionally uses
loopback for this desktop's NAT setup.

## Verify and manage Ubuntu monitoring

```bash
systemctl is-enabled vm-monitor-agent
systemctl is-active vm-monitor-agent
sudo journalctl -u vm-monitor-agent -n 20 --no-pager
sudo systemctl restart vm-monitor-agent
```

Open the dashboard and select `taneesha_ubantu` to see its graphs. For an offline
check, stop the agent with `sudo systemctl stop vm-monitor-agent`, wait over
30 seconds, and look for an offline alert. Restart it with
`sudo systemctl start vm-monitor-agent`; the next sample restores online status
and resolves that alert. Do not submit fabricated resource samples to the live
database. Automated threshold tests use temporary databases.

The Windows server must remain running to receive readings, refresh graphs and
detect offline VMs. A stopped service, a powered-off VM, a broken connection and
a sleeping host can all interrupt heartbeats; the alert reports missing samples,
not a definitive cause. Resource alerts are visible in the dashboard's Alerts
page; this project does not send email or phone notifications.

If the agent cannot connect, test `curl --fail http://10.0.2.2:5000/api/health`
inside Ubuntu and check the Windows server logs. If the service fails to start,
read its journal. If the VM is slow, close unused Windows applications rather
than running additional VM copies or demo generators alongside it.

## Checks

```powershell
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp runtime\tests-new-run
```

Use a fresh `--basetemp` path each time if old Windows test folders have restricted
permissions. The API tests cover all alert thresholds, deduplication, recovery,
offline detection and reconnection. Deployment tests verify the bundle's contents
and the launcher health endpoint. Guest service installation and live sample
delivery are verified separately against the actual Ubuntu VM.
