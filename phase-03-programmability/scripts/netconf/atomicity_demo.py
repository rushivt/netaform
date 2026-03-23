#!/usr/bin/env python3
"""
atomicity_demo.py — NETCONF Transaction Atomicity Demonstration

Demonstrates NETCONF's transactional capabilities that RESTCONF lacks:
  - Candidate datastore isolation
  - Lock/unlock for exclusive access
  - Validate before commit
  - Atomic commit (all-or-nothing)
  - Discard on failure (running config untouched)

Two scenarios:
  1. SUCCESS: Valid multi-part config change commits atomically
  2. FAILURE: Invalid config is caught, discarded safely
"""

import sys
import json
import xmltodict
from lxml import etree
from ncclient import manager

sys.path.insert(0, "..")
from inventory import get_device


def connect(dev):
    """Create a new NETCONF connection."""
    return manager.connect(
        host=dev["host"],
        port=dev["netconf_port"],
        username=dev["username"],
        password=dev["password"],
        hostkey_verify=False,
        timeout=30,
    )


def get_current_description(m, intf_name):
    """Helper to read current interface description."""
    filt = f"""
    <interface xmlns="urn:nokia.com:srlinux:chassis:interfaces">
      <name>{intf_name}</name>
      <description/>
    </interface>
    """
    result = m.get_config(source="running", filter=("subtree", filt))
    data = xmltodict.parse(result.xml)
    intf = data.get("rpc-reply", {}).get("data", {}).get("interface", {})
    return intf.get("description", "(none)")


def scenario_success(dev):
    """Scenario 1: Valid config change — full transaction succeeds."""
    print(f"""
{'='*70}
  SCENARIO 1: SUCCESSFUL ATOMIC TRANSACTION
  Device: dist-3 ({dev['host']})
{'='*70}
""")

    valid_config = """
    <config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
      <interface xmlns="urn:nokia.com:srlinux:chassis:interfaces">
        <name>ethernet-1/1</name>
        <description>Link to EDGE-1 [NETCONF-verified]</description>
      </interface>
      <interface xmlns="urn:nokia.com:srlinux:chassis:interfaces">
        <name>ethernet-1/2</name>
        <description>Link to DIST-2 [NETCONF-verified]</description>
      </interface>
    </config>
    """

    with connect(dev) as m:
        # Show current state
        print("  BEFORE transaction:")
        print(f"    ethernet-1/1 description: {get_current_description(m, 'ethernet-1/1')}")
        print(f"    ethernet-1/2 description: {get_current_description(m, 'ethernet-1/2')}")
        print()

        print("  [1/5] LOCK candidate datastore...")
        m.lock(target="candidate")
        print("        Candidate is now exclusively locked. No other session can modify it.")
        print()

        print("  [2/5] EDIT-CONFIG — writing TWO interface changes to candidate...")
        m.edit_config(target="candidate", config=etree.fromstring(valid_config))
        print("        Both changes written to candidate. Running config is UNTOUCHED.")
        print()

        print("  [3/5] VALIDATE — asking the device to check the candidate...")
        m.validate(source="candidate")
        print("        Validation PASSED. Config is syntactically and semantically correct.")
        print()

        print("  [4/5] COMMIT — applying candidate to running (atomic, all-or-nothing)...")
        m.commit()
        print("        Committed. BOTH changes applied to running config simultaneously.")
        print()

        print("  [5/5] UNLOCK candidate datastore...")
        m.unlock(target="candidate")
        print("        Unlocked. Other sessions can now modify the config.")
        print()

        # Show after state
        print("  AFTER transaction:")
        print(f"    ethernet-1/1 description: {get_current_description(m, 'ethernet-1/1')}")
        print(f"    ethernet-1/2 description: {get_current_description(m, 'ethernet-1/2')}")
        print()
        print("  RESULT: Both interfaces updated atomically in a single transaction.")
        print()

    # Restore original descriptions in a separate session
    with connect(dev) as m:
        restore_config = """
        <config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
          <interface xmlns="urn:nokia.com:srlinux:chassis:interfaces">
            <name>ethernet-1/1</name>
            <description>Link to EDGE-1</description>
          </interface>
          <interface xmlns="urn:nokia.com:srlinux:chassis:interfaces">
            <name>ethernet-1/2</name>
            <description>Link to DIST-2</description>
          </interface>
        </config>
        """
        m.lock(target="candidate")
        m.edit_config(target="candidate", config=etree.fromstring(restore_config))
        m.commit()
        m.unlock(target="candidate")
        print("  (Original descriptions restored.)\n")


