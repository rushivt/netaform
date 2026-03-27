"""
NAPALM helper functions for Netaform Phase 4 (cEOS variant).
Uses the EOS driver for vendor-neutral state retrieval.
"""

from napalm import get_network_driver
from inventory import DEVICES


def get_device_connection(device_name):
    """Return an open NAPALM connection to the specified device."""
    device_info = DEVICES[device_name]
    driver = get_network_driver(device_info["driver"])
    device = driver(
        hostname=device_info["hostname"],
        username=device_info["username"],
        password=device_info["password"],
        optional_args=device_info.get("optional_args", {}),
    )
    device.open()
    return device


def get_all_bgp_neighbors(device_name):
    """Fetch BGP neighbor table from a device using NAPALM."""
    device = get_device_connection(device_name)
    try:
        return device.get_bgp_neighbors()
    finally:
        device.close()


def get_all_interfaces(device_name):
    """Fetch interface status from a device using NAPALM."""
    device = get_device_connection(device_name)
    try:
        return device.get_interfaces()
    finally:
        device.close()


def get_all_interfaces_ip(device_name):
    """Fetch interface IP addresses from a device using NAPALM."""
    device = get_device_connection(device_name)
    try:
        return device.get_interfaces_ip()
    finally:
        device.close()


def get_device_facts(device_name):
    """Fetch device facts (hostname, model, OS version) using NAPALM."""
    device = get_device_connection(device_name)
    try:
        return device.get_facts()
    finally:
        device.close()


def get_route_to(device_name, destination):
    """Fetch routing table entry for a destination using NAPALM."""
    device = get_device_connection(device_name)
    try:
        return device.get_route_to(destination=destination)
    finally:
        device.close()


if __name__ == "__main__":
    for name in DEVICES:
        print(f"\n{'=' * 50}")
        print(f"Device: {name}")
        print(f"{'=' * 50}")
        try:
            facts = get_device_facts(name)
            print(f"  Hostname : {facts['hostname']}")
            print(f"  Model    : {facts['model']}")
            print(f"  OS       : {facts['os_version']}")
            print(f"  Status   : CONNECTED")
        except Exception as e:
            print(f"  Status   : FAILED - {e}")
