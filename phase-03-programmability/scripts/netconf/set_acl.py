#!/usr/bin/env python3
"""
set_acl.py - Push an ACL to dist-3 via NETCONF edit-config.

Demonstrates NETCONF write operations using:
  1. Lock candidate datastore
  2. edit-config to create an IPv4 ACL
  3. Validate the candidate config
  4. Commit
  5. Unlock

Uses Nokia native YANG model (srl_nokia-acl).
"""

import sys
import xmltodict
import json
from lxml import etree
from ncclient import manager

sys.path.insert(0, "..")
from inventory import get_device


ACL_XML = """
<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <acl xmlns="urn:nokia.com:srlinux:acl:acl">
    <acl-filter>
      <name>NETCONF-MANAGED-ACL</name>
      <type>ipv4</type>
      <description>ACL created via NETCONF - Phase 3 demonstration</description>
      <entry>
        <sequence-id>10</sequence-id>
        <description>Allow management subnet</description>
        <match>
          <ipv4>
            <source-ip>
              <prefix>172.20.20.0/24</prefix>
            </source-ip>
          </ipv4>
        </match>
        <action>
          <accept/>
        </action>
      </entry>
      <entry>
        <sequence-id>20</sequence-id>
        <description>Allow internal networks</description>
        <match>
          <ipv4>
            <source-ip>
              <prefix>10.0.0.0/8</prefix>
            </source-ip>
          </ipv4>
        </match>
        <action>
          <accept/>
        </action>
      </entry>
      <entry>
        <sequence-id>100</sequence-id>
        <description>Deny all other traffic</description>
        <action>
          <drop/>
        </action>
      </entry>
    </acl-filter>
  </acl>
</config>
"""


def push_acl(device_name):
    """Push an ACL to a device using NETCONF edit-config with full transaction."""
    dev = get_device(device_name)
    print(f"Pushing ACL to {device_name} ({dev['host']}) [{dev['vendor']}]...\n")

    with manager.connect(
        host=dev["host"],
        port=dev["netconf_port"],
        username=dev["username"],
        password=dev["password"],
        hostkey_verify=False,
        timeout=30,
    ) as m:

        # Parse the XML config into an lxml Element
        config_element = etree.fromstring(ACL_XML)

        # Step 1: Lock candidate datastore
        print("  [1/5] Locking candidate datastore...")
        m.lock(target="candidate")
        print("        Locked.")

        try:
            # Step 2: Edit config
            print("  [2/5] Pushing ACL via edit-config...")
            m.edit_config(target="candidate", config=config_element)
            print("        ACL written to candidate.")

            # Step 3: Validate
            print("  [3/5] Validating candidate config...")
            m.validate(source="candidate")
            print("        Validation passed.")

            # Step 4: Commit
            print("  [4/5] Committing...")
            m.commit()
            print("        Committed.")

        except Exception as e:
            print(f"\n  ERROR: {e}")
            print("  Discarding candidate changes...")
            m.discard_changes()
            raise
        finally:
            # Step 5: Unlock
            print("  [5/5] Unlocking candidate datastore...")
            m.unlock(target="candidate")
            print("        Unlocked.")

        print("\n  ACL push complete. Verifying...\n")

        # Verify by reading back the ACL
        verify_filter = """
        <acl xmlns="urn:nokia.com:srlinux:acl:acl">
          <acl-filter>
            <name>NETCONF-MANAGED-ACL</name>
            <type>ipv4</type>
          </acl-filter>
        </acl>
        """
        result = m.get_config(source="running", filter=("subtree", verify_filter))
        data = xmltodict.parse(result.xml)
        acl_data = data.get("rpc-reply", {}).get("data", {})

        print("  --- Verified ACL from running config ---")
        print(json.dumps(acl_data, indent=2))


def remove_acl(device_name):
    """Remove the ACL from a device using NETCONF edit-config with delete operation."""
    dev = get_device(device_name)
    print(f"Removing ACL from {device_name} ({dev['host']}) [{dev['vendor']}]...\n")

    delete_xml = """
    <config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
      <acl xmlns="urn:nokia.com:srlinux:acl:acl">
        <acl-filter xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" nc:operation="delete">
          <name>NETCONF-MANAGED-ACL</name>
          <type>ipv4</type>
        </acl-filter>
      </acl>
    </config>
    """

    with manager.connect(
        host=dev["host"],
        port=dev["netconf_port"],
        username=dev["username"],
        password=dev["password"],
        hostkey_verify=False,
        timeout=30,
    ) as m:
        config_element = etree.fromstring(delete_xml)
        m.lock(target="candidate")
        try:
            m.edit_config(target="candidate", config=config_element)
            m.validate(source="candidate")
            m.commit()
        except Exception as e:
            print(f"  ERROR: {e}")
            m.discard_changes()
            raise
        finally:
            m.unlock(target="candidate")
        print("  ACL removed successfully.\n")


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "push"
    device = sys.argv[2] if len(sys.argv) > 2 else "dist-3"

    if action == "push":
        push_acl(device)
    elif action == "remove":
        remove_acl(device)
    else:
        print(f"Usage: {sys.argv[0]} [push|remove] [device_name]")