def scenario_failure(dev):
    """Scenario 2: Invalid config — caught and discarded, running config safe."""
    print(f"""
{'='*70}
  SCENARIO 2: FAILED TRANSACTION — RUNNING CONFIG PROTECTED
  Device: dist-3 ({dev['host']})
{'='*70}
""")

    invalid_config = """
    <config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
      <interface xmlns="urn:nokia.com:srlinux:chassis:interfaces">
        <name>ethernet-1/1</name>
        <description>THIS SHOULD NOT PERSIST</description>
      </interface>
      <interface xmlns="urn:nokia.com:srlinux:chassis:interfaces">
        <name>ethernet-1/2</name>
        <subinterface>
          <index>0</index>
          <ipv4 xmlns="urn:nokia.com:srlinux:chassis:if-ip">
            <address>
              <ip-prefix>INVALID-NOT-AN-IP</ip-prefix>
            </address>
          </ipv4>
        </subinterface>
      </interface>
    </config>
    """

    with connect(dev) as m:
        # Show current state
        print("  BEFORE transaction:")
        print(f"    ethernet-1/1 description: {get_current_description(m, 'ethernet-1/1')}")
        print(f"    ethernet-1/2 description: {get_current_description(m, 'ethernet-1/2')}")
        print()

        print("  [1/5] LOCK candidate datastore...")
        m.lock(target="candidate")
        print("        Locked.")
        print()

        try:
            print("  [2/5] EDIT-CONFIG — writing a valid change + an INVALID change...")
            m.edit_config(target="candidate", config=etree.fromstring(invalid_config))
            print("        Written to candidate (not yet validated).")
            print()

            print("  [3/5] VALIDATE — asking the device to check the candidate...")
            m.validate(source="candidate")
            print("        Validation passed (unexpected).")
            print()

            print("  [4/5] COMMIT...")
            m.commit()
            print("        Committed (unexpected).")

        except Exception as e:
            error_lines = str(e).strip().split('\n')
            error_msg = error_lines[0][:100] if error_lines else "Unknown error"
            print(f"        REJECTED: {error_msg}")
            print()
            print("  [4/5] DISCARD-CHANGES — rolling back the candidate...")
            try:
                m.discard_changes()
                print("        Candidate discarded. ALL changes thrown away (even the valid one).")
            except Exception:
                print("        Candidate auto-discarded by the server (change was never accepted).")
            print()

        finally:
            print("  [5/5] UNLOCK candidate datastore...")
            m.unlock(target="candidate")
            print("        Unlocked.")
            print()

        # Show after state — should be unchanged
        print("  AFTER failed transaction:")
        print(f"    ethernet-1/1 description: {get_current_description(m, 'ethernet-1/1')}")
        print(f"    ethernet-1/2 description: {get_current_description(m, 'ethernet-1/2')}")
        print()
        print("  RESULT: Running config is UNTOUCHED. The invalid change was caught,")
        print("  and the valid change was also discarded — all-or-nothing atomicity.")
        print()
        print("  This is what RESTCONF cannot do. RESTCONF applies changes directly")
        print("  to running config with no candidate isolation, no validate step,")
        print("  and no ability to discard a batch of changes atomically.")
        print()


if __name__ == "__main__":
    dev = get_device("dist-3")
    scenario_success(dev)
    scenario_failure(dev)
