import os
import sys
import time
import json
from datetime import datetime
from dotenv import load_dotenv
from colorama import Fore, Style, init

init(autoreset=True)

# Load environment variables first
load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))

# Add scripts directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tools.network_tools import (
    get_bgp_neighbors,
    get_interfaces,
    get_ospf_config,
    get_static_routes,
    ping_device,
    get_all_device_facts
)
from agent.bantu import handle_fault, print_bantu

# ---------------------------------------------------------------------------
# POLL INTERVAL
# How often Bantu checks the network in seconds
# 30 seconds is realistic for a lab — production would be 60-300 seconds
# ---------------------------------------------------------------------------
POLL_INTERVAL = 30

# ---------------------------------------------------------------------------
# EXPECTED STATE
# Defines what a healthy network looks like.
# Bantu compares live device state against these expectations every poll.
# If anything deviates, it triggers an investigation automatically.
# ---------------------------------------------------------------------------
EXPECTED_STATE = {
    # BGP sessions that must be established
    # Format: {device: [list of neighbor IPs that must be up]}
    "bgp": {
        "edge-1": ["203.0.113.1"]
    },

    # Interfaces that must be up and enabled
    # Format: {device: [list of interface names that must be up]}
    "interfaces": {
        "edge-1": ["Ethernet1", "Ethernet2", "Ethernet3"],
        "dist-1": ["Ethernet1", "Ethernet2"],
        "dist-2": ["Ethernet1", "Ethernet2"]
    },

    # OSPF neighbor counts — minimum expected neighbors per device
    # Format: {device: minimum_neighbor_count}
    "ospf_min_neighbors": {
        "edge-1": 2,
        "dist-1": 2,
        "dist-2": 2
    },

    # Reachability pairs that must succeed
    # Format: [[source_device, destination_ip, description], ...]
    "reachability": [
        ["dist-1", "10.0.30.100", "Engineering to Servers"],
        ["edge-1", "203.0.113.1", "Edge to ISP"],
    ],

    # Prefixes that must NOT appear as static routes pointing to Null0
    # Format: {device: [list of prefixes to watch for blackholes]}
    "blackhole_watch": {
        "dist-1": ["10.0.30.0/24", "10.0.20.0/24", "10.0.10.0/24"],
        "dist-2": ["10.0.30.0/24", "10.0.20.0/24", "10.0.10.0/24"],
        "edge-1": ["10.0.0.0/8"]
    }
}


def check_bgp(device, neighbors):
    # ---------------------------------------------------------------------------
    # PURPOSE: Checks if all expected BGP sessions are established
    # USED BY: run_health_checks() below
    # PARAMETERS:
    #   device    — hostname to check
    #   neighbors — list of neighbor IPs that must be up
    # OUTCOME: Returns list of fault dicts for any BGP session that is down
    #          Empty list means all BGP sessions healthy
    # ---------------------------------------------------------------------------
    faults = []
    try:
        data = get_bgp_neighbors(device)
        peers = data.get("global", {}).get("peers", {})
        for neighbor_ip in neighbors:
            if neighbor_ip not in peers:
                faults.append({
                    "alert_type": "bgp_down",
                    "device": device,
                    "details": {
                        "neighbor": neighbor_ip,
                        "expected_state": "established",
                        "current_state": "missing"
                    }
                })
            elif not peers[neighbor_ip].get("is_up", False):
                faults.append({
                    "alert_type": "bgp_down",
                    "device": device,
                    "details": {
                        "neighbor": neighbor_ip,
                        "expected_state": "established",
                        "current_state": "down",
                        "remote_as": peers[neighbor_ip].get("remote_as", "unknown")
                    }
                })
    except Exception as e:
        print_bantu(f"BGP check failed for {device}: {str(e)}", "error")
    return faults


