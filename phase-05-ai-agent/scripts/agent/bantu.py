import os
import sys
import json
from datetime import datetime
from dotenv import load_dotenv
from colorama import Fore, Style, init

# Initialize colorama for colored terminal output
# autoreset=True means color resets after every print automatically
init(autoreset=True)

# ---------------------------------------------------------------------------
# LOAD ENVIRONMENT VARIABLES
# Reads .env file and loads GROQ_API_KEY, DEVICE_USERNAME, DEVICE_PASSWORD
# into os.environ so all modules can access them via os.environ.get()
# Must be called before importing any module that reads environment variables
# ---------------------------------------------------------------------------
load_dotenv(os.path.join(os.path.dirname(__file__), "../../.env"))

# Add scripts directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ---------------------------------------------------------------------------
# IMPORTS
# All imports after load_dotenv() so environment variables are available
# when these modules initialize
# ---------------------------------------------------------------------------
from tools.network_tools import (
    get_bgp_neighbors,
    get_interfaces,
    get_ospf_neighbors,
    get_arp_table,
    get_route_table,
    get_device_facts,
    get_ospf_config,
    get_static_routes,
    ping_device,
    get_all_device_facts
)
from agent.groq_client import ask_bantu, build_alert_message
from agent.playbook_generator import generate_playbook
from agent.remediation import apply_fix, verify_fix
from agent.fault_definitions import get_fault, get_all_faults

# ---------------------------------------------------------------------------
# TOOL REGISTRY
# Maps tool name strings (what the LLM requests) to actual Python functions
# When Bantu's LLM response says {"tool": "get_bgp_neighbors", "args": {...}}
# we look up the function here and call it with the provided args
# This is the core of the tool-calling pattern — LLM decides, Python executes
# ---------------------------------------------------------------------------
TOOL_REGISTRY = {
    "get_bgp_neighbors": get_bgp_neighbors,
    "get_interfaces": get_interfaces,
    "get_ospf_neighbors": get_ospf_neighbors,
    "get_arp_table": get_arp_table,
    "get_route_table": get_route_table,
    "get_device_facts": get_device_facts,
    "ping_device": ping_device,
    "get_ospf_config": get_ospf_config,
    "get_static_routes": get_static_routes,
}


def print_bantu(message, level="info"):
    # ---------------------------------------------------------------------------
    # PURPOSE: Prints formatted, colored output to the terminal
    # USED BY: Throughout bantu.py for all terminal output
    # PARAMETERS:
    #   message — text to print
    #   level   — controls color: info=cyan, success=green, warning=yellow,
    #             error=red, header=magenta
    # OUTCOME: Prints "[Bantu] message" with appropriate color
    # ---------------------------------------------------------------------------
    colors = {
        "info":    Fore.CYAN,
        "success": Fore.GREEN,
        "warning": Fore.YELLOW,
        "error":   Fore.RED,
        "header":  Fore.MAGENTA
    }
    color = colors.get(level, Fore.WHITE)
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"{color}[Bantu {timestamp}] {message}{Style.RESET_ALL}")


def execute_tool_calls(tool_calls):
    # ---------------------------------------------------------------------------
    # PURPOSE: Executes the list of tool calls requested by the LLM response
    # USED BY: investigate_fault() below after each LLM response
    # PARAMETERS:
    #   tool_calls — list of dicts from LLM response e.g.
    #                [{"tool": "get_bgp_neighbors", "args": {"hostname": "edge-1"}}]
    # HOW IT WORKS:
    #   Loops through each requested tool call, looks up the function in
    #   TOOL_REGISTRY, calls it with the provided args, and collects results.
    #   Results are returned as a dict keyed by tool name for easy reference.
    # OUTCOME: Returns dict of {tool_name: result} for all executed tool calls
    # ---------------------------------------------------------------------------
    results = {}
    for call in tool_calls:
        tool_name = call.get("tool")
        args = call.get("args", {})

        if tool_name not in TOOL_REGISTRY:
            # LLM requested a tool that doesn't exist — log warning and skip
            print_bantu(f"Unknown tool requested: {tool_name}", "warning")
            results[tool_name] = {"error": f"Tool {tool_name} not found"}
            continue

        print_bantu(f"Calling tool: {tool_name}({args})", "info")
        try:
            # Look up function in registry and call it with unpacked args dict
            # **args unpacks {"hostname": "edge-1"} into hostname="edge-1"
            fn = TOOL_REGISTRY[tool_name]
            results[tool_name] = fn(**args)
            print_bantu(f"Tool {tool_name} completed", "success")
        except Exception as e:
            print_bantu(f"Tool {tool_name} failed: {str(e)}", "error")
            results[tool_name] = {"error": str(e)}

    return results


