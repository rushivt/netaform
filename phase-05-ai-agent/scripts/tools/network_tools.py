import napalm
import os
import sys

# Add the scripts directory to path so we can import inventory.py
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from inventory import get_napalm_config, get_all_devices

# ---------------------------------------------------------------------------
# CREDENTIALS
# Read from environment variables set in .env file
# Never hardcoded — loaded at runtime
# ---------------------------------------------------------------------------
USERNAME = os.environ.get("DEVICE_USERNAME", "admin")
PASSWORD = os.environ.get("DEVICE_PASSWORD", "admin")


def _get_device(hostname):
    # ---------------------------------------------------------------------------
    # PURPOSE: Opens and returns a connected NAPALM device session
    # USED BY: Every tool function below — private helper, not called by agent
    # OUTCOME: Returns an open NAPALM EOS driver instance ready for getters
    # NOTE: Caller is responsible for calling device.close() after use
    # ---------------------------------------------------------------------------
    driver = napalm.get_network_driver("eos")
    config = get_napalm_config(hostname, USERNAME, PASSWORD)
    device = driver(**config)
    device.open()
    return device


def get_bgp_neighbors(hostname):
    # ---------------------------------------------------------------------------
    # PURPOSE: Fetches BGP neighbor state for a device
    # USED BY: Bantu when it receives a BGP-related alert
    # REFERENCES: _get_device() for connection, NAPALM get_bgp_neighbors() getter
    # OUTCOME: Returns a dict of BGP peers and their up/down state
    # Example return:
    # {
    #   "global": {
    #     "peers": {
    #       "203.0.113.1": {"is_up": False, "remote_as": 65000}
    #     }
    #   }
    # }
    # ---------------------------------------------------------------------------
    device = _get_device(hostname)
    try:
        return device.get_bgp_neighbors()
    finally:
        # finally block ensures device.close() always runs even if getter fails
        device.close()


def get_interfaces(hostname):
    # ---------------------------------------------------------------------------
    # PURPOSE: Fetches interface state for all interfaces on a device
    # USED BY: Bantu when investigating why BGP or OSPF is down
    #          An interface being down is often the root cause
    # REFERENCES: _get_device(), NAPALM get_interfaces() getter
    # OUTCOME: Returns dict of interfaces with is_up, is_enabled, speed, description
    # Example return:
    # {
    #   "Ethernet1": {"is_up": False, "is_enabled": False, "description": ""}
    # }
    # ---------------------------------------------------------------------------
    device = _get_device(hostname)
    try:
        return device.get_interfaces()
    finally:
        device.close()


def get_ospf_neighbors(hostname):
    # ---------------------------------------------------------------------------
    # PURPOSE: Fetches OSPF neighbor state for a device
    # USED BY: Bantu when investigating routing or reachability issues
    # REFERENCES: _get_device(), NAPALM get_network_instances() getter
    # NOTE: NAPALM does not have a dedicated get_ospf_neighbors() getter.
    #       We use get_network_instances() which returns routing protocol state
    #       including OSPF neighbors in the default VRF
    # OUTCOME: Returns network instance data containing OSPF neighbor info
    # ---------------------------------------------------------------------------
    device = _get_device(hostname)
    try:
        return device.get_network_instances()
    finally:
        device.close()


def get_arp_table(hostname):
    # ---------------------------------------------------------------------------
    # PURPOSE: Fetches the ARP table of a device
    # USED BY: Bantu when investigating Layer 3 reachability issues
    # REFERENCES: _get_device(), NAPALM get_arp_table() getter
    # OUTCOME: Returns list of ARP entries with IP, MAC, and interface
    # Example return:
    # [{"ip": "10.0.0.1", "mac": "aa:bb:cc:dd:ee:ff", "interface": "Ethernet1"}]
    # ---------------------------------------------------------------------------
    device = _get_device(hostname)
    try:
        return device.get_arp_table()
    finally:
        device.close()


def get_route_table(hostname):
    # ---------------------------------------------------------------------------
    # PURPOSE: Fetches the routing table of a device
    # USED BY: Bantu when investigating reachability or route missing issues
    # REFERENCES: _get_device(), NAPALM get_route_to() getter with default route
    #             "0.0.0.0/0" returns all routes in the table
    # OUTCOME: Returns dict of all routes with next-hop and protocol info
    # ---------------------------------------------------------------------------
    device = _get_device(hostname)
    try:
        return device.get_route_to("0.0.0.0/0")
    finally:
        device.close()