def check_interfaces(device, expected_interfaces):
    # ---------------------------------------------------------------------------
    # PURPOSE: Checks if all expected interfaces are up and enabled
    # USED BY: run_health_checks() below
    # PARAMETERS:
    #   device               — hostname to check
    #   expected_interfaces  — list of interface names that must be up
    # OUTCOME: Returns list of fault dicts for any interface that is down
    # ---------------------------------------------------------------------------
    faults = []
    try:
        data = get_interfaces(device)
        for intf in expected_interfaces:
            if intf not in data:
                continue
            state = data[intf]
            # is_enabled=False means admin shutdown — that's our fault condition
            # is_up=False with is_enabled=True means physical link issue
            if not state.get("is_enabled", True):
                faults.append({
                    "alert_type": "interface_down",
                    "device": device,
                    "details": {
                        "interface": intf,
                        "is_enabled": False,
                        "is_up": state.get("is_up", False),
                        "description": state.get("description", ""),
                        "last_change": "detected by monitor"
                    }
                })
    except Exception as e:
        print_bantu(f"Interface check failed for {device}: {str(e)}", "error")
    return faults


def check_ospf(device, min_neighbors):
    # ---------------------------------------------------------------------------
    # PURPOSE: Checks if OSPF has minimum expected neighbor count
    # USED BY: run_health_checks() below
    # PARAMETERS:
    #   device        — hostname to check
    #   min_neighbors — minimum number of OSPF neighbors expected
    # HOW: Uses get_ospf_config() which runs actual CLI and returns neighbor table
    #      Counts lines containing "FULL" state in the neighbor output
    # OUTCOME: Returns fault dict if neighbor count below minimum, else empty list
    # ---------------------------------------------------------------------------
    faults = []
    try:
        data = get_ospf_config(device)
        neighbor_output = data.get("ospf_neighbors", "")
        # Count FULL adjacencies by looking for FULL in the neighbor table output
        full_count = neighbor_output.count("FULL")
        if full_count < min_neighbors:
            faults.append({
                "alert_type": "ospf_neighbor_down",
                "device": device,
                "details": {
                    "neighbor": "unknown",
                    "expected_area": "0.0.0.0",
                    "description": f"OSPF neighbor count {full_count} below expected {min_neighbors}",
                    "current_neighbors": full_count,
                    "expected_neighbors": min_neighbors
                }
            })
    except Exception as e:
        print_bantu(f"OSPF check failed for {device}: {str(e)}", "error")
    return faults


def check_reachability(source, destination, description):
    # ---------------------------------------------------------------------------
    # PURPOSE: Verifies end-to-end reachability between two points
    # USED BY: run_health_checks() below
    # PARAMETERS:
    #   source      — device to ping from
    #   destination — IP address to ping to
    #   description — human readable description of this reachability pair
    # OUTCOME: Returns fault dict if ping fails, empty list if succeeds
    # ---------------------------------------------------------------------------
    faults = []
    try:
        result = ping_device(source, destination)
        # NAPALM ping returns success dict with packet_loss key
        success = result.get("success", {})
        packet_loss = success.get("packet_loss", 100)
        if packet_loss == 100:
            faults.append({
                "alert_type": "reachability_failure",
                "device": source,
                "details": {
                    "source": source,
                    "destination": destination,
                    "description": description,
                    "packet_loss": packet_loss
                }
            })
    except Exception as e:
        print_bantu(f"Reachability check failed {source}→{destination}: {str(e)}", "error")
    return faults


def check_blackholes(device, watched_prefixes):
    # ---------------------------------------------------------------------------
    # PURPOSE: Checks for unexpected static blackhole routes on a device
    # USED BY: run_health_checks() below
    # PARAMETERS:
    #   device          — hostname to check
    #   watched_prefixes — list of prefixes to watch for Null0 routes
    # HOW: Runs get_static_routes() and checks if any watched prefix
    #      appears in the output alongside "Null" keyword
    # OUTCOME: Returns fault dict for each blackhole found
    # ---------------------------------------------------------------------------
    faults = []
    try:
        data = get_static_routes(device)
        route_output = data.get("static_routes", "")
        for prefix in watched_prefixes:
            # Check if this prefix appears in static routes with Null0
            if prefix in route_output and "Null" in route_output:
                faults.append({
                    "alert_type": "reachability_failure",
                    "device": device,
                    "details": {
                        "source": "10.0.10.100",
                        "destination": "10.0.30.100",
                        "description": f"Static blackhole detected for {prefix} on {device}",
                        "suspected_blackhole": prefix
                    }
                })
                break  # One fault per device per poll cycle
    except Exception as e:
        print_bantu(f"Blackhole check failed for {device}: {str(e)}", "error")
    return faults


