<p align="center">
  <img src="../netaform-logo.png" alt="Netaform Logo" width="600">
</p>

# Phase 4: CI/CD Pipeline - Network as Code

## Scenario

The branch office network from Phase 2 is automated with Ansible and programmable with NETCONF from Phase 3 — but there's no safety net. An engineer can push a broken config, run the playbook, and take down the network. Phase 4 introduces a CI/CD pipeline that validates every change before it reaches production. Every config modification goes through a Git branch, gets linted for syntax and best practices, triggers a full integration test on a self-hosted runner, and only merges to main after all 40 tests pass and a reviewer approves.

## What Changed from Phase 3

- **Self-hosted GitHub Actions runner** registered on the lab machine with Arista cEOS and Containerlab pre-installed
- **Two-stage pipeline**: lint on every push (GitHub-hosted), full integration test on PR to main (self-hosted)
- **pytest test suite** with 40 tests across 5 validation layers using NAPALM for vendor-neutral state retrieval
- **Ansible Vault + GitHub Secrets** for credential management — zero plaintext passwords in Git
- **Linting pipeline** with yamllint, flake8, ansible-lint, and Gitleaks secret scanning
- **Topology uses Phase 1/2 design** with Arista cEOS — each VLAN local to its switch, routed inter-switch links, no trunking

## Topology

Same branch office topology as Phase 1/2 — ISP router (FRR) peering with edge-1 via eBGP, two distribution switches running OSPF, three department hosts on separate VLANs. DIST-1 hosts VLAN 10 (Engineering), DIST-2 hosts VLANs 20 (Sales) and 30 (Servers). All inter-switch links are routed /30 point-to-point links.

## Devices

| Device      | Image       | Role                                              |
| ----------- | ----------- | ------------------------------------------------- |
| ISP-RTR     | FRRouting   | L3 router — simulates ISP, eBGP peer              |
| EDGE-1      | Arista cEOS | Border router — eBGP to ISP, OSPF to internal     |
| DIST-1      | Arista cEOS | L3 switch — OSPF, VLAN 10, inter-VLAN routing     |
| DIST-2      | Arista cEOS | L3 switch — OSPF, VLANs 20/30, inter-VLAN routing |
| HOST-ENG    | Linux       | Engineering department host (VLAN 10)             |
| HOST-SALES  | Linux       | Sales department host (VLAN 20)                   |
| HOST-SERVER | Linux       | Server/infrastructure host (VLAN 30)              |

## Interview with Bitt

<table>
<tr>
<td width="120" align="center">
<img src="../bitt.png" alt="Bitt" width="100">
</td>
<td>
CI/CD, pipelines, self-hosted runners, pytest, NAPALM, Ansible Vault, Gitleaks — Phase 4 has more moving parts than a Swiss watch. Bitt sat down with the Pipeline itself to find out why every config change needs to pass 40 tests before it's allowed anywhere near main.
<br><br>
📖 <a href="docs/conversations/bitt-cicd.md">Bitt meets the Pipeline</a>
</td>
</tr>
</table>

## Tools Used

| Tool               | Purpose                                                      |
| ------------------ | ------------------------------------------------------------ |
| GitHub Actions     | CI/CD pipeline orchestration                                 |
| Self-hosted runner | Executes integration tests on local machine with cEOS images |
| pytest             | Python test framework for network validation                 |
| NAPALM             | Vendor-neutral device state retrieval (EOS driver)           |
| Ansible 2.17       | Configuration management with arista.eos collection          |
| Ansible Vault      | Local credential encryption                                  |
| GitHub Secrets     | CI credential injection                                      |
| yamllint           | YAML syntax and style checking                               |
| flake8             | Python syntax error detection                                |
| ansible-lint       | Ansible playbook best practices                              |
| Gitleaks           | Git history secret scanning                                  |
| GNU Make           | Command shortcuts for deployment workflow                    |
| Containerlab       | Network topology orchestration                               |

## How It Works

### Pipeline Flow

Every config change follows the same path:

**1. Push to feature branch** → Lint pipeline triggers on GitHub-hosted runner. yamllint checks YAML syntax, flake8 checks Python for fatal errors, ansible-lint validates playbook best practices, Gitleaks scans for accidentally committed secrets.

**2. Raise PR to main** → Full CI pipeline triggers on self-hosted runner. Re-runs lint, deploys Containerlab topology, bootstraps cEOS devices, runs Ansible to configure the entire network, waits for protocol convergence, runs 40 pytest tests, posts results to PR summary, tears down topology.

**3. Review and merge** → Reviewer sees test results at a glance. If all tests pass, the change merges to main. If any test fails, the PR is blocked.

### Test Suite (5 Layers, 40 Tests)

