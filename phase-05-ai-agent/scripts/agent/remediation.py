import netmiko
import os
import sys

# Add scripts directory to path so we can import inventory.py
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from inventory import get_device_ip

# ---------------------------------------------------------------------------
# CREDENTIALS
# Same credentials used by network_tools.py — read from environment variables
# Both NAPALM (for querying) and Netmiko (for fixing) use the same creds
# ---------------------------------------------------------------------------
USERNAME = os.environ.get("DEVICE_USERNAME", "admin")
PASSWORD = os.environ.get("DEVICE_PASSWORD", "admin")


def _get_netmiko_connection(hostname):
    # ---------------------------------------------------------------------------
    # PURPOSE: Opens and returns a Netmiko SSH connection to a device
    # USED BY: apply_fix() below — private helper, not called directly
    # WHY NETMIKO HERE INSTEAD OF NAPALM:
    #   NAPALM is great for reading state (getters) but for sending config
    #   commands Netmiko gives us more direct control. We can send any EOS
    #   CLI command and read the output immediately.
    # OUTCOME: Returns an open Netmiko ConnectHandler instance
    # ---------------------------------------------------------------------------
    ip = get_device_ip(hostname)
    return netmiko.ConnectHandler(
        device_type="arista_eos",  # Netmiko device type for Arista EOS
        host=ip,                   # Resolved IP from inventory
        username=USERNAME,
        password=PASSWORD,
    )


def apply_fix(hostname, commands):
    # ---------------------------------------------------------------------------
    # PURPOSE: Sends a list of EOS CLI commands to a device to fix a LOW
    #          severity fault — this is Bantu's auto-remediation capability
    # USED BY: bantu.py when fault severity is LOW
    # PARAMETERS:
    #   hostname — device to fix e.g. "edge-1"
    #   commands — list of EOS CLI commands to send e.g.
    #              ["interface Ethernet1", "no shutdown"]
    # HOW IT WORKS:
    #   Netmiko sends commands one by one over SSH in config mode
    #   send_config_set() automatically enters "configure terminal" before
    #   sending commands and exits config mode after — we don't need to
    #   manually type "configure terminal" in the commands list
    # OUTCOME: Returns dict with success status and device output
    #          bantu.py uses this to confirm fix was applied and log the result
    # ---------------------------------------------------------------------------
    connection = None
    try:
        # Open SSH connection to the device
        connection = _get_netmiko_connection(hostname)

        # Send all commands in config mode
        # send_config_set() enters configure terminal, sends each command
        # in order, then exits config mode automatically
        output = connection.send_config_set(commands)

        # Save the running config to startup config so fix survives a reboot
        # send_command() sends a single exec mode command (not config mode)
        connection.send_command("write memory")

        return {
            "success": True,
            "output": output,
            "message": f"Fix applied successfully to {hostname}"
        }

    except Exception as e:
        # If anything goes wrong during fix application, return failure dict
        # bantu.py will log this and escalate to human review instead
        return {
            "success": False,
            "output": str(e),
            "message": f"Failed to apply fix to {hostname}: {str(e)}"
        }

    finally:
        # Always close the SSH connection whether fix succeeded or failed
        # Leaving connections open causes resource leaks on the device
        if connection:
            connection.disconnect()


def verify_fix(tool_fn, hostname, **kwargs):
    # ---------------------------------------------------------------------------
    # PURPOSE: Calls a NAPALM tool function after fix to confirm fault is resolved
    # USED BY: bantu.py after apply_fix() completes on LOW severity faults
    # PARAMETERS:
    #   tool_fn  — the actual function object to call e.g. get_interfaces
    #   hostname — device to verify against
    #   **kwargs — any extra args the tool function needs e.g. destination IP
    #              for ping_device
    # WHY THIS APPROACH:
    #   Instead of hardcoding verification logic per fault type, we pass the
    #   tool function itself as a parameter. bantu.py looks up verify_fn from
    #   fault_definitions.py and passes the corresponding function object here.
    #   This keeps verification generic and reusable across all fault types.
    # OUTCOME: Returns the raw tool function result — bantu.py interprets
    #          whether the result confirms the fix worked
    # ---------------------------------------------------------------------------
    try:
        return tool_fn(hostname, **kwargs)
    except Exception as e:
        return {"error": f"Verification failed: {str(e)}"}
