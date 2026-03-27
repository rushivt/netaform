"""
Test Layer 3: Protocol State Validation
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "napalm"))

from inventory import DEVICES, EXPECTED_STATE
from napalm_helpers import get_all_bgp_neighbors, get_route_to


class TestOSPF:
    """OSPF adjacency validation."""

    @pytest.mark.parametrize("device_name", EXPECTED_STATE["ospf_neighbors"].keys())
    def test_ospf_routes_learned(self, device_name):
        """Verify OSPF routes are in the routing table."""
        test_routes = ["10.0.10.0/24", "10.0.20.0/24", "10.0.30.0/24"]
        for route in test_routes:
            routes = get_route_to(device_name, route)
            assert len(routes) > 0, (
                f"{device_name}: no route found for {route}"
            )


class TestBGP:
    """BGP session validation."""

    def test_bgp_peer_established(self):
        """Verify edge-1's BGP peer to ISP is established."""
        bgp = get_all_bgp_neighbors("edge-1")
        assert "global" in bgp, "edge-1: no global BGP data returned"
        peers = bgp["global"]["peers"]
        assert "203.0.113.1" in peers, (
            "edge-1: BGP peer 203.0.113.1 (ISP) not found"
        )
        peer = peers["203.0.113.1"]
        assert peer["is_up"] is True, (
            "edge-1: BGP peer 203.0.113.1 is not established"
        )

    def test_bgp_peer_correct_asn(self):
        """Verify the ISP peer has the correct remote ASN."""
        bgp = get_all_bgp_neighbors("edge-1")
        peers = bgp["global"]["peers"]
        peer = peers.get("203.0.113.1", {})
        assert peer.get("remote_as") == 65000, (
            f"edge-1: expected ISP ASN 65000, got {peer.get('remote_as')}"
        )

    def test_bgp_default_route_received(self):
        """Verify edge-1 receives a default route from the ISP via BGP."""
        routes = get_route_to("edge-1", "0.0.0.0/0")
        assert len(routes) > 0, (
            "edge-1: no default route received from ISP"
        )

    def test_dist_switches_have_default_route(self):
        """Verify distribution switches learn the default route via OSPF."""
        for device in ["dist-1", "dist-2"]:
            routes = get_route_to(device, "0.0.0.0/0")
            assert len(routes) > 0, (
                f"{device}: no default route - OSPF default originate may not be working"
            )