| Layer | Tests | What It Validates                                                    | Method           |
| ----- | ----- | -------------------------------------------------------------------- | ---------------- |
| 1     | 6     | Device connectivity — can NAPALM reach all devices?                  | NAPALM facts     |
| 2     | 6     | Interface state — are interfaces up with correct IPs?                | NAPALM getters   |
| 3     | 7     | Protocol state — OSPF routes learned, BGP established?               | NAPALM getters   |
| 4     | 15    | Reachability — host-to-host, host-to-gateway, host-to-ISP, loopbacks | docker exec ping |
| 5     | 6     | Security — management ACLs configured with deny rule?                | docker exec CLI  |

### Credential Security

| Context           | Method         | How It Works                                                                                                     |
| ----------------- | -------------- | ---------------------------------------------------------------------------------------------------------------- |
| Local development | Ansible Vault  | Credentials encrypted in `vault.yml`, decrypted at runtime using `.vault-pass` (never committed)                 |
| CI pipeline       | GitHub Secrets | Credentials injected via `--extra-vars` and environment variables, vault decrypted using `VAULT_PASSWORD` secret |
| Secret scanning   | Gitleaks       | Scans full git history for accidentally committed passwords, API keys, or tokens                                 |

## Quick Start

```bash
cd ceos/ansible

# Deploy the Containerlab topology
make deploy

# Bootstrap eAPI + credentials, configure all devices
make all

# Run the pytest validation suite
make test

# Validate network health with Ansible only
make validate

# Destroy, redeploy, and configure from scratch
make redeploy

# Tear down the lab
make clean
```

## Self-Hosted Runner Setup

The CI pipeline requires a self-hosted runner with Docker, Containerlab, and Arista cEOS pre-installed.

```bash
# Run the setup script (checks prerequisites, downloads runner, registers with GitHub)
chmod +x setup-runner.sh
./setup-runner.sh

# Start the runner (interactive mode)
cd ~/actions-runner && ./run.sh
```

The runner registers with labels `self-hosted`, `linux`, `containerlab`, `ceos`. The CI workflow targets these labels with `runs-on: [self-hosted, linux, ceos]`.

**Security:** For public repositories, enable "Require approval for all external contributors" in repo Settings > Actions > General to prevent fork PRs from executing code on your runner.

## Project Structure

```
phase-04-ci-cd/
├── .github/workflows/
│   ├── lint.yml                     # Lint pipeline (GitHub-hosted, on push)
│   └── ci.yml                       # CI pipeline (self-hosted, on PR to main)
├── .yamllint                        # YAML lint config
├── .ansible-lint                    # Ansible lint config
├── .flake8                          # Python lint config
├── requirements.txt                 # Python dependencies
├── setup-runner.sh                  # Self-hosted runner setup script
├── ceos/
│   ├── topology/
│   │   ├── topology.clab.yml        # Containerlab topology (7 containers)
│   │   └── configs/
│   │       ├── isp-rtr/
│   │       │   ├── frr.conf         # ISP router BGP + routing config
│   │       │   └── daemons          # FRR daemon enablement
│   │       ├── edge-1/startup-config
│   │       ├── dist-1/startup-config
│   │       └── dist-2/startup-config
│   ├── ansible/
│   │   ├── ansible.cfg
│   │   ├── bootstrap.sh             # Pre-Ansible eAPI bootstrapping
│   │   ├── Makefile
│   │   ├── network.yml              # cEOS playbook
│   │   ├── hosts.yml                # Linux hosts playbook
│   │   ├── inventory/
│   │   │   └── inventory.yml
│   │   ├── group_vars/
│   │   │   ├── all/common.yml       # DNS, NTP, domain, banner
│   │   │   ├── eos_devices/
│   │   │   │   ├── connection.yml   # eAPI connection settings
│   │   │   │   └── vault.yml        # Encrypted credentials
│   │   │   └── lab_hosts/
│   │   │       └── connection.yml   # Docker connection settings
│   │   ├── host_vars/
│   │   │   ├── edge-1/vars.yml      # Interfaces, OSPF, BGP
│   │   │   ├── dist-1/vars.yml      # Interfaces, VLAN 10, OSPF
│   │   │   ├── dist-2/vars.yml      # Interfaces, VLANs 20/30, OSPF
│   │   │   ├── host-eng/vars.yml
│   │   │   ├── host-sales/vars.yml
│   │   │   └── host-server/vars.yml
│   │   └── roles/
│   │       ├── base/                 # Hostname, DNS, NTP, banner, eAPI
│   │       ├── interfaces/           # VLANs, routed/access interfaces, SVIs
│   │       ├── routing/              # OSPF, BGP
│   │       ├── security/             # Management ACL
│   │       └── validate/             # Show commands for verification
│   └── scripts/
│       ├── inventory.py              # Device connections + expected state
│       ├── napalm/
│       │   └── napalm_helpers.py     # NAPALM getter wrappers
│       └── tests/
│           ├── conftest.py           # Shared fixtures
│           ├── test_01_connectivity.py
│           ├── test_02_interfaces.py
│           ├── test_03_protocols.py
│           ├── test_04_reachability.py
│           └── test_05_security.py
└── docs/
    └── ip-plan.md
```

