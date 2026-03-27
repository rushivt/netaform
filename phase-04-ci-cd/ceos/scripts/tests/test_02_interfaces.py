"""
Test Layer 2: Interface Validation
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "napalm"))

from napalm_helpers import get_all_interfaces, get_all_interfaces_ip

EXPECTED_INTERFACES = {
    "edge-1": [
        "Ethernet1",
        "Ethernet2",
        "Ethernet3",
        "Loopback0",
    ],
    "dist-1": [
        "Ethernet1",
        "Ethernet2",
        "Ethernet3",
        "Loopback0",
        "Vlan10",
    ],
    "dist-2": [
        "Ethernet1",
        "Ethernet2",
        "Ethernet3",
        "Ethernet4",
        "Loopback0",
        "Vlan20",
        "Vlan30",
    ],
}

EXPECTED_IPS = {
    "edge-1": {
        "Loopback0": "10.0.255.10",
        "Ethernet1": "203.0.113.2",
        "Ethernet2": "10.0.1.1",
        "Ethernet3": "10.0.1.5",
    },
    "dist-1": {
        "Loopback0": "10.0.255.11",
        "Ethernet1": "10.0.1.2",
        "Ethernet2": "10.0.1.9",
        "Vlan10": "10.0.10.2",
        "Vlan20": "10.0.20.2",
        "Vlan30": "10.0.30.2",
    },
    "dist-2": {
        "Loopback0": "10.0.255.12",
        "Ethernet1": "10.0.1.6",
        "Ethernet2": "10.0.1.10",
        "Vlan10": "10.0.10.3",
        "Vlan20": "10.0.20.3",
        "Vlan30": "10.0.30.3",
    },
}


@pytest.mark.parametrize("device_name", EXPECTED_INTERFACES.keys())
def test_interfaces_are_up(device_name):
    """Verify all expected interfaces are operationally up."""
    interfaces = get_all_interfaces(device_name)
    for intf_name in EXPECTED_INTERFACES[device_name]:
        assert intf_name in interfaces, (
            f"{device_name}: interface {intf_name} not found"
        )
        assert interfaces[intf_name]["is_up"], (
            f"{device_name}: {intf_name} is not up"
        )


@pytest.mark.parametrize("device_name", EXPECTED_IPS.keys())
def test_interface_ips_assigned(device_name):
    """Verify expected IP addresses are assigned to interfaces."""
    interfaces_ip = get_all_interfaces_ip(device_name)
    for intf_name, expected_ip in EXPECTED_IPS[device_name].items():
        assert intf_name in interfaces_ip, (
            f"{device_name}: {intf_name} not found in IP output"
        )
        assert "ipv4" in interfaces_ip[intf_name], (
            f"{device_name}: {intf_name} has no IPv4 addresses"
        )
        assert expected_ip in interfaces_ip[intf_name]["ipv4"], (
            f"{device_name}: {intf_name} missing expected IP {expected_ip}"
        )