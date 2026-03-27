"""
Device inventory for Netaform Phase 4 (cEOS variant).
Provides connection details for NAPALM and pytest fixtures.
"""

import os

CEOS_CREDENTIALS = {
    "username": os.environ.get("CEOS_USER", "admin"),
    "password": os.environ.get("CEOS_PASSWORD", "admin"),
}

DEVICES = {
    "edge-1": {
        "hostname": "clab-netaform-p4-ceos-edge-1",
        "role": "border_router",
        "driver": "eos",
        **CEOS_CREDENTIALS,
        "optional_args": {"transport": "https"},
    },
    "dist-1": {
        "hostname": "clab-netaform-p4-ceos-dist-1",
        "role": "distribution",
        "driver": "eos",
        **CEOS_CREDENTIALS,
        "optional_args": {"transport": "https"},
    },
    "dist-2": {
        "hostname": "clab-netaform-p4-ceos-dist-2",
        "role": "distribution",
        "driver": "eos",
        **CEOS_CREDENTIALS,
        "optional_args": {"transport": "https"},
    },
}

HOSTS = {
    "host-eng": {
        "container": "clab-netaform-p4-ceos-host-eng",
        "ip": "10.0.10.100",
        "gateway": "10.0.10.2",
        "vlan": 10,
    },
    "host-sales": {
        "container": "clab-netaform-p4-ceos-host-sales",
        "ip": "10.0.20.100",
        "gateway": "10.0.20.3",
        "vlan": 20,
    },
    "host-server": {
        "container": "clab-netaform-p4-ceos-host-server",
        "ip": "10.0.30.100",
        "gateway": "10.0.30.3",
        "vlan": 30,
    },
}

EXPECTED_STATE = {
    "bgp_peers": {
        "edge-1": {
            "203.0.113.1": {"peer_as": 65000, "should_be_up": True},
        },
    },
    "ospf_neighbors": {
        "edge-1": ["10.0.255.11", "10.0.255.12"],
        "dist-1": ["10.0.255.10", "10.0.255.12"],
        "dist-2": ["10.0.255.10", "10.0.255.11"],
    },
    "reachability_matrix": [
        {"src": "host-eng", "dst_ip": "10.0.20.100", "dst_name": "host-sales"},
        {"src": "host-eng", "dst_ip": "10.0.30.100", "dst_name": "host-server"},
        {"src": "host-sales", "dst_ip": "10.0.10.100", "dst_name": "host-eng"},
        {"src": "host-sales", "dst_ip": "10.0.30.100", "dst_name": "host-server"},
        {"src": "host-server", "dst_ip": "10.0.10.100", "dst_name": "host-eng"},
        {"src": "host-server", "dst_ip": "10.0.20.100", "dst_name": "host-sales"},
    ],
}