def investigate_fault(alert_type, device, details):
    # ---------------------------------------------------------------------------
    # PURPOSE: Core investigation loop — sends alert to LLM, executes tool calls,
    #          feeds results back to LLM, repeats until conclusion reached
    # USED BY: handle_fault() below
    # PARAMETERS:
    #   alert_type — type of alert e.g. "bgp_down", "interface_down"
    #   device     — affected device e.g. "edge-1"
    #   details    — additional context dict e.g. {"neighbor": "203.0.113.1"}
    # HOW THE LOOP WORKS:
    #   1. Format alert as user message and send to LLM
    #   2. LLM responds with reasoning + tool calls it wants to make
    #   3. We execute those tool calls against real devices
    #   4. We send tool results back to LLM as next user message
    #   5. LLM analyzes results and either calls more tools or concludes
    #   6. Loop ends when LLM provides fault_type and root_cause
    # MAX ITERATIONS: 5 — prevents infinite loops if LLM keeps requesting tools
    # OUTCOME: Returns the final LLM analysis dict with fault_type, severity,
    #          root_cause, fix_commands etc.
    # ---------------------------------------------------------------------------
    print_bantu(f"Starting investigation — alert: {alert_type} on {device}", "header")

    # Conversation history — maintained in Python since LLM has no memory
    # Every message sent and received is appended here and sent with next call
    messages = []

    # Format the initial alert as the first user message
    alert_message = build_alert_message(alert_type, device, details)
    messages.append({"role": "user", "content": alert_message})

    # Investigation loop — maximum 5 iterations
    max_iterations = 5
    final_analysis = None

    for iteration in range(max_iterations):
        print_bantu(f"Investigation iteration {iteration + 1}/{max_iterations}", "info")

        # Send current conversation to Groq and get Bantu's response
        response = ask_bantu(messages)

        # Print Bantu's reasoning so engineer can follow the investigation
        print_bantu(f"Reasoning: {response.get('reasoning', 'No reasoning provided')}", "info")

        # Append LLM response to conversation history as assistant message
        messages.append({
            "role": "assistant",
            "content": json.dumps(response)
        })

        # Check if LLM has reached a conclusion
        # A conclusion means fault_type is known and root_cause is identified
        fault_type = response.get("fault_type", "unknown")
        if fault_type != "unknown" and response.get("root_cause"):
            print_bantu(f"Root cause identified: {response['root_cause']}", "success")
            final_analysis = response
            break

        # LLM requested tool calls — execute them and feed results back
        tool_calls = response.get("tool_calls", [])
        if tool_calls:
            tool_results = execute_tool_calls(tool_calls)

            # Format tool results as next user message
            # Sending results back continues the investigation conversation
            results_message = (
                f"Tool execution results:\n"
                f"{json.dumps(tool_results, indent=2, default=str)}\n\n"
                f"Based on these results, continue your investigation and "
                f"provide your updated analysis."
            )
            messages.append({"role": "user", "content": results_message})
        else:
            # LLM gave no tool calls and no conclusion — unusual, break loop
            print_bantu("No tool calls and no conclusion — ending investigation", "warning")
            final_analysis = response
            break

    # If loop exhausted without conclusion, use last response as final analysis
    if not final_analysis:
        print_bantu("Max iterations reached — using best available analysis", "warning")
        final_analysis = response

    return final_analysis