def run_health_checks():
    # ---------------------------------------------------------------------------
    # PURPOSE: Runs all health checks and returns list of detected faults
    # USED BY: monitoring_loop() below on every poll cycle
    # HOW: Calls all check functions and collects results into one list
    #      Deduplicates faults so same fault isn't investigated twice
    # OUTCOME: Returns list of fault dicts ready to pass to handle_fault()
    # ---------------------------------------------------------------------------
    all_faults = []

    # BGP checks
    for device, neighbors in EXPECTED_STATE["bgp"].items():
        all_faults.extend(check_bgp(device, neighbors))

    # Interface checks
    for device, interfaces in EXPECTED_STATE["interfaces"].items():
        all_faults.extend(check_interfaces(device, interfaces))

    # OSPF checks
    for device, min_nbrs in EXPECTED_STATE["ospf_min_neighbors"].items():
        all_faults.extend(check_ospf(device, min_nbrs))

    # Reachability checks
    for source, dest, desc in EXPECTED_STATE["reachability"]:
        all_faults.extend(check_reachability(source, dest, desc))

    # Blackhole checks
    for device, prefixes in EXPECTED_STATE["blackhole_watch"].items():
        all_faults.extend(check_blackholes(device, prefixes))

    return all_faults


def print_incident_report(fault, analysis_start, analysis_end):
    # ---------------------------------------------------------------------------
    # PURPOSE: Prints a clear structured incident report after each fault is handled
    # USED BY: monitoring_loop() after handle_fault() completes
    # OUTCOME: Prints timestamped incident summary to terminal
    # ---------------------------------------------------------------------------
    duration = (analysis_end - analysis_start).seconds
    print_bantu("=" * 60, "header")
    print_bantu("INCIDENT REPORT", "header")
    print_bantu(f"Time     : {analysis_start.strftime('%Y-%m-%d %H:%M:%S')}", "info")
    print_bantu(f"Device   : {fault['device']}", "info")
    print_bantu(f"Alert    : {fault['alert_type']}", "info")
    print_bantu(f"Duration : {duration} seconds to investigate", "info")
    print_bantu("=" * 60, "header")


# ---------------------------------------------------------------------------
# FAULT TRACKER
# Tracks known faults and their current status to avoid redundant work.
# Structure:
#   key: (alert_type, device) tuple
#   value: dict with keys:
#     status       — "investigating" | "playbook_generated" | "auto_fixed"
#     detected_at  — datetime when first detected
#     playbook     — path to generated playbook (HIGH severity only)
#     fix_commands — commands in the playbook for quick reference
# ---------------------------------------------------------------------------
fault_tracker = {}


