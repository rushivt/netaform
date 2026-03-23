#!/usr/bin/env python3
"""
maarpu.py — Config Drift Detector (Telugu: maarpu = "change")

Pulls running configuration from a device via NETCONF, compares it
against the intended state defined in the Ansible host_vars — the
same single source of truth used to configure the device.

Usage:
    python3 maarpu.py [device_name]
    python3 maarpu.py dist-3
"""

import sys
import os
import yaml
import json
import xmltodict
from datetime import datetime
from ncclient import manager

sys.path.insert(0, "..")
from inventory import get_device

HOSTVARS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "ansible", "host_vars"
)


def load_intended(device_name):
    """Load intended state from Ansible host_vars."""
    vars_path = os.path.join(HOSTVARS_DIR, device_name, "vars.yml")
    if not os.path.exists(vars_path):
        print(f"  ERROR: Host vars not found: {vars_path}")
        sys.exit(1)
    with open(vars_path, "r") as f:
        return yaml.safe_load(f), vars_path


def fetch_hostname(m):
    """Fetch hostname via NETCONF."""
    filt = """
    <system xmlns="urn:nokia.com:srlinux:general:system">
      <name xmlns="urn:nokia.com:srlinux:chassis:system-name">
        <host-name/>
      </name>
    </system>
    """
    result = m.get(filter=("subtree", filt))
    data = xmltodict.parse(result.xml)
    system = data.get("rpc-reply", {}).get("data", {}).get("system", {})
    name_block = system.get("name", {})
    if isinstance(name_block, dict):
        return name_block.get("host-name", "UNKNOWN")
    return "UNKNOWN"


def fetch_interfaces(m):
    """Fetch interface config via NETCONF."""
    filt = """
    <interface xmlns="urn:nokia.com:srlinux:chassis:interfaces">
    </interface>
    """
    result = m.get_config(source="running", filter=("subtree", filt))
    data = xmltodict.parse(result.xml)
    interfaces_raw = data.get("rpc-reply", {}).get("data", {}).get("interface", [])
    if not isinstance(interfaces_raw, list):
        interfaces_raw = [interfaces_raw]

    interfaces = {}
    for intf in interfaces_raw:
        if not isinstance(intf, dict):
            continue
        name = intf.get("name", "")
        admin = intf.get("admin-state", "N/A")
        desc = intf.get("description", "")

        ipv4 = ""
        subintfs = intf.get("subinterface", [])
        if not isinstance(subintfs, list):
            subintfs = [subintfs]
        for sub in subintfs:
            if not isinstance(sub, dict):
                continue
            if str(sub.get("index", "")) == "0":
                ipv4_block = sub.get("ipv4", {})
                if isinstance(ipv4_block, dict):
                    addrs = ipv4_block.get("address", [])
                    if not isinstance(addrs, list):
                        addrs = [addrs]
                    for a in addrs:
                        if isinstance(a, dict):
                            ipv4 = a.get("ip-prefix", "")
                            break

        interfaces[name] = {
            "admin_state": admin,
            "description": desc,
            "ipv4_address": ipv4,
        }

    return interfaces


def fetch_ospf(m):
    """Fetch OSPF config via NETCONF."""
    filt = """
    <network-instance xmlns="urn:nokia.com:srlinux:net-inst:network-instance">
      <name>default</name>
      <protocols>
        <ospf xmlns="urn:nokia.com:srlinux:ospf:ospf">
          <instance>
            <name/>
            <router-id/>
            <area>
              <area-id/>
              <interface>
                <interface-name/>
              </interface>
            </area>
          </instance>
        </ospf>
      </protocols>
    </network-instance>
    """
    result = m.get_config(source="running", filter=("subtree", filt))
    data = xmltodict.parse(result.xml)
    ni = data.get("rpc-reply", {}).get("data", {}).get("network-instance", {})
    ospf_inst = ni.get("protocols", {}).get("ospf", {}).get("instance", {})

    area_data = ospf_inst.get("area", {})
    intfs_raw = area_data.get("interface", [])
    if not isinstance(intfs_raw, list):
        intfs_raw = [intfs_raw]

    return {
        "instance": ospf_inst.get("name", ""),
        "router_id": ospf_inst.get("router-id", ""),
        "area": area_data.get("area-id", ""),
        "interfaces": sorted([i.get("interface-name", "") for i in intfs_raw if isinstance(i, dict)]),
    }


