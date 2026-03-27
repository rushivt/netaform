"""
Test Layer 4: End-to-End Reachability
"""

import subprocess
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from inventory import HOSTS, EXPECTED_STATE


def ping_from_container(container, destination, count=3):
    result = subprocess.run(
        ["docker", "exec", container, "ping", "-c", str(count), "-W", "2", destination],
        capture_output=True,
        text=True,
        timeout=30,
    )
    return result.returncode == 0, result.stdout


class TestHostToHost:
    @pytest.mark.parametrize(
        "path",
        EXPECTED_STATE["reachability_matrix"],
        ids=lambda p: f"{p['src']}-to-{p['dst_name']}",
    )
    def test_host_reachability(self, path):
        src_container = HOSTS[path["src"]]["container"]
        success, output = ping_from_container(src_container, path["dst_ip"])
        assert success, (
            f"{path['src']} cannot reach {path['dst_name']} ({path['dst_ip']})\n"
            f"Ping output: {output}"
        )


class TestHostToGateway:
    @pytest.mark.parametrize("host_name", HOSTS.keys())
    def test_gateway_reachable(self, host_name):
        host = HOSTS[host_name]
        success, output = ping_from_container(host["container"], host["gateway"])
        assert success, (
            f"{host_name} cannot reach gateway {host['gateway']}\n"
            f"Ping output: {output}"
        )


class TestHostToISP:
    @pytest.mark.parametrize("host_name", HOSTS.keys())
    def test_isp_reachable(self, host_name):
        host = HOSTS[host_name]
        success, output = ping_from_container(host["container"], "203.0.113.1")
        assert success, (
            f"{host_name} cannot reach ISP router (203.0.113.1)\n"
            f"Ping output: {output}"
        )


class TestLoopbackReachability:
    LOOPBACKS = {
        "edge-1": "10.0.255.10",
        "dist-1": "10.0.255.11",
        "dist-2": "10.0.255.12",
    }

    @pytest.mark.parametrize("host_name", HOSTS.keys())
    def test_all_loopbacks_reachable(self, host_name):
        host = HOSTS[host_name]
        for router, loopback in self.LOOPBACKS.items():
            success, output = ping_from_container(host["container"], loopback)
            assert success, (
                f"{host_name} cannot reach {router} loopback ({loopback})\n"
                f"Ping output: {output}"
            )