def handle_fault(alert_type, device, details=None):
    # ---------------------------------------------------------------------------
    # PURPOSE: Top level fault handler — orchestrates full Bantu workflow
    #          from alert receipt to resolution
    # USED BY: inject_fault() below and can be called directly for real alerts
    # PARAMETERS:
    #   alert_type — type of alert e.g. "bgp_down"
    #   device     — affected device e.g. "edge-1"
    #   details    — optional additional context dict
    # WORKFLOW:
    #   1. Run investigation loop to get LLM analysis
    #   2. Check severity from analysis
    #   3. LOW severity → auto-fix with Netmiko → verify fix → log result
    #   4. HIGH severity → generate Ansible playbook → save to file → notify engineer
    # OUTCOME: Prints full investigation and resolution to terminal
    #          For HIGH severity, saves playbook to playbooks/remediation/
    # ---------------------------------------------------------------------------
    if details is None:
        details = {}

    print_bantu("=" * 60, "header")
    print_bantu(f"BANTU ACTIVATED — {alert_type.upper()} on {device}", "header")
    print_bantu("=" * 60, "header")

    # Run the investigation loop
    analysis = investigate_fault(alert_type, device, details)

    # Extract key fields from analysis
    # Map LLM fault names to our defined fault types
    # The LLM sometimes uses different names than our definitions
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
    raw_fault_type = analysis.get("fault_type", "unknown")
    fault_type = FAULT_TYPE_MAP.get(raw_fault_type, raw_fault_type)
    severity = analysis.get("severity", "UNKNOWN")
    root_cause = analysis.get("root_cause", "Unknown")
    fix_commands = analysis.get("fix_commands", [])
    affected_device = analysis.get("affected_device", device)
    affected_interface = analysis.get("affected_interface")
    confidence = analysis.get("confidence", "LOW")

    # Print investigation summary
    print_bantu("=" * 60, "header")
    print_bantu("INVESTIGATION SUMMARY", "header")
    print_bantu(f"Fault Type  : {fault_type}", "info")
    print_bantu(f"Severity    : {severity}", "warning" if severity == "HIGH" else "success")
    print_bantu(f"Root Cause  : {root_cause}", "info")
    print_bantu(f"Confidence  : {confidence}", "info")
    print_bantu(f"Fix Commands: {fix_commands}", "info")
    print_bantu("=" * 60, "header")

    if fault_type == "unknown" or not fix_commands:
        print_bantu("Could not determine fault or fix — manual investigation required", "error")
        return

    # ---------------------------------------------------------------------------
    # SEVERITY ROUTING
    # LOW  → auto-fix path: apply fix directly, verify, log result
    # HIGH → playbook path: generate Ansible playbook, save, notify engineer
    # ---------------------------------------------------------------------------
    if severity == "LOW":
        print_bantu(f"Severity LOW — applying auto-fix to {affected_device}", "success")

        # Substitute interface name into fix commands if needed
        # Replaces {interface} placeholder with actual interface name from analysis
        resolved_commands = [
            cmd.replace("{interface}", affected_interface or "")
            for cmd in fix_commands
        ]

        # Apply the fix via Netmiko
        result = apply_fix(affected_device, resolved_commands)

        if result["success"]:
            print_bantu(f"Auto-fix applied: {result['message']}", "success")

            # Verify the fix worked by calling the verify tool function
            # Look up the fault definition to find which tool verifies this fault
            try:
                fault_def = get_fault(fault_type)
                verify_tool_name = fault_def["verify_fn"]
                verify_fn = TOOL_REGISTRY[verify_tool_name]
                print_bantu(f"Verifying fix with {verify_tool_name}...", "info")
                verification = verify_fix(verify_fn, affected_device)
                print_bantu(f"Verification result: {json.dumps(verification, indent=2, default=str)}", "success")
            except Exception as e:
                print_bantu(f"Verification failed: {str(e)}", "warning")
        else:
            print_bantu(f"Auto-fix failed: {result['message']}", "error")
            print_bantu("Escalating to playbook generation for manual review", "warning")
            severity = "HIGH"  # Escalate to HIGH if auto-fix fails

    if severity == "HIGH":
        print_bantu(f"Severity HIGH — generating remediation playbook", "warning")

        # Generate the Ansible remediation playbook using the Jinja2 template
        try:
            fault_def = get_fault(fault_type)
            playbook_path = generate_playbook(
                fault_type=fault_type,
                device=affected_device,
                description=fault_def["description"],
                commands=fix_commands
            )
            print_bantu("=" * 60, "warning")
            print_bantu("HUMAN REVIEW REQUIRED", "warning")
            print_bantu(f"Playbook saved to: {playbook_path}", "warning")
            print_bantu("Review the playbook carefully before running", "warning")
            print_bantu(f"Run with: ansible-playbook -i <inventory> {playbook_path}", "warning")
            print_bantu("=" * 60, "warning")
        except Exception as e:
            print_bantu(f"Playbook generation failed: {str(e)}", "error")


