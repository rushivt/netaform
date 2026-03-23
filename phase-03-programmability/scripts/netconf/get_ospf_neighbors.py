#!/usr/bin/env python3
"""
get_ospf_neighbors.py - Fetch OSPF neighbors via NETCONF.

Demonstrates NETCONF <get> with subtree filtering using the Nokia native
YANG model (srl_nokia-ospf). This script targets dist-3 (Nokia SR Linux)
but the approach is the same for any NETCONF-capable device.
"""

import sys
import json
import xmltodict
from ncclient import manager

sys.path.insert(0, "..")
from inventory import get_device


# Nokia native YANG filter for OSPF neighbors
SRL_OSPF_FILTER = """
<network-instance xmlns="urn:nokia.com:srlinux:net-inst:network-instance">
  <name>default</name>
  <protocols>
    <ospf xmlns="urn:nokia.com:srlinux:ospf:ospf">
      <instance>
        <name>main</name>
        <area>
          <area-id>0.0.0.0</area-id>
          <interface>
            <interface-name/>
            <neighbor/>
          </interface>
        </area>
      </instance>
    </ospf>
  </protocols>
</network-instance>
"""


def fetch_ospf_neighbors(device_name):
    """Fetch OSPF neighbors from a device via NETCONF."""
    dev = get_device(device_name)
    print(f"Fetching OSPF neighbors from {device_name} ({dev['host']}) [{dev['vendor']}]...\n")

    with manager.connect(
        host=dev["host"],
        port=dev["netconf_port"],
        username=dev["username"],
        password=dev["password"],
        hostkey_verify=False,
        timeout=30,
    ) as m:
        result = m.get(filter=("subtree", SRL_OSPF_FILTER))

    # Parse XML to dict
    data = xmltodict.parse(result.xml)
    rpc_reply = data.get("rpc-reply", {}).get("data", {})

    if not rpc_reply:
        print("  No OSPF data returned.")
        return

    # Navigate to the OSPF instance
    ni = rpc_reply.get("network-instance", {})
    ospf = (
        ni.get("protocols", {})
        .get("ospf", {})
        .get("instance", {})
    )

    areas = ospf.get("area", {})
    if not isinstance(areas, list):
        areas = [areas]

    print(f"  Router ID: {ospf.get('router-id', 'N/A')}")
    print(f"  Instance:  {ospf.get('name', 'N/A')}")
    print()

    for area in areas:
        area_id = area.get("area-id", "N/A")
        interfaces = area.get("interface", [])
        if not isinstance(interfaces, list):
            interfaces = [interfaces]

        for intf in interfaces:
            intf_name = intf.get("interface-name", "N/A")
            neighbors = intf.get("neighbor", [])
            if not neighbors:
                continue
            if not isinstance(neighbors, list):
                neighbors = [neighbors]

            for nbr in neighbors:
                print(f"  Interface: {intf_name}")
                print(f"    Neighbor Router ID: {nbr.get('router-id', 'N/A')}")
                print(f"    State:             {nbr.get('state', 'N/A')}")
                print(f"    Address:           {nbr.get('address', 'N/A')}")
                print(f"    Priority:          {nbr.get('priority', 'N/A')}")
                print(f"    Area:              {area_id}")
                print()

    # Also output raw JSON for structured consumption
    print("--- Raw JSON ---")
    print(json.dumps(rpc_reply, indent=2))


if __name__ == "__main__":
    device = sys.argv[1] if len(sys.argv) > 1 else "dist-3"
    fetch_ospf_neighbors(device)
