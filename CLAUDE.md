# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

Netaform is a network automation portfolio built on [Containerlab](https://containerlab.dev). It simulates real enterprise network scenarios inside containers and progressively layers in automation tooling. Each phase builds on the one before it — Phase 1 defines the topology, Phase 2 automates it with Ansible, Phase 3 adds programmability via NETCONF/RESTCONF.

All labs must run inside a Linux environment. The expected setup is an OrbStack Ubuntu VM on macOS.

## Phase Structure

### Phase 1 — Enterprise Branch Office (`phase-01-branch-office/`)
Defines the Containerlab topology: ISP-RTR (FRR), EDGE-1/DIST-1/DIST-2 (Arista cEOS), and three Alpine hosts. Static configs live in `configs/` per device. The topology YAML (`topology/topology.clab.yml`) references configs with `../configs/` paths.

```bash
cd phase-01-branch-office/topology
sudo containerlab deploy -t topology.clab.yml
sudo containerlab destroy -t topology.clab.yml
```

### Phase 2 — Ansible Automation (`phase-02-ansible-automation/`)
Automates Phase 1 from bare containers to a fully routed network. Uses the Phase 1 topology YAML directly (`LAB_TOPOLOGY := ../phase-01-branch-office/topology/topology.clab.yml`).

All commands run from `phase-02-ansible-automation/`:

```bash
make deploy      # Deploy Containerlab topology
make bootstrap   # Enable eAPI on cEOS nodes (must run before Ansible)
make network     # Run Ansible against cEOS switches
make hosts       # Run Ansible against Alpine hosts
make all         # bootstrap + network + hosts
make validate    # Run validate role only (show commands, health checks)
make redeploy    # destroy + deploy + all
make clean       # Destroy the lab
```

To target a single role without touching others:
```bash
ansible-playbook network.yml --tags routing
```

**Critical:** `make bootstrap` (or `./bootstrap.sh`) must complete before `make network`. cEOS does not persist `management api http-commands` from startup-config in Containerlab — eAPI must be enabled at runtime via `docker exec`.

### Phase 3 — Programmability (`phase-03-programmability/`)
Python scripts using NETCONF and RESTCONF against the live lab. Reads device IPs dynamically from the Containerlab-generated inventory at `phase-01-branch-office/topology/clab-branch-office/ansible-inventory.yml`.

```bash
cd phase-03-programmability
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run scripts from their directory so relative paths resolve correctly
cd scripts/netconf
python3 fetch_bgp_neighbors.py
```

`scripts/inventory.py` is the shared device lookup module — all Phase 3 scripts import it. It maps short names (`edge-1`) to Containerlab container names and pulls IPs from the generated inventory file.

## Key Architecture Facts

- **Phase 1 topology is the single source of truth** for the lab infrastructure. Phases 2 and 3 both reference it directly rather than defining their own.
- **Containerlab generates an Ansible inventory** at `phase-01-branch-office/topology/clab-branch-office/ansible-inventory.yml` after deploy. Phase 2 uses this for connection details; Phase 3's `inventory.py` reads it programmatically.
- **cEOS eAPI quirk**: eAPI does not start from startup-config under Containerlab. The bootstrap script polls for CLI readiness, configures eAPI via `docker exec`, then polls for HTTPS readiness before handing off to Ansible.
- **Alpine hosts have no Python**: Phase 2 uses the `raw` Ansible module for host configuration instead of standard modules.
- **cEOS requires ARM image on Apple Silicon**: Use `cEOSarm-lab`, not `cEOS-lab`.
- **Never `docker restart` a Containerlab node** — it disconnects virtual links. Always use `containerlab destroy` + `containerlab deploy`.
- **File ownership after destroy**: Containerlab bind-mounts as root. After destroying, run `sudo chown $USER:$USER <file>` if git operations fail with permission errors.

## Ansible Role Order (Phase 2)

Roles apply in this sequence: `base` → `interfaces` → `routing` → `security` → `validate`. Each role has a matching tag. Host vars in `host_vars/<device>/vars.yml` drive all Jinja2 templates.

## Phase 3 NETCONF Notes

- NETCONF runs on port 830
- YANG model used: OpenConfig `network-instance`
- `xmltodict` parses XML responses; single-item responses return a dict, not a list — normalize with `if isinstance(x, dict): x = [x]`
- Output files are written to `phase-03-programmability/output/`
