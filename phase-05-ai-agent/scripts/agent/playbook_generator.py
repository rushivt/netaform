import os
import jinja2
from datetime import datetime

# ---------------------------------------------------------------------------
# TEMPLATE_PATH
# Points to the Jinja2 template we created in playbooks/remediation_template.j2
# Uses __file__ to build an absolute path so it works from any working directory
# ---------------------------------------------------------------------------
TEMPLATE_PATH = os.path.join(
    os.path.dirname(__file__),
    "../../playbooks/remediation_template.j2"
)

# ---------------------------------------------------------------------------
# OUTPUT_DIR
# Where generated playbooks are saved
# This directory is gitignored — generated files are never committed
# Each playbook is named {fault_type}_{device}.yml for easy identification
# ---------------------------------------------------------------------------
OUTPUT_DIR = os.path.join(
    os.path.dirname(__file__),
    "../../playbooks/remediation"
)


def generate_playbook(fault_type, device, description, commands):
    # ---------------------------------------------------------------------------
    # PURPOSE: Fills the Jinja2 template with fault details and saves the result
    #          as a valid Ansible playbook file
    # USED BY: scripts/agent/bantu.py when fault severity is HIGH
    # PARAMETERS:
    #   fault_type  — short identifier for the fault e.g. "bgp_asn_mismatch"
    #   device      — hostname of the affected device e.g. "edge-1"
    #   description — human readable fault description for the playbook header
    #   commands    — list of EOS CLI commands that fix the fault
    #                 e.g. ["router bgp 65001", "neighbor 203.0.113.1 remote-as 65000"]
    # OUTCOME: Saves a .yml playbook to playbooks/remediation/ and returns
    #          the full path so Bantu can tell the engineer where to find it
    # ---------------------------------------------------------------------------

    # Load the Jinja2 template from the filesystem
    # jinja2.FileSystemLoader reads template files from a directory
    # jinja2.Environment is the rendering engine that processes {{ variables }}
    template_dir = os.path.dirname(TEMPLATE_PATH)
    template_file = os.path.basename(TEMPLATE_PATH)
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(template_dir),
        # trim_blocks removes newline after block tags like {% for %}
        # lstrip_blocks removes leading whitespace before block tags
        # Both make the generated YAML cleaner and properly indented
        trim_blocks=True,
        lstrip_blocks=True
    )
    template = env.get_template(template_file)

    # Render the template by injecting all variables
    # datetime.now() gives the current timestamp for the playbook header
    rendered = template.render(
        fault_type=fault_type,
        device=device,
        description=description,
        commands=commands,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

    # Build the output file path and save the rendered playbook
    # Filename pattern: {fault_type}_{device}.yml
    # Example: bgp_asn_mismatch_edge-1.yml
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, f"{fault_type}_{device}.yml")
    with open(output_path, "w") as f:
        f.write(rendered)

    # Return the path so Bantu can print it for the engineer
    return output_path
