<p align="center">
  <img src="../netaform-logo.png" alt="Netaform Logo" width="600">
</p>

# Phase 2: Automating the Branch with Ansible

## Scenario

The branch office from Phase 1 works — but every device was configured by hand. If the lab is destroyed and redeployed, someone has to log into each switch and re-enter every command. Phase 2 eliminates that. The entire network is now provisioned by Ansible — from bare containers to a fully routed, validated network with a single command.

## What Changed from Phase 1

- Host IP configuration moved from Containerlab `exec` blocks to Ansible — Ansible is now the sole source of truth for host addressing
- A bootstrap script handles cEOS eAPI and credential setup (cEOS does not persist `management api http-commands` from startup-config in Containerlab)

## Interview with Bitt

<table>
<tr>
<td width="120" align="center">
<img src="../bitt.png" alt="Bitt" width="100">
</td>
<td>
Ansible showed up promising zero-touch automation. Bitt has opinions about that — especially after the eAPI saga, the bootstrap script that needed three revisions, and twenty directories for three switches. In this interview, Bitt sits down with Ansible herself to hash it out.
<br><br>
📖 <a href="docs/conversations/bitt-ansible-automation.md">Bitt sits down with Ansible</a>
</td>
</tr>
</table>

## Tools Used

| Tool                  | Purpose                                         |
| --------------------- | ----------------------------------------------- |
| Ansible 2.17          | Configuration management and orchestration      |
| arista.eos collection | Ansible modules for Arista EOS devices          |
| Jinja2                | Templating engine for generating device configs |
| GNU Make              | Command shortcuts for deployment workflow       |

## How It Works

Ansible connects to the three cEOS switches (edge-1, dist-1, dist-2) over eAPI (HTTPS) and to the three alpine hosts via Docker connection. It applies five roles in order:

| Role       | What It Does                                                 |
| ---------- | ------------------------------------------------------------ |
| base       | Hostname, DNS, NTP, login banner, eAPI                       |
| interfaces | VLANs, routed interfaces, access ports, SVIs, loopbacks      |
| routing    | OSPF on all switches, BGP on edge-1 only                     |
| security   | Management access-list                                       |
| validate   | Runs show commands to verify OSPF, BGP, and interface status |

A separate playbook configures the alpine hosts with IP addresses and default gateways.

## Quick Start

```bash
# Deploy the Containerlab topology
make deploy

# Bootstrap eAPI + credentials, configure all devices
make all

# Validate network health only
make validate

# Destroy, redeploy, and configure from scratch
make redeploy

# Tear down the lab
make clean
```

## Bootstrap

cEOS in Containerlab does not persist management API configuration from startup-config. The bootstrap script solves this in three phases:

1. **Wait for CLI** — polls each device until `show version` responds
2. **Configure** — creates the admin user, enables AAA, and turns on eAPI
3. **Wait for eAPI** — polls each device's HTTPS endpoint until it responds

Only after all three phases complete does Ansible take over.

## Project Structure

```
phase-02-ansible-automation/
├── ansible.cfg              # Connection timeouts, inventory path
├── bootstrap.sh             # Pre-Ansible device bootstrapping
├── Makefile                 # Command shortcuts
├── network.yml              # Playbook for cEOS switches
├── hosts.yml                # Playbook for alpine hosts
├── inventory/
│   └── inventory.yml        # Device inventory with container names
├── group_vars/
│   ├── all/
│   │   └── common.yml       # DNS, NTP, domain, banner
│   ├── eos_devices/
│   │   └── connection.yml   # eAPI connection settings
│   └── lab_hosts/
│       └── connection.yml   # Docker connection settings
├── host_vars/
│   ├── edge-1/
│   │   └── vars.yml         # Interfaces, OSPF, BGP
│   ├── dist-1/
│   │   └── vars.yml         # Interfaces, VLANs, OSPF
│   ├── dist-2/
│   │   └── vars.yml         # Interfaces, VLANs, OSPF
│   ├── host-eng/
│   │   └── vars.yml         # IP and gateway
│   ├── host-sales/
│   │   └── vars.yml         # IP and gateway
│   └── host-server/
│       └── vars.yml         # IP and gateway
├── roles/
│   ├── base/
│   │   ├── tasks/main.yml
│   │   └── templates/base.j2
│   ├── interfaces/
│   │   ├── tasks/main.yml
│   │   └── templates/
│   │       ├── vlans.j2
│   │       └── interfaces.j2
│   ├── routing/
│   │   ├── tasks/main.yml
│   │   └── templates/routing.j2
│   ├── security/
│   │   ├── tasks/main.yml
│   │   └── templates/security.j2
│   └── validate/
│       └── tasks/main.yml
└── docs/
```

## Lessons Learned

**1. Arista EOS is not Cisco IOS**
EOS uses `dns domain` instead of `ip domain-name`. EOS does not have `ip ssh version` — SSH v2 is the default. Templates that assume Cisco syntax will fail. Always verify commands against the target platform.

**2. cEOS does not persist management API from startup-config**
Adding `management api http-commands` / `no shutdown` to startup-config has no effect in Containerlab. The eAPI service must be enabled at runtime after boot. This creates a chicken-and-egg problem — Ansible needs eAPI to connect, but enabling eAPI requires access to the device. The bootstrap script solves this by using `docker exec` before Ansible runs.

**3. cEOS boot timing is unpredictable**
The CLI may be ready but eAPI is not. A fixed `sleep` is unreliable — boot times vary per device and per run. The bootstrap script uses active polling instead: it checks CLI readiness, then eAPI readiness, and only proceeds when both respond.

**4. Never `docker restart` a Containerlab node**
Restarting a container with `docker restart` disconnects the virtual links that Containerlab created. The node boots but cannot find its interfaces, hanging at "Connected 0 interfaces." Always use `containerlab destroy` and `containerlab deploy` for lifecycle management.

**5. Alpine containers need the `raw` module**
Alpine hosts have no Python installed. Standard Ansible modules require Python on the target. The `raw` module bypasses this by sending commands directly through the Docker connection plugin.

## Design Decisions

**eAPI over SSH** — Ansible connects to cEOS via HTTPS (eAPI) rather than SSH (network_cli). eAPI returns structured JSON, is faster, and is more reliable for automation. This is the recommended approach in Arista's own documentation.

**Two separate playbooks** — Network devices and hosts use fundamentally different connection methods (httpapi vs docker) and require different modules. Separating them keeps each playbook focused and avoids connection-type conflicts.

**Bootstrap script instead of startup-config** — After discovering that cEOS ignores management API settings in startup-config under Containerlab, we moved bootstrapping to a dedicated script with active health checks rather than relying on static config or fixed delays.

**Roles for separation of concerns** — Each role manages one domain (base settings, interfaces, routing, security, validation). This means you can re-run just the routing config with `--tags routing` without touching anything else.
