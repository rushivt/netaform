# Phase 1: IP Addressing Plan

## Design Principles
- **10.0.0.0/8** for internal networks
- **203.0.113.0/24** for ISP peering (RFC 5737 documentation range)
- **/30** subnets for point-to-point links
- **/24** subnets for host VLANs
- Loopbacks use **10.0.255.x/32**

## Loopback Addresses

| Device   | Loopback0       | Purpose              |
|----------|-----------------|----------------------|
| ISP-RTR  | 10.0.255.1/32   | Router ID            |
| EDGE-1   | 10.0.255.10/32  | Router ID / OSPF RID |
| DIST-1   | 10.0.255.11/32  | Router ID / OSPF RID |
| DIST-2   | 10.0.255.12/32  | Router ID / OSPF RID |

## Point-to-Point Links

### ISP-RTR to EDGE-1 (eBGP peering)
| Device   | Interface | IP Address       |
|----------|-----------|------------------|
| ISP-RTR  | eth1      | 203.0.113.1/30   |
| EDGE-1   | eth1      | 203.0.113.2/30   |

### EDGE-1 to DIST-1 (OSPF Area 0)
| Device   | Interface | IP Address       |
|----------|-----------|------------------|
| EDGE-1   | eth2      | 10.0.1.1/30      |
| DIST-1   | eth1      | 10.0.1.2/30      |

### EDGE-1 to DIST-2 (OSPF Area 0)
| Device   | Interface | IP Address       |
|----------|-----------|------------------|
| EDGE-1   | eth3      | 10.0.1.5/30      |
| DIST-2   | eth1      | 10.0.1.6/30      |

### DIST-1 to DIST-2 (Inter-switch link, OSPF Area 0)
| Device   | Interface | IP Address       |
|----------|-----------|------------------|
| DIST-1   | eth2      | 10.0.1.9/30      |
| DIST-2   | eth2      | 10.0.1.10/30     |

## Interface Mapping

### ISP-RTR (FRRouting)
| Interface | Connects To     | IP Address       |
|-----------|-----------------|------------------|
| eth1      | EDGE-1 eth1     | 203.0.113.1/30   |
| lo        | -               | 10.0.255.1/32    |

### EDGE-1 (Arista cEOS - Border Router)
| Interface | Connects To     | IP Address       |
|-----------|-----------------|------------------|
| eth1      | ISP-RTR eth1    | 203.0.113.2/30   |
| eth2      | DIST-1 eth1     | 10.0.1.1/30      |
| eth3      | DIST-2 eth1     | 10.0.1.5/30      |
| Loopback0 | -               | 10.0.255.10/32   |

### DIST-1 (Arista cEOS - L3 Switch)
| Interface | Connects To     | IP Address       |
|-----------|-----------------|------------------|
| eth1      | EDGE-1 eth2     | 10.0.1.2/30      |
| eth2      | DIST-2 eth2     | 10.0.1.9/30      |
| eth3      | HOST-ENG eth1   | Access VLAN 10   |
| Vlan10    | -               | 10.0.10.2/24     |
| Vlan20    | -               | 10.0.20.2/24     |
| Vlan30    | -               | 10.0.30.2/24     |
| Loopback0 | -               | 10.0.255.11/32   |

### DIST-2 (Arista cEOS - L3 Switch)
| Interface | Connects To     | IP Address       |
|-----------|-----------------|------------------|
| eth1      | EDGE-1 eth3     | 10.0.1.6/30      |
| eth2      | DIST-1 eth2     | 10.0.1.10/30     |
| eth3      | HOST-SALES eth1 | Access VLAN 20   |
| eth4      | HOST-SERVER eth1| Access VLAN 30   |
| Vlan10    | -               | 10.0.10.3/24     |
| Vlan20    | -               | 10.0.20.3/24     |
| Vlan30    | -               | 10.0.30.3/24     |
| Loopback0 | -               | 10.0.255.12/32   |

### HOST-ENG (Linux container)
| Interface | Connects To     | IP Address                    |
|-----------|-----------------|-------------------------------|
| eth1      | DIST-1 eth3     | 10.0.10.100/24 (gw: 10.0.10.2) |

### HOST-SALES (Linux container)
| Interface | Connects To     | IP Address                    |
|-----------|-----------------|-------------------------------|
| eth1      | DIST-2 eth3     | 10.0.20.100/24 (gw: 10.0.20.3) |

### HOST-SERVER (Linux container)
| Interface | Connects To     | IP Address                    |
|-----------|-----------------|-------------------------------|
| eth1      | DIST-2 eth4     | 10.0.30.100/24 (gw: 10.0.30.3) |

## VLAN Subnets

| VLAN | Name        | Subnet          | DIST-1 IP   | DIST-2 IP   |
|------|-------------|-----------------|-------------|-------------|
| 10   | Engineering | 10.0.10.0/24    | 10.0.10.2   | 10.0.10.3   |
| 20   | Sales       | 10.0.20.0/24    | 10.0.20.2   | 10.0.20.3   |
| 30   | Servers     | 10.0.30.0/24    | 10.0.30.2   | 10.0.30.3   |

## BGP ASN Assignments

| Device   | ASN   | Role     |
|----------|-------|----------|
| ISP-RTR  | 65000 | ISP      |
| EDGE-1   | 65001 | Branch   |

## Summary

| Subnet          | Purpose                  |
|-----------------|--------------------------|
| 203.0.113.0/30  | ISP to EDGE-1 peering    |
| 10.0.1.0/30     | EDGE-1 to DIST-1         |
| 10.0.1.4/30     | EDGE-1 to DIST-2         |
| 10.0.1.8/30     | DIST-1 to DIST-2         |
| 10.0.10.0/24    | VLAN 10 - Engineering    |
| 10.0.20.0/24    | VLAN 20 - Sales          |
| 10.0.30.0/24    | VLAN 30 - Servers        |
| 10.0.255.0/24   | Loopbacks                |
