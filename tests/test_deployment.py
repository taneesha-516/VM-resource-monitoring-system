import json
import tarfile

from agent.agent import load_config
from scripts.build_ubuntu_bundle import build_bundle


def test_bundle_contains_only_guest_files_and_uses_selected_vm(tmp_path):
    output = build_bundle(tmp_path / "guest.tar.gz", hostname="ubuntu-test")
    with tarfile.open(output) as archive:
        assert set(archive.getnames()) == {
            "vm-agent/agent.py", "vm-agent/requirements.txt",
            "vm-agent/agent_config.json", "vm-agent/install.sh",
        }
        config_bytes = archive.extractfile("vm-agent/agent_config.json").read()
        config = json.loads(config_bytes)
        assert config["server_url"] == "http://10.0.2.2:5000"
        assert config["hostname"] == "ubuntu-test"
        script = archive.extractfile("vm-agent/install.sh").read()
        assert b"\r" not in script
        assert archive.getmember("vm-agent/install.sh").mode == 0o755
    config_path = tmp_path / "agent_config.json"
    config_path.write_bytes(config_bytes)
    assert load_config(config_path)["metric_interval"] == 5


def test_launcher_health_identifies_monitor_and_detects_database_failure(client, app, tmp_path):
    assert client.get("/api/health").json == {
        "service": "vm-resource-monitor", "status": "ok",
    }
    app.config["DATABASE"] = str(tmp_path / "missing-parent" / "monitor.db")
    assert client.get("/api/health").status_code == 503