def run_maarpu(device_name):
    """Run the drift detection using Ansible host_vars as intended state."""
    dev = get_device(device_name)
    intended, vars_path = load_intended(device_name)

    print(f"""
{'='*70}
  MAARPU — Config Drift Detector
  Device:    {device_name} ({dev['host']}) [{dev['vendor']}]
  Time:      {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
  Source:    NETCONF (running config)
  Intended:  {vars_path}
{'='*70}
""")

    with manager.connect(
        host=dev["host"],
        port=dev["netconf_port"],
        username=dev["username"],
        password=dev["password"],
        hostkey_verify=False,
        timeout=30,
    ) as m:

        all_drifts = []

        # 1. Check hostname
        print("  Checking hostname...")
        actual_hostname = fetch_hostname(m)
        if actual_hostname != intended.get("hostname", ""):
            all_drifts.append({
                "path": "/system/name/host-name",
                "type": "MISMATCH",
                "expected": intended["hostname"],
                "actual": actual_hostname,
            })

        # 2. Check routed interfaces
        print("  Checking interfaces...")
        actual_intfs = fetch_interfaces(m)

        for intf_intended in intended.get("routed_interfaces", []):
            name = intf_intended["name"]
            actual = actual_intfs.get(name)
            if not actual:
                all_drifts.append({
                    "path": f"/interface/{name}",
                    "type": "MISSING",
                    "expected": "interface should exist",
                })
                continue

            if intf_intended.get("description", "") != actual.get("description", ""):
                all_drifts.append({
                    "path": f"/interface/{name}/description",
                    "type": "MISMATCH",
                    "expected": intf_intended["description"],
                    "actual": actual["description"],
                })

            if actual.get("admin_state", "") != "enable":
                all_drifts.append({
                    "path": f"/interface/{name}/admin-state",
                    "type": "MISMATCH",
                    "expected": "enable",
                    "actual": actual.get("admin_state", "N/A"),
                })

            if intf_intended.get("ipv4_address", "") != actual.get("ipv4_address", ""):
                all_drifts.append({
                    "path": f"/interface/{name}/ipv4-address",
                    "type": "MISMATCH",
                    "expected": intf_intended["ipv4_address"],
                    "actual": actual.get("ipv4_address", "N/A"),
                })

        # 3. Check loopback
        print("  Checking loopback...")
        lo = intended.get("loopback", {})
        lo_name = lo.get("name", "")
        actual_lo = actual_intfs.get(lo_name)
        if actual_lo:
            if lo.get("ipv4_address", "") != actual_lo.get("ipv4_address", ""):
                all_drifts.append({
                    "path": f"/interface/{lo_name}/ipv4-address",
                    "type": "MISMATCH",
                    "expected": lo["ipv4_address"],
                    "actual": actual_lo.get("ipv4_address", "N/A"),
                })
        elif lo_name:
            all_drifts.append({
                "path": f"/interface/{lo_name}",
                "type": "MISSING",
                "expected": "loopback should exist",
            })

        # 4. Check OSPF
        print("  Checking OSPF...")
        actual_ospf = fetch_ospf(m)
        intended_ospf = intended.get("ospf", {})

        ospf_checks = {
            "instance": ("instance_name", "instance"),
            "router_id": ("router_id", "router_id"),
            "area": ("area", "area"),
        }

        for label, (intended_key, actual_key) in ospf_checks.items():
            expected = str(intended_ospf.get(intended_key, ""))
            actual = str(actual_ospf.get(actual_key, ""))
            if expected and expected != actual:
                all_drifts.append({
                    "path": f"/ospf/{label}",
                    "type": "MISMATCH",
                    "expected": expected,
                    "actual": actual,
                })

        intended_ospf_intfs = sorted(intended_ospf.get("interfaces", []))
        actual_ospf_intfs = sorted(actual_ospf.get("interfaces", []))
        missing_ospf = set(intended_ospf_intfs) - set(actual_ospf_intfs)
        extra_ospf = set(actual_ospf_intfs) - set(intended_ospf_intfs)
        if missing_ospf:
            all_drifts.append({
                "path": "/ospf/interfaces",
                "type": "MISSING",
                "expected": sorted(list(missing_ospf)),
            })
        if extra_ospf:
            all_drifts.append({
                "path": "/ospf/interfaces",
                "type": "EXTRA",
                "found": sorted(list(extra_ospf)),
            })

    # Report
    print()
    if not all_drifts:
        print("  RESULT: NO DRIFT DETECTED")
        print("  Running config matches intended state.")
    else:
        print(f"  RESULT: {len(all_drifts)} DRIFT(S) DETECTED\n")
        for i, drift in enumerate(all_drifts, 1):
            print(f"  [{i}] {drift['type']} at {drift['path']}")
            if drift["type"] == "MISMATCH":
                print(f"      Expected: {drift['expected']}")
                print(f"      Actual:   {drift['actual']}")
            elif drift["type"] == "MISSING":
                print(f"      Expected: {drift.get('expected', 'N/A')}")
            elif drift["type"] == "EXTRA":
                print(f"      Found:    {drift.get('found', 'N/A')}")
            print()

    print()
    return all_drifts


if __name__ == "__main__":
    device = sys.argv[1] if len(sys.argv) > 1 else "dist-3"
    run_maarpu(device)
