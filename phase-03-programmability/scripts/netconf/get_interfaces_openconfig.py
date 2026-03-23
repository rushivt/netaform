#!/usr/bin/env python3
"""
get_interfaces_openconfig.py - Multi-vendor interface status via NETCONF.

Uses OpenConfig YANG models (http://openconfig.net/yang/interfaces).
The SAME filter and parsing logic works against both Arista cEOS and
Nokia SR Linux — demonstrating the vendor-neutral promise of OpenConfig.
"""

import sys
import json
import xmltodict
from ncclient import manager

sys.path.insert(0, "..")
from inventory import get_device


OC_INTERFACES_FILTER = """
<interfaces xmlns="http://openconfig.net/yang/interfaces">
</interfaces>
"""


def fetch_interfaces_oc(device_name):
    """Fetch interfaces using OpenConfig YANG model — works on any vendor."""
    dev = get_device(device_name)
    print(f"\n{'='*70}")
    print(f"  Device: {device_name} ({dev['host']}) | Vendor: {dev['vendor']}")
    print(f"  Model:  OpenConfig (http://openconfig.net/yang/interfaces)")
    print(f"{'='*70}\n")

    with manager.connect(
        host=dev["host"],
        port=dev["netconf_port"],
        username=dev["username"],
        password=dev["password"],
        hostkey_verify=False,
        timeout=30,
    ) as m:
        result = m.get(filter=("subtree", OC_INTERFACES_FILTER))

    data = xmltodict.parse(result.xml)
    rpc_reply = data.get("rpc-reply", {}).get("data", {})

    if not rpc_reply:
        print("  No interface data returned.\n")
        return

    interfaces = rpc_reply.get("interfaces", {}).get("interface", [])
    if not isinstance(interfaces, list):
        interfaces = [interfaces]

    # Header
    print(f"  {'Interface':<25} {'Admin':<10} {'Oper':<10} {'In Bytes':<15} {'Out Bytes':<15} {'Description'}")
    print(f"  {'-'*25} {'-'*10} {'-'*10} {'-'*15} {'-'*15} {'-'*30}")

    for intf in interfaces:
        name = intf.get("name", "N/A")
        state = intf.get("state", {})
        config = intf.get("config", {})

        admin = state.get("admin-status", config.get("enabled", "N/A"))
        oper = state.get("oper-status", "N/A")
        desc = state.get("description", config.get("description", ""))

        counters = state.get("counters", {})
        in_oct = counters.get("in-octets", "-")
        out_oct = counters.get("out-octets", "-")

        print(f"  {name:<25} {admin:<10} {oper:<10} {str(in_oct):<15} {str(out_oct):<15} {desc}")

        # Subinterfaces
        subintfs = intf.get("subinterfaces", {}).get("subinterface", [])
        if not isinstance(subintfs, list):
            subintfs = [subintfs]

        for sub in subintfs:
            if not isinstance(sub, dict):
                continue
            sub_idx = sub.get("index", sub.get("config", {}).get("index", "?"))
            sub_state = sub.get("state", {})
            sub_admin = sub_state.get("admin-status", "N/A")
            sub_oper = sub_state.get("oper-status", "N/A")

            # Get IP from OpenConfig ip model
            ipv4 = sub.get("ipv4", {})
            if isinstance(ipv4, dict):
                addrs = ipv4.get("addresses", {}).get("address", [])
                if not isinstance(addrs, list):
                    addrs = [addrs]
                ip_str = ", ".join(
                    f"{a.get('ip', a.get('config', {}).get('ip', ''))}/{a.get('config', {}).get('prefix-length', a.get('state', {}).get('prefix-length', ''))}"
                    for a in addrs if isinstance(a, dict)
                )
            else:
                ip_str = ""

            if ip_str:
                print(f"    .{str(sub_idx):<22} {sub_admin:<10} {sub_oper:<10} {ip_str}")

    print()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        devices = sys.argv[1:]
    else:
        devices = ["edge-1", "dist-3"]

    for dev_name in devices:
        try:
            fetch_interfaces_oc(dev_name)
        except Exception as e:
            print(f"  FAILED on {dev_name}: {e}\n")
