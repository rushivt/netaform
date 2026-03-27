"""
Test Layer 5: Security Validation
"""

import subprocess
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "napalm"))

from inventory import DEVICES


class TestACLConfiguration:

    @pytest.mark.parametrize("device_name", DEVICES.keys())
    def test_mgmt_acl_exists(self, device_name):
        """Verify the management ACL is configured on each device."""
        result = subprocess.run(
            [
                "docker", "exec",
                f"clab-netaform-p4-ceos-{device_name}",
                "Cli", "-p", "15", "-c", "show ip access-lists MGMT-ACCESS"
            ],
            capture_output=True, text=True, timeout=30,
        )
        assert "MGMT-ACCESS" in result.stdout, (
            f"{device_name}: management ACL 'MGMT-ACCESS' not found"
        )

    @pytest.mark.parametrize("device_name", DEVICES.keys())
    def test_acl_has_deny_rule(self, device_name):
        """Verify the ACL includes a deny-all rule."""
        result = subprocess.run(
            [
                "docker", "exec",
                f"clab-netaform-p4-ceos-{device_name}",
                "Cli", "-p", "15", "-c", "show ip access-lists MGMT-ACCESS"
            ],
            capture_output=True, text=True, timeout=30,
        )
        assert "deny" in result.stdout.lower(), (
            f"{device_name}: ACL should contain a deny rule"
        )