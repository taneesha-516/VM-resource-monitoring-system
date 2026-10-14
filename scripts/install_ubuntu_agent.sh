#!/usr/bin/env bash
# Install only this project's read-only metrics agent; run using sudo.
set -euo pipefail
if [ "$(id -u)" -ne 0 ]; then
    echo "Run: sudo bash install.sh" >&2
    exit 1
fi
source_dir="$(cd -- "$(dirname -- "$0")" && pwd)"
if ! /usr/bin/python3 -c 'import psutil, requests' >/dev/null 2>&1; then
    apt-get update
    DEBIAN_FRONTEND=noninteractive apt-get install -y python3-psutil python3-requests
fi
/usr/bin/python3 -c 'import psutil, requests; print("Dependencies:", psutil.__version__, requests.__version__)'
if ! getent passwd vm-monitor >/dev/null; then
    useradd --system --no-create-home --shell /usr/sbin/nologin vm-monitor
fi
install -d -m 755 /opt/vm-monitor
install -m 644 "$source_dir/agent.py" /opt/vm-monitor/agent.py
install -m 644 "$source_dir/agent_config.json" /opt/vm-monitor/agent_config.json
# A failing connectivity probe must not discard the persistent service setup.
probe_status=0
runuser -u vm-monitor -- /usr/bin/python3 /opt/vm-monitor/agent.py --once || probe_status=$?
cat > /etc/systemd/system/vm-monitor-agent.service <<'UNIT'
[Unit]
Description=VM Resource Monitor metrics agent
Wants=network-online.target
After=network-online.target

[Service]
Type=simple
User=vm-monitor
WorkingDirectory=/opt/vm-monitor
ExecStart=/usr/bin/python3 -u /opt/vm-monitor/agent.py --config /opt/vm-monitor/agent_config.json
Restart=always
RestartSec=5
TimeoutStopSec=10
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX

[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload
systemctl enable vm-monitor-agent.service
systemctl restart vm-monitor-agent.service
systemctl --no-pager --full status vm-monitor-agent.service
if [ "$probe_status" -ne 0 ]; then
    echo "The initial sample failed. The service will retry; check the Windows server and agent_config.json." >&2
fi
echo "Agent installed. Logs: journalctl -u vm-monitor-agent -n 20 --no-pager"
