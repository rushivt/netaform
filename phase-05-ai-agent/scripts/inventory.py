# Standard libraries only — no external dependencies needed for this helper
import yaml    # Parses the YAML inventory file into a Python dictionary
import os      # Builds file paths that work regardless of where the script is run from
import socket  # Resolves Docker DNS names (clab-netaform-p4-ceos-edge-1) to actual IPs

# ---------------------------------------------------------------------------
# INVENTORY_PATH
# Builds an absolute path to Phase 4's Ansible inventory file.
# We reuse Phase 4's inventory instead of duplicating it — single source of truth.
# __file__ = current script location
# os.path.dirname(__file__) = parent directory of this script
# os.path.join walks two levels up (../..)) into Phase 4's inventory directory
# Result: /home/rushi/netaform/phase-04-ci-cd/ceos/ansible/inventory/inventory.yml
# ---------------------------------------------------------------------------
INVENTORY_PATH = os.path.join(
    os.path.dirname(__file__),
    "../../phase-04-ci-cd/ceos/ansible/inventory/inventory.yml"
)

# ---------------------------------------------------------------------------
# NAPALM_DEVICES
# Defines how NAPALM should connect to each cEOS device.
# driver: "eos" tells NAPALM this is an Arista EOS device
# transport: "https" tells NAPALM to use eAPI over HTTPS (not SSH)
# port: 443 is where cEOS exposes eAPI — same as Phase 4 Ansible connection
# These settings are pulled later in get_napalm_config() to build connections
# ---------------------------------------------------------------------------
NAPALM_DEVICES = {
    "edge-1": {"driver": "eos", "optional_args": {"transport": "https", "port": 443}},
    "dist-1": {"driver": "eos", "optional_args": {"transport": "https", "port": 443}},
    "dist-2": {"driver": "eos", "optional_args": {"transport": "https", "port": 443}},
}

def get_device_ip(hostname):
    # ---------------------------------------------------------------------------
    # PURPOSE: Takes a device hostname like "edge-1" and returns its actual IP
    # USED BY: get_napalm_config() below — called every time a tool function
    #          needs to open a connection to a device
    # ---------------------------------------------------------------------------

    # Open and parse the Phase 4 inventory YAML into a Python dictionary
    with open(INVENTORY_PATH) as f:
        inv = yaml.safe_load(f)

    # Navigate the nested YAML structure to reach the eos_devices hosts section
    # Structure: all -> children -> eos_devices -> hosts -> {device: {ansible_host: ...}}
    eos = inv["all"]["children"]["eos_devices"]["hosts"]

    # Raise a clear error if the requested hostname doesn't exist in inventory
    # Prevents confusing KeyError crashes deeper in the code
    if hostname not in eos:
        raise ValueError(f"Device {hostname} not found in inventory")

    # Read the ansible_host value — this is the Docker DNS name
    # Example: clab-netaform-p4-ceos-edge-1
    dns_name = eos[hostname]["ansible_host"]

    # Resolve the Docker DNS name to an actual IP address
    # socket.gethostbyname() asks the OS DNS resolver to look up the name
    # This works because Docker registers container names in its internal DNS
    # If the topology is not running, DNS resolution fails and we raise a
    # helpful error instead of a confusing socket crash
    try:
        ip = socket.gethostbyname(dns_name)
        return ip  # Returns something like "172.20.20.3"
    except socket.gaierror:
        raise RuntimeError(f"Could not resolve {dns_name} — is the topology running?")


def get_napalm_config(hostname, username, password):
    # ---------------------------------------------------------------------------
    # PURPOSE: Builds a complete NAPALM connection dictionary for a given device
    # USED BY: Every tool function in scripts/tools/ that opens a NAPALM session
    # OUTCOME: Returns a dict that can be unpacked directly into a NAPALM driver
    #          Example usage in tool files:
    #          driver = napalm.get_network_driver("eos")
    #          device = driver(**get_napalm_config("edge-1", user, pass))
    # ---------------------------------------------------------------------------

    # Resolve the device's actual IP using the function above
    ip = get_device_ip(hostname)

    # Pull the NAPALM connection settings (transport, port) from NAPALM_DEVICES
    # If hostname somehow not in NAPALM_DEVICES, default to empty dict
    cfg = NAPALM_DEVICES.get(hostname, {})

    # Combine IP, credentials, and connection options into one clean dictionary
    # This dictionary is passed directly to the NAPALM driver constructor
    return {
        "hostname": ip,           # Resolved IP of the device
        "username": username,     # Passed in from the agent's credential config
        "password": password,     # Passed in from the agent's credential config
        "optional_args": cfg.get("optional_args", {}),  # transport + port settings
    }


def get_all_devices():
    # ---------------------------------------------------------------------------
    # PURPOSE: Returns a list of all device names Bantu knows about
    # USED BY: Agent startup health check — scans all devices at once
    # OUTCOME: Returns ["edge-1", "dist-1", "dist-2"]
    # ---------------------------------------------------------------------------
    return list(NAPALM_DEVICES.keys())