def startup_health_check():
    # ---------------------------------------------------------------------------
    # PURPOSE: Runs at Bantu startup to confirm all devices are reachable
    # USED BY: main() below before running any fault scenarios
    # HOW IT WORKS:
    #   Calls get_all_device_facts() which tries to connect to every device
    #   and returns either facts or an error message per device
    # OUTCOME: Prints health status for each device
    #          Returns True if all devices reachable, False if any unreachable
    # ---------------------------------------------------------------------------
    print_bantu("Running startup health check...", "header")
    results = get_all_device_facts()
    all_healthy = True

    for device, result in results.items():
        if "error" in result:
            print_bantu(f"{device}: UNREACHABLE — {result['error']}", "error")
            all_healthy = False
        else:
            print_bantu(f"{device}: OK — {result.get('os_version', 'unknown version')}", "success")

    return all_healthy


def inject_fault(scenario):
    # ---------------------------------------------------------------------------
    # PURPOSE: Simulates receiving an alert for a specific fault scenario
    # USED BY: main() below for demo and testing
    # PARAMETERS:
    #   scenario — string name of the fault scenario to simulate
    # NOTE: In a real deployment, alerts would come from monitoring systems
    #       like Grafana, PagerDuty, or a custom webhook. For the portfolio
    #       demo we inject them manually via this function.
    # SCENARIOS:
    #   "interface_down"     — Ethernet1 on edge-1 is shut down
    #   "bgp_asn_mismatch"   — BGP ASN on edge-1 is wrong
    #   "acl_blocking"       — ACL blocking traffic from Engineering to Servers
    #   "ospf_area_mismatch" — OSPF area mismatch on dist-1
    # ---------------------------------------------------------------------------
    scenarios = {
        "interface_down": {
            "alert_type": "interface_down",
            "device": "edge-1",
            "details": {
                "interface": "Ethernet1",
                "description": "Link to dist-1 went down",
                "last_change": "2 minutes ago"
            }
        },
        "bgp_asn_mismatch": {
            "alert_type": "bgp_down",
            "device": "edge-1",
            "details": {
                "neighbor": "203.0.113.1",
                "expected_state": "established",
                "current_state": "idle",
                "last_change": "5 minutes ago"
            }
        },
        "acl_blocking": {
            "alert_type": "reachability_failure",
            "device": "dist-1",
            "details": {
                "source": "10.0.10.100",
                "destination": "10.0.30.100",
                "description": "Engineering hosts cannot reach Server VLAN — suspected route blackhole"
            }
        },
        "ospf_area_mismatch": {
            "alert_type": "ospf_neighbor_down",
            "device": "dist-1",
            "details": {
                "neighbor": "edge-1",
                "expected_area": "0.0.0.0",
                "description": "OSPF adjacency lost with edge-1"
            }
        }
    }

    if scenario not in scenarios:
        print_bantu(f"Unknown scenario: {scenario}", "error")
        print_bantu(f"Available: {list(scenarios.keys())}", "info")
        return

    s = scenarios[scenario]
    handle_fault(s["alert_type"], s["device"], s["details"])


def main():
    # ---------------------------------------------------------------------------
    # PURPOSE: Entry point for Bantu — runs startup check then demo scenarios
    # USED BY: Running "python bantu.py" from the command line
    # FLOW:
    #   1. Print Bantu banner
    #   2. Run startup health check — abort if devices unreachable
    #   3. Print available fault scenarios
    #   4. Ask user which scenario to run
    #   5. Run selected scenario
    # ---------------------------------------------------------------------------
    print_bantu("=" * 60, "header")
    print_bantu("BANTU — AI Network Troubleshooting Agent", "header")
    print_bantu("Powered by Groq + Llama 3.3 70B", "header")
    print_bantu("=" * 60, "header")

    # Run health check first — no point investigating if devices are down
    healthy = startup_health_check()
    if not healthy:
        print_bantu("One or more devices unreachable — check topology is running", "error")
        print_bantu("Run: sudo containerlab deploy -t topology/topology.clab.yml", "info")
        sys.exit(1)

    print_bantu("All devices healthy — Bantu ready", "success")
    print_bantu(f"Known fault scenarios: {get_all_faults()}", "info")

    # Prompt user to select a scenario
    print("\nAvailable scenarios:")
    print("  1. interface_down")
    print("  2. bgp_asn_mismatch")
    print("  3. acl_blocking")
    print("  4. ospf_area_mismatch")
    print()

    choice = input("Enter scenario (interface_down, bgp_asn_mismatch, acl_blocking, ospf_area_mismatch): ").strip()
    inject_fault(choice)


if __name__ == "__main__":
    main()
