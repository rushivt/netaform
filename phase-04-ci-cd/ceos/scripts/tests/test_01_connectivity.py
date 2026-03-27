"""
Test Layer 1: Device Connectivity
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "napalm"))

from inventory import DEVICES
from napalm_helpers import get_device_facts


@pytest.mark.parametrize("device_name", DEVICES.keys())
def test_device_reachable(device_name):
    """Verify each cEOS device is reachable via NAPALM."""
    facts = get_device_facts(device_name)
    assert facts is not None, f"{device_name} returned no facts"
    assert facts["hostname"] != "", f"{device_name} has empty hostname"


@pytest.mark.parametrize("device_name", DEVICES.keys())
def test_device_hostname_matches(device_name):
    """Verify each device's configured hostname matches expected value."""
    facts = get_device_facts(device_name)
    assert device_name in facts["hostname"].lower(), (
        f"Expected hostname containing '{device_name}', "
        f"got '{facts['hostname']}'"
    )
