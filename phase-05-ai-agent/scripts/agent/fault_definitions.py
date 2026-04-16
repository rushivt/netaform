# ---------------------------------------------------------------------------
# FAULT DEFINITIONS
# This file defines every fault scenario Bantu knows how to handle.
# Each fault has:
#   - severity   : LOW (auto-fix) or HIGH (generate playbook, wait for review)
#   - description: Human readable explanation of the fault
#   - symptoms   : What Bantu looks for in NAPALM data to detect this fault
#   - fix_commands: EOS CLI commands that resolve the fault (used for LOW
#                   severity auto-fix AND as input to playbook generator
#                   for HIGH severity)
#   - verify_fn  : String name of the tool function Bantu calls after fixing
#                  to confirm the fault is resolved
#
# USED BY: scripts/agent/bantu.py — loaded at startup
# OUTCOME: Bantu matches incoming alert data against these definitions
#          to classify, diagnose, and respond to each fault
# ---------------------------------------------------------------------------

FAULT_DEFINITIONS = {

    "interface_down": {
        # -----------------------------------------------------------------------
        # SEVERITY: LOW
        # An interface going down is operationally safe to auto-fix with
        # "no shutdown" — it restores the previous intended state.
        # This is the most common recoverable fault in the lab.
        # -----------------------------------------------------------------------
        "severity": "LOW",
        "description": "Interface is administratively shutdown causing downstream failures",
        "symptoms": {
            # NAPALM get_interfaces() returns is_enabled: False when
            # an interface has been manually shut down via "shutdown" command
            "tool": "get_interfaces",
            "condition": "is_enabled == False"
        },
        "fix_commands": [
            # "no shutdown" re-enables the interface
            # The interface name is injected dynamically by Bantu at runtime
            "interface {interface}",
            "no shutdown"
        ],
        "verify_fn": "get_interfaces"
    },

    "bgp_asn_mismatch": {
        # -----------------------------------------------------------------------
        # SEVERITY: HIGH
        # A BGP ASN mismatch means the neighbor configuration is wrong.
        # Changing BGP ASN affects routing policy and traffic paths —
        # requires human review before applying.
        # -----------------------------------------------------------------------
        "severity": "HIGH",
        "description": "BGP session down due to ASN mismatch with neighbor",
        "symptoms": {
            # NAPALM get_bgp_neighbors() returns is_up: False when
            # the BGP session cannot establish due to ASN mismatch
            "tool": "get_bgp_neighbors",
            "condition": "is_up == False"
        },
        "fix_commands": [
            # Commands are placeholders — actual ASN values injected by Bantu
            # after it reads the correct ASN from the alert context
            "router bgp {local_asn}",
            "neighbor {neighbor_ip} remote-as {correct_asn}"
        ],
        "verify_fn": "get_bgp_neighbors"
    },

    "acl_blocking_traffic": {
        # -----------------------------------------------------------------------
        # SEVERITY: HIGH
        # A static route blackhole silently drops traffic to a destination.
        # Removing a static route affects routing policy — requires human review
        # before applying in case the route was intentionally added.
        # -----------------------------------------------------------------------
        "severity": "HIGH",
        "description": "Static route blackhole silently dropping traffic to destination",
        "symptoms": {
            # Detected via ping failure + route table shows unexpected static
            # route with null0 or wrong next-hop pointing to nowhere
            "tool": "ping_device",
            "condition": "packet_loss == 100"
        },
        "fix_commands": [
            # Placeholder — actual prefix injected by Bantu from route table
            "no ip route {prefix} {next_hop}"
        ],
        "verify_fn": "ping_device"
    },

    "ospf_area_mismatch": {
        # -----------------------------------------------------------------------
        # SEVERITY: HIGH
        # OSPF area mismatches affect the entire internal routing domain.
        # Changing OSPF area config can cause widespread route loss —
        # must be reviewed before applying.
        # -----------------------------------------------------------------------
        "severity": "HIGH",
        "description": "OSPF neighbor down due to area mismatch",
        "symptoms": {
            # NAPALM get_network_instances() returns OSPF neighbor state
            # A missing or down neighbor indicates area mismatch
            "tool": "get_ospf_neighbors",
            "condition": "neighbor_count == 0"
        },
        "fix_commands": [
            # Placeholder — actual interface and area injected by Bantu
            "interface {interface}",
            "ip ospf area {correct_area}"
        ],
        "verify_fn": "get_ospf_neighbors"
    }
}


def get_fault(fault_type):
    # ---------------------------------------------------------------------------
    # PURPOSE: Returns the fault definition dict for a given fault type
    # USED BY: bantu.py when it needs to look up severity and fix commands
    # OUTCOME: Returns the fault dict or raises KeyError if unknown fault type
    # ---------------------------------------------------------------------------
    if fault_type not in FAULT_DEFINITIONS:
        raise KeyError(f"Unknown fault type: {fault_type}. "
                       f"Known faults: {list(FAULT_DEFINITIONS.keys())}")
    return FAULT_DEFINITIONS[fault_type]


def get_all_faults():
    # ---------------------------------------------------------------------------
    # PURPOSE: Returns all fault type names Bantu knows about
    # USED BY: bantu.py at startup when printing Bantu's capabilities
    # OUTCOME: Returns list of fault type strings
    # ---------------------------------------------------------------------------
    return list(FAULT_DEFINITIONS.keys())