def monitoring_loop():
    # ---------------------------------------------------------------------------
    # PURPOSE: Main always-on monitoring loop — runs indefinitely
    # USED BY: main() below
    # HOW IT WORKS:
    #   1. Run all health checks
    #   2. For each new fault found — trigger handle_fault() automatically
    #   3. Track active faults to avoid duplicate investigations
    #   4. Sleep POLL_INTERVAL seconds then repeat
    # OUTCOME: Bantu runs continuously — no manual intervention needed
    #          Faults are detected and handled automatically
    # ---------------------------------------------------------------------------
    print(f"""\033[96m
▛▀▖      ▐      BANTU MONITOR — Always-On Network Watch
▙▄▘▝▀▖▛▀▖▜▀ ▌ ▌ Network Automation, Endlessly Evolving
▌ ▌▞▀▌▌ ▌▐ ▖▌ ▌ Powered by Groq + Llama 3.3 70B
▀▀ ▝▀▘▘ ▘ ▀ ▝▀▘ Built by Tirupathi Rushi Vedulapurapu
\033[0m""")

    # Initial device health check before starting loop
    print_bantu("Running initial device health check...", "info")
    facts = get_all_device_facts()
    all_reachable = True
    for device, result in facts.items():
        if "error" in result:
            print_bantu(f"{device}: UNREACHABLE — {result['error']}", "error")
            all_reachable = False
        else:
            print_bantu(f"{device}: OK", "success")

    if not all_reachable:
        print_bantu("Some devices unreachable — check topology is running", "error")
        sys.exit(1)

    print_bantu("All devices reachable — starting monitoring loop", "success")
    print_bantu(f"Ctrl+C to stop\n", "info")

    poll_count = 0

    while True:
        poll_count += 1
        now = datetime.now().strftime("%H:%M:%S")
        print(f"""\033[96m
▛▀▖      ▐     
▙▄▘▝▀▖▛▀▖▜▀ ▌ ▌  BANTU MONITOR
▌ ▌▞▀▌▌ ▌▐ ▖▌ ▌  Interval: {POLL_INTERVAL}s · Devices: {", ".join(EXPECTED_STATE["interfaces"].keys())}
▀▀ ▝▀▘▘ ▘ ▀ ▝▀▘
\033[0m""")
        print(f"\033[96m{'─' * 20} Poll #{poll_count} · {now} {'─' * 20}\033[0m")

        # Run all health checks
        faults = run_health_checks()

        # Build set of currently active fault keys from this poll
        current_fault_keys = set()
        for f in faults:
            current_fault_keys.add((f["alert_type"], f["device"]))

        # Clear resolved faults from tracker
        # If a fault no longer appears in health checks it has been resolved
        resolved = [k for k in fault_tracker if k not in current_fault_keys]
        for k in resolved:
            entry = fault_tracker.pop(k)
            print_bantu(
                f"RESOLVED — {k[0]} on {k[1]} is no longer detected",
                "success"
            )

        if not faults:
            print_bantu(f"Poll #{poll_count} — all checks passed", "success")
        else:
            print_bantu(f"Poll #{poll_count} — {len(faults)} fault(s) detected", "warning")

            for fault in faults:
                fault_key = (fault["alert_type"], fault["device"])
                existing = fault_tracker.get(fault_key)

                if existing:
                    # ---------------------------------------------------------------------------
                    # KNOWN FAULT — already investigated this one
                    # Instead of re-investigating, just remind the engineer
                    # ---------------------------------------------------------------------------
                    status = existing["status"]

                    if status == "playbook_generated":
                        # HIGH severity — playbook already exists, remind engineer
                        print_bantu(
                            f"PENDING HUMAN ACTION — {fault['alert_type']} on {fault['device']}",
                            "warning"
                        )
                        print_bantu(
                            f"Playbook ready at: {existing['playbook']}",
                            "warning"
                        )
                        if existing.get("fix_commands"):
                            print_bantu(
                                f"Fix commands: {existing['fix_commands']}",
                                "warning"
                            )
                        print_bantu(
                            f"Run in a new terminal: ansible-playbook -i "
                            f"../../phase-04-ci-cd/ceos/ansible/inventory/inventory.yml "
                            f"{existing['playbook']}",
                            "warning"
                        )

                    elif status == "auto_fixed":
                        # LOW severity — was auto-fixed but fault is back
                        # This means the fix didn't hold — re-investigate
                        print_bantu(
                            f"FAULT RETURNED — {fault['alert_type']} on "
                            f"{fault['device']} reappeared after auto-fix",
                            "error"
                        )
                        fault_tracker.pop(fault_key)  # Remove so it re-investigates

                    continue

                # ---------------------------------------------------------------------------
                # NEW FAULT — not seen before, investigate now
                # ---------------------------------------------------------------------------
                print_bantu(
                    f"NEW FAULT DETECTED — {fault['alert_type']} on {fault['device']}",
                    "warning"
                )

                # Add to tracker as investigating
                fault_tracker[fault_key] = {
                    "status": "investigating",
                    "detected_at": datetime.now(),
                    "playbook": None,
                    "fix_commands": []
                }

                analysis_start = datetime.now()

                # Run investigation — capture result to check severity
                # We patch handle_fault to return analysis for tracking
                from agent.bantu import investigate_fault
                analysis = investigate_fault(
                    fault["alert_type"],
                    fault["device"],
                    fault.get("details", {})
                )

                severity = analysis.get("severity", "UNKNOWN")
                fault_type = analysis.get("fault_type", "unknown")
                fix_commands = analysis.get("fix_commands", [])

                # Map fault types same as bantu.py
                FAULT_TYPE_MAP = {
                    "bgp_down": "bgp_asn_mismatch",
                    "bgp_session_down": "bgp_asn_mismatch",
                    "bgp_neighbor_down": "bgp_asn_mismatch",
                    "interface_shutdown": "interface_down",
                    "link_down": "interface_down",
                    "ospf_down": "ospf_area_mismatch",
                    "ospf_neighbor_loss": "ospf_area_mismatch",
                    "acl_blocking": "acl_blocking_traffic",
                    "traffic_blocked": "acl_blocking_traffic",
                }
                fault_type = FAULT_TYPE_MAP.get(fault_type, fault_type)

                if severity == "LOW" and fix_commands and fault_type != "unknown":
                    # AUTO-FIX PATH
                    from agent.remediation import apply_fix, verify_fix
                    from agent.fault_definitions import get_fault
                    from tools.network_tools import get_interfaces
                    affected_device = analysis.get("affected_device", fault["device"])
                    affected_interface = analysis.get("affected_interface")

                    resolved_commands = [
                        cmd.replace("{interface}", affected_interface or "")
                        for cmd in fix_commands
                    ]

                    result = apply_fix(affected_device, resolved_commands)
                    if result["success"]:
                        print_bantu(f"AUTO-FIX APPLIED — {result['message']}", "success")
                        fault_tracker[fault_key]["status"] = "auto_fixed"
                    else:
                        print_bantu(f"AUTO-FIX FAILED — {result['message']}", "error")
                        fault_tracker[fault_key]["status"] = "playbook_generated"

                elif severity == "HIGH" and fault_type != "unknown":
                    # PLAYBOOK PATH
                    from agent.playbook_generator import generate_playbook
                    from agent.fault_definitions import get_fault
                    try:
                        fault_def = get_fault(fault_type)
                        playbook_path = generate_playbook(
                            fault_type=fault_type,
                            device=analysis.get("affected_device", fault["device"]),
                            description=fault_def["description"],
                            commands=fix_commands
                        )
                        fault_tracker[fault_key]["status"] = "playbook_generated"
                        fault_tracker[fault_key]["playbook"] = playbook_path
                        fault_tracker[fault_key]["fix_commands"] = fix_commands
                        print_bantu("=" * 60, "warning")
                        print_bantu("HUMAN ACTION REQUIRED", "warning")
                        print_bantu(f"Fault    : {fault_type}", "warning")
                        print_bantu(f"Device   : {analysis.get('affected_device', fault['device'])}", "warning")
                        print_bantu(f"Playbook : {playbook_path}", "warning")
                        print_bantu(f"Commands : {fix_commands}", "warning")
                        print_bantu(
                            f"Run in new terminal: ansible-playbook -i "
                            f"../../phase-04-ci-cd/ceos/ansible/inventory/inventory.yml "
                            f"{playbook_path}",
                            "warning"
                        )
                        print_bantu("=" * 60, "warning")
                    except Exception as e:
                        print_bantu(f"Playbook generation failed: {str(e)}", "error")
                        fault_tracker[fault_key]["status"] = "playbook_generated"
                else:
                    # Could not determine fault — keep tracking but don't re-investigate
                    fault_tracker[fault_key]["status"] = "playbook_generated"
                    fault_tracker[fault_key]["playbook"] = "Could not determine fix"

                analysis_end = datetime.now()
                print_incident_report(fault, analysis_start, analysis_end)

        # Wait before next poll
        print_bantu(f"Next poll in {POLL_INTERVAL} seconds...\n", "info")
        time.sleep(POLL_INTERVAL)


def main():
    try:
        monitoring_loop()
    except KeyboardInterrupt:
        print_bantu("\nMonitor stopped by user", "warning")
        sys.exit(0)


if __name__ == "__main__":
    main()
