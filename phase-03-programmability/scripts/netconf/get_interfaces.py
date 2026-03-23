#!/usr/bin/env python3
"""
get_interfaces.py - Fetch interface status and counters via NETCONF.

Uses Nokia native YANG model to retrieve interface operational state
from dist-3 (Nokia SR Linux).
"""

import sys
import json
import xmltodict
from ncclient import manager

sys.path.insert(0, "..")
from inventory import get_device


SRL_INTERFACE_FILTER = """
<interface xmlns="urn:nokia.com:srlinux:chassis:interfaces">
</interface>
"""


def fetch_interfaces(device_name):
    """Fetch all interfaces from a device via NETCONF."""
    dev = get_device(device_name)
    print(f"Fetching interfaces from {device_name} ({dev['host']}) [{dev['vendor']}]...\n")

    with manager.connect(
        host=dev["host"],
        port=dev["netconf_port"],
        username=dev["username"],
        password=dev["password"],
        hostkey_verify=False,
        timeout=30,
    ) as m:
        result = m.get(filter=("subtree", SRL_INTERFACE_FILTER))

    data = xmltodict.parse(result.xml)
    rpc_reply = data.get("rpc-reply", {}).get("data", {})

    if not rpc_reply:
        print("  No interface data returned.")
        return

    interfaces = rpc_reply.get("interface", [])
    if not isinstance(interfaces, list):
        interfaces = [interfaces]

    print(f"  {'Interface':<25} {'Admin':<10} {'Oper':<10} {'Description'}")
    print(f"  {'-'*25} {'-'*10} {'-'*10} {'-'*30}")

    for intf in interfaces:
        name = intf.get("name", "N/A")
        admin = intf.get("admin-state", "N/A")
        oper = intf.get("oper-state", "N/A")
        desc = intf.get("description", "")

        print(f"  {name:<25} {admin:<10} {oper:<10} {desc}")

        # Print subinterfaces if present
        subintfs = intf.get("subinterface", [])
        if not isinstance(subintfs, list):
            subintfs = [subintfs]

        for sub in subintfs:
            if not isinstance(sub, dict):
                continue
            sub_idx = sub.get("index", "?")
            sub_admin = sub.get("admin-state", "N/A")
            sub_oper = sub.get("oper-state", "N/A")
            ipv4 = sub.get("ipv4", {})
            addresses = ipv4.get("address", []) if isinstance(ipv4, dict) else []
            if not isinstance(addresses, list):
                addresses = [addresses]
            ip_str = ", ".join(
                a.get("ip-prefix", "") for a in addresses if isinstance(a, dict)
            )
            print(f"    .{sub_idx:<22} {sub_admin:<10} {sub_oper:<10} {ip_str}")

        # Print counters if present
        stats = intf.get("statistics", {})
        if isinstance(stats, dict) and stats:
            in_oct = stats.get("in-octets", "0")
            out_oct = stats.get("out-octets", "0")
            in_err = stats.get("in-errors", "0")
            out_err = stats.get("out-errors", "0")
            print(f"      Counters: in={in_oct} bytes, out={out_oct} bytes, in-err={in_err}, out-err={out_err}")

    print()


if __name__ == "__main__":
    device = sys.argv[1] if len(sys.argv) > 1 else "dist-3"
    fetch_interfaces(device)
