"""
Pytest fixtures for Netaform Phase 4 (cEOS) network validation.
"""

import subprocess
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "napalm"))

from inventory import DEVICES, HOSTS, EXPECTED_STATE
from napalm_helpers import get_device_connection


@pytest.fixture(scope="session")
def napalm_devices():
    """Open NAPALM connections to all cEOS devices for the test session."""
    connections = {}
    for name in DEVICES:
        try:
            connections[name] = get_device_connection(name)
        except Exception as e:
            pytest.fail(f"Cannot connect to {name}: {e}")
    yield connections
    for conn in connections.values():
        conn.close()


@pytest.fixture
def hosts():
    return HOSTS


@pytest.fixture
def expected():
    return EXPECTED_STATE


def docker_exec(container, command):
    result = subprocess.run(
        ["docker", "exec", container] + command.split(),
        capture_output=True,
        text=True,
        timeout=30,
    )
    return result


def ping_from_host(host_name, destination, count=3):
    container = HOSTS[host_name]["container"]
    result = docker_exec(container, f"ping -c {count} -W 2 {destination}")
    return result.returncode == 0