def get_device_facts(hostname):
    # ---------------------------------------------------------------------------
    # PURPOSE: Fetches basic device facts — uptime, model, OS version, hostname
    # USED BY: Bantu at startup during health check of all devices
    # REFERENCES: _get_device(), NAPALM get_facts() getter
    # OUTCOME: Returns dict with vendor, model, os_version, uptime, hostname
    # Example return:
    # {"vendor": "Arista", "model": "cEOSLab", "os_version": "4.28.0F"}
    # ---------------------------------------------------------------------------
    device = _get_device(hostname)
    try:
        return device.get_facts()
    finally:
        device.close()


def ping_device(hostname, destination):
    # ---------------------------------------------------------------------------
    # PURPOSE: Runs a ping from a device to a destination IP
    # USED BY: Bantu to verify reachability after diagnosing a fault
    #          Also used to verify fix worked after auto-remediation
    # REFERENCES: _get_device(), NAPALM ping() method
    # NOTE: cEOS requires a source address for ping — we use the device's
    #       loopback0 address as source since it's always available
    # OUTCOME: Returns dict with success/failure and packet loss percentage
    # Example return:
    # {"success": {"packet_loss": 0, "rtt_avg": 1.2}}
    # ---------------------------------------------------------------------------
    device = _get_device(hostname)
    try:
        # Use count=3 for quick results, source loopback ensures ping works
        # even when the outgoing interface has no IP in that subnet
        return device.ping(destination, count=3, source="Loopback0")
    finally:
        device.close()


def get_all_device_facts():
    # ---------------------------------------------------------------------------
    # PURPOSE: Runs get_device_facts() across all devices in the inventory
    # USED BY: Bantu at startup to confirm all devices are reachable
    #          If a device is unreachable here, Bantu warns before proceeding
    # REFERENCES: get_all_devices() from inventory.py, get_device_facts() above
    # OUTCOME: Returns dict of {hostname: facts} for all devices
    #          If a device is unreachable, stores the error message instead
    # ---------------------------------------------------------------------------
    results = {}
    for device in get_all_devices():
        try:
            results[device] = get_device_facts(device)
        except Exception as e:
            # Store error string instead of crashing — Bantu handles the warning
            results[device] = {"error": str(e)}
    return results


def get_ospf_config(hostname):
    # ---------------------------------------------------------------------------
    # PURPOSE: Fetches OSPF configuration and neighbor state via direct CLI
    # USED BY: Bantu when investigating OSPF neighbor loss
    # WHY: NAPALM's get_network_instances() does not clearly expose OSPF area
    #      configuration. This function uses NAPALM's cli() method to run
    #      actual EOS show commands and return structured text output that
    #      the LLM can read and reason about directly.
    # COMMANDS RUN:
    #   - show ip ospf neighbor — current neighbor adjacencies and states
    #   - show ip ospf — OSPF process config including router-id and areas
    # OUTCOME: Returns dict with neighbor state and ospf process config
    #          as raw CLI text — LLM reads this to identify area mismatches
    # ---------------------------------------------------------------------------
    device = _get_device(hostname)
    try:
        output = device.cli([
            "show ip ospf neighbor",
            "show ip ospf"
        ])
        return {
            "ospf_neighbors": output.get("show ip ospf neighbor", ""),
            "ospf_process":   output.get("show ip ospf", "")
        }
    finally:
        device.close()


def get_static_routes(hostname):
    # ---------------------------------------------------------------------------
    # PURPOSE: Fetches static routes configured on a device via direct CLI
    # USED BY: Bantu when investigating reachability failures
    # WHY: get_route_table() uses NAPALM's get_route_to("0.0.0.0/0") which
    #      returns all routes but the output is large and the LLM misses
    #      specific static blackhole entries. This tool runs "show ip route static"
    #      which clearly shows only static routes including Null0 blackholes.
    # OUTCOME: Returns dict with static route CLI output — LLM reads this
    #          to identify unexpected blackhole routes
    # ---------------------------------------------------------------------------
    device = _get_device(hostname)
    try:
        output = device.cli(["show ip route static"])
        return {"static_routes": output.get("show ip route static", "")}
    finally:
        device.close()