## Lessons Learned

**1. Self-hosted runners are the enterprise-realistic choice for network CI/CD**
Proprietary vendor images like Arista cEOS can't be pulled from public registries during a pipeline run. A self-hosted runner with pre-installed images reflects how real network teams operate. GitHub-hosted runners work only with freely available images like Nokia SR Linux — but SR Linux's JSON-RPC management interface wasn't available by default in the container version (v26.3.1), reinforcing that self-hosted is the practical path.

**2. Ansible Vault and GitHub Secrets serve different contexts**
Vault encrypts credentials in the repository for local development. GitHub Secrets injects credentials at CI runtime. Both are needed: vault for engineers running playbooks locally, secrets for the pipeline. Extra-vars in CI override vault values, but Ansible still decrypts the vault file when loading group_vars — so the vault password must also be a GitHub Secret.

**3. The vault password file creates a chicken-and-egg in CI**
`ansible.cfg` references `vault_password_file = .vault-pass` which exists locally but not on the CI runner. The pipeline uses `sed` to remove this line at runtime and provides the vault password via `--vault-password-file` created from the GitHub Secret. One `ansible.cfg` works in both contexts without maintaining two versions.

**4. Linting config requires tuning for network automation**
Default yamllint, flake8, and ansible-lint rules are too strict for network projects. YANG paths exceed 80-character line limits. Ansible's `raw` module triggers "use a proper module" warnings. cEOS startup-configs use non-standard YAML patterns. Custom config files (`.yamllint`, `.ansible-lint`, `.flake8`) tune each tool to flag real problems while accepting patterns that are normal in network automation.

**5. NAPALM provides the cleanest test interface**
NAPALM's structured getters return Python dictionaries that are perfect for pytest assertions. `get_bgp_neighbors()` returns `{"global": {"peers": {"203.0.113.1": {"is_up": True}}}}` — one line to assert. Parsing CLI text output would require regex and be fragile across EOS versions. NAPALM abstracts the vendor API, making tests portable.

**6. Teardown must always run — `if: always()` is non-negotiable**
Without `if: always()` on the teardown step, a failed test run leaves Containerlab containers running. The next pipeline run fails trying to deploy a topology that already exists. Combined with `continue-on-error: true` on the pytest step and a final check step, this ensures cleanup happens regardless of test outcome.

**7. VLANs without hosts stay operationally down on Arista cEOS**
Creating a VLAN SVI with Ansible doesn't guarantee it's operationally up. If no ports are assigned to that VLAN on the switch, the SVI stays down. The test suite initially expected all VLANs on all switches, but DIST-1 only has VLAN 10 and DIST-2 only has VLANs 20/30. Tests were corrected to match the actual design — each switch validates only the VLANs it serves.

## Design Decisions

**Self-hosted runner with Arista cEOS** — Chosen because proprietary vendor images can't be pulled from public registries. Pre-installing cEOS on the runner mirrors enterprise CI/CD where lab infrastructure is dedicated and persistent. A GitHub-hosted variant with Nokia SR Linux was evaluated but removed due to JSON-RPC management interface limitations in the container version.

**Two-stage pipeline (lint + integration)** — Lint runs on every push for fast feedback (seconds). Integration runs on PR for thorough validation (minutes). Lint uses a GitHub-hosted runner (no special requirements). Integration uses the self-hosted runner (needs Docker, Containerlab, cEOS). Separating them avoids tying up the self-hosted runner for simple syntax checks.

**NAPALM for test validation, Ansible for configuration** — Each tool does what it's best at. Ansible pushes declarative configuration. NAPALM retrieves structured operational state. pytest makes assertions on the structured data. Three tools, each in its lane.

**Five-layer test architecture** — Tests are organized from infrastructure (connectivity) to application (reachability) to policy (security). Each layer depends on the previous one. The first failure in the output points to the root cause. This mirrors how a network engineer manually troubleshoots — check L1, then L2, then L3, then end-to-end.

**Routed inter-switch links, no trunking** — Each distribution switch hosts only the VLANs it physically serves. OSPF handles all inter-subnet routing via the /30 point-to-point links. A trunk would add Layer 2 complexity (spanning tree, VLAN tagging, mac-vrfs) for no benefit since no VLAN spans both switches. Trunking is planned for Phase 9 with VXLAN/EVPN.

**Phase 1/2 topology reused** — The same branch office design proves that the CI/CD pipeline validates real infrastructure, not a toy example. Reusing existing Ansible roles demonstrates pipeline integration with established automation, not code written specifically for CI.
