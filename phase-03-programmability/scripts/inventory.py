#!/usr/bin/env python3
"""
inventory.py - Dynamic device inventory helper for Phase 3 NETCONF/JSON-RPC scripts.

Reads the Containerlab-generated ansible-inventory.yml and provides
device connection details. No hardcoded IPs.
"""

import yaml
import os

INVENTORY_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "topology", "clab-branch-office", "ansible-inventory.yml"
)

# Device metadata not available in the Containerlab inventory
DEVICE_META = {
    "edge-1": {"vendor": "arista", "netconf_port": 830, "platform": "ceos"},
    "dist-1": {"vendor": "arista", "netconf_port": 830, "platform": "ceos"},
    "dist-2": {"vendor": "arista", "netconf_port": 830, "platform": "ceos"},
    "dist-3": {"vendor": "nokia", "netconf_port": 830, "platform": "srlinux"},
}


def load_inventory():
    """Parse the Containerlab ansible-inventory.yml and return device details."""
    with open(INVENTORY_PATH, "r") as f:
        inv = yaml.safe_load(f)

    devices = {}

    for group_name, group_data in inv.get("all", {}).get("children", {}).items():
        hosts = group_data.get("hosts", {})
        group_vars = group_data.get("vars", {})

        for fqdn, host_data in hosts.items():
            # Extract short name: clab-branch-office-edge-1 -> edge-1
            short_name = fqdn.replace("clab-branch-office-", "")

            if short_name not in DEVICE_META:
                continue

            meta = DEVICE_META[short_name]
            devices[short_name] = {
                "host": host_data.get("ansible_host", fqdn),
                "fqdn": fqdn,
                "username": group_vars.get("ansible_user", "admin"),
                "password": group_vars.get("ansible_password", "admin"),
                "vendor": meta["vendor"],
                "platform": meta["platform"],
                "netconf_port": meta["netconf_port"],
            }

    return devices


def get_device(name):
    """Get connection details for a single device by short name."""
    devices = load_inventory()
    if name not in devices:
        raise ValueError(
            f"Device '{name}' not found. Available: {list(devices.keys())}"
        )
    return devices[name]


def get_all_devices():
    """Get all network devices (excludes hosts and ISP)."""
    return load_inventory()


def get_arista_devices():
    """Get only Arista cEOS devices."""
    return {k: v for k, v in load_inventory().items() if v["vendor"] == "arista"}


def get_nokia_devices():
    """Get only Nokia SR Linux devices."""
    return {k: v for k, v in load_inventory().items() if v["vendor"] == "nokia"}


if __name__ == "__main__":
    print("=== Netaform Phase 3 Device Inventory ===\n")
    devices = get_all_devices()
    for name, info in sorted(devices.items()):
        print(f"  {name:10s}  {info['host']:15s}  {info['vendor']:8s}  port {info['netconf_port']}")
    print()
