#!/usr/bin/env python3
"""Quick NETCONF connectivity test."""

import sys
sys.path.insert(0, "../..")
sys.path.insert(0, "..")

from ncclient import manager
from inventory import get_device

def test_device(name):
    dev = get_device(name)
    print(f"Connecting to {name} ({dev['host']}:{dev['netconf_port']}) [{dev['vendor']}]...")

    with manager.connect(
        host=dev["host"],
        port=dev["netconf_port"],
        username=dev["username"],
        password=dev["password"],
        hostkey_verify=False,
        timeout=30,
    ) as m:
        print(f"  Connected! Session ID: {m.session_id}")
        caps = [c for c in m.server_capabilities]
        print(f"  Server capabilities: {len(caps)}")

        # Print a few interesting ones
        for cap in sorted(caps):
            if "candidate" in cap or "ospf" in cap or "interface" in cap:
                print(f"    {cap[:120]}")

    print(f"  Disconnected from {name}.\n")

if __name__ == "__main__":
    for device_name in ["dist-3", "edge-1"]:
        try:
            test_device(device_name)
        except Exception as e:
            print(f"  FAILED: {e}\n")
