<p align="center">
  <img src="../netaform-logo.png" alt="Netaform Logo" width="600">
</p>
# Phase 1: Enterprise Branch Office

## Scenario

A small company branch office that needs internet access, internal department segmentation, and basic redundancy. This is one of the most common network designs in the real world — an edge router peering with an ISP, a pair of distribution switches handling internal routing, and hosts separated by VLANs.

## Topology

![Branch Office Topology](diagrams/branch-topology.png)

## Devices

| Device      | Image        | Role                                          |
| ----------- | ------------ | --------------------------------------------- |
| ISP-RTR     | FRRouting    | L3 router — simulates ISP, eBGP peer          |
| EDGE-1      | Arista cEOS  | Border router — eBGP to ISP, OSPF to internal |
| DIST-1      | Arista cEOS  | L3 switch — OSPF, VLANs, inter-VLAN routing   |
| DIST-2      | Arista cEOS  | L3 switch — OSPF, VLANs, inter-VLAN routing   |
| HOST-ENG    | Alpine Linux | Engineering department host (VLAN 10)         |
| HOST-SALES  | Alpine Linux | Sales department host (VLAN 20)               |
| HOST-SERVER | Alpine Linux | Server/infrastructure host (VLAN 30)          |

## Protocols

- **eBGP** between EDGE-1 (AS 65001) and ISP-RTR (AS 65000)
- **OSPF Area 0** between EDGE-1, DIST-1, and DIST-2
- **VLANs** for department segmentation (10: Engineering, 20: Sales, 30: Servers)

## IP Addressing Plan

See [docs/ip-plan.md](docs/ip-plan.md)

## How to Deploy

```bash
cd topology
sudo containerlab deploy -t topology.clab.yml
```

## How to Destroy

```bash
sudo containerlab destroy -t topology/topology.clab.yml
```

## Design Decisions

_To be documented after deployment and testing._

## Lessons Learned

_To be documented after completion._
