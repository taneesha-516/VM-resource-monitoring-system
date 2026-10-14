"""Build a small Ubuntu deployment archive without databases or host files."""
import argparse
import io
import json
from pathlib import Path
import tarfile

ROOT = Path(__file__).resolve().parents[1]


def build_bundle(output, server_url="http://10.0.2.2:5000", hostname="taneesha_ubantu"):
    config = json.loads((ROOT / "agent/agent_config.json").read_text(encoding="utf-8"))
    config.update(server_url=server_url, hostname=hostname)
    files = {
        "agent.py": (ROOT / "agent/agent.py").read_bytes(),
        "requirements.txt": (ROOT / "agent/requirements.txt").read_bytes(),
        "agent_config.json": (json.dumps(config, indent=2) + "\n").encode(),
        "install.sh": (ROOT / "scripts/install_ubuntu_agent.sh").read_bytes(),
    }
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(output, "w:gz") as archive:
        for name, contents in files.items():
            # Linux scripts must work even when the Windows checkout uses CRLF.
            contents = contents.replace(b"\r\n", b"\n")
            entry = tarfile.TarInfo("vm-agent/" + name)
            entry.size = len(contents)
            entry.mode = 0o755 if name == "install.sh" else 0o644
            archive.addfile(entry, io.BytesIO(contents))
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--server-url", default="http://10.0.2.2:5000")
    parser.add_argument("--hostname", default="taneesha_ubantu")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "static/downloads/ubuntu-agent.tar.gz")
    args = parser.parse_args()
    print(build_bundle(args.output, args.server_url, args.hostname))


if __name__ == "__main__":
    main()
