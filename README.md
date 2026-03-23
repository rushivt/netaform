<p align="center">
  <img src="netaform-logo.png" alt="Netaform Logo" width="600">
</p>

# Netaform — Network Automation, Endlessly Evolving

A public, evolving network automation portfolio built on [Containerlab](https://containerlab.dev). Each phase introduces a realistic network scenario and layers in new tools.

## Phases

| Phase | Scenario                                                           | Key Tools               | Status      |
| ----- | ------------------------------------------------------------------ | ----------------------- | ----------- |
| 1     | [Enterprise Branch Office](phase-01-branch-office/)                | Containerlab, cEOS, FRR | 🟢 Complete |
| 2     | [Automating the Branch with Ansible](phase-02-ansible-automation/) | Ansible, Jinja2, Make   | 🟢 Complete |
| 3     | [Network Programmability — NETCONF](phase-03-programmability/)     | Python, ncclient, pyang | 🟢 Complete |

_More phases coming — follow the journey._

## Interview with Bitt

<table>
<tr>
<td width="120" align="center">
<img src="bitt.png" alt="Bitt" width="100">
</td>
<td>
Too many tools? Too much jargon? Don't worry — <strong>Bitt</strong> has you covered. Bitt is a panda who lives inside the network (don't ask how, it's a long story) and explains everything in plain language. No textbook definitions. No assumptions. Just honest answers with a side of humor.
<br><br>
📖 <a href="docs/conversations/what-is-netaform.md">Bitt explains what Netaform is all about</a>
</td>
</tr>
</table>

## Getting Started

### Prerequisites

| Tool         | Purpose                                                      | Setup                                                                                                                                                                                                               |
| ------------ | ------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Linux VM     | Containerlab requires Linux                                  | macOS users: install [OrbStack](https://orbstack.dev) and create an Ubuntu VM with `orb create ubuntu`                                                                                                              |
| Docker       | Container runtime for all network nodes                      | Inside your Linux VM: `sudo apt update && sudo apt install -y docker.io`                                                                                                                                            |
| Containerlab | Topology orchestration — deploys and wires up all containers | `sudo bash -c "$(curl -sL https://get.containerlab.dev)"`                                                                                                                                                           |
| Arista cEOS  | Network OS for switches and routers                          | Free download from [Arista](https://www.arista.com/en/support/software-download) — requires account. Apple Silicon users: download **cEOSarm-lab**, not cEOS-lab. Import with `docker import <file> ceos:<version>` |
| Git          | Version control                                              | `sudo apt install -y git`                                                                                                                                                                                           |
| Ansible      | Network automation and configuration management              | `pip3 install ansible`                                                                                                                                                                                              |

### Quick Start

```bash
# Clone the repo
git clone https://github.com/rushivt/netaform.git
cd netaform/phase-01-branch-office

# Deploy the lab
sudo containerlab deploy -t topology/topology.clab.yml

# Destroy the lab
sudo containerlab destroy -t topology/topology.clab.yml
```

## About

Built by [Tirupathi Rushi Vedulapurapu](https://linkedin.com/in/rushivt) — documenting the journey of building real-world network automation skills, one phase at a time.
