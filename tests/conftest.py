import pytest

from app import create_app


@pytest.fixture
def app(tmp_path):
    return create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.db")})


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def payload():
    return dict(
        hostname="vm-01", ip_address="192.168.56.101", cpu_usage=40,
        memory_usage=60, memory_used=600, memory_total=1000,
        disk_usage=30, disk_used=300, disk_total=1000,
        network_sent=1000, network_received=2000, uptime=120,
        timestamp="2026-09-15T10:00:00+00:00",
    )
