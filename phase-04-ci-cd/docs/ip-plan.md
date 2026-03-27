# Phase 4: IP Addressing Plan

## Design Principles
- Same addressing scheme as Phase 1 — consistency across phases
- **10.0.0.0/8** for internal networks
- **203.0.113.0/24** for ISP peering (RFC 5737 documentation range)
- **/30** subnets for point-to-point links
- **/24** subnets for host VLANs
- Loopbacks use **10.0.255.x/32**

## What Changed from Phase 1
- All Arista cEOS devices replaced with Nokia SR Linux
- Interface names changed: `Ethernet1` → `ethernet-1/1`, `Vlan10` → `irb0.10`
- VLANs are local to each switch (no trunk link needed)
- DIST-1 hosts VLAN 10 only, DIST-2 hosts VLANs 20 and 30

## Loopback Addresses

| Device   | Interface | IP Address      | Purpose              |
|----------|-----------|-----------------|----------------------|
| ISP-RTR  | lo        | 10.0.255.1/32   | Router ID            |
| EDGE-1   | system0   | 10.0.255.10/32  | Router ID / OSPF RID |
| DIST-1   | system0   | 10.0.255.11/32  | Router ID / OSPF RID |
| DIST-2   | system0   | 10.0.255.12/32  | Router ID / OSPF RID |

## Point-to-Point Links

### ISP-RTR to EDGE-1 (eBGP peering)
| Device   | Interface      | IP Address       |
|----------|----------------|------------------|
| ISP-RTR  | eth1           | 203.0.113.1/30   |
| EDGE-1   | ethernet-1/1   | 203.0.113.2/30   |

### EDGE-1 to DIST-1 (OSPF Area 0)
| Device   | Interface      | IP Address       |
|----------|----------------|------------------|
| EDGE-1   | ethernet-1/2   | 10.0.1.1/30      |
| DIST-1   | ethernet-1/1   | 10.0.1.2/30      |

### EDGE-1 to DIST-2 (OSPF Area 0)
| Device   | Interface      | IP Address       |
|----------|----------------|------------------|
| EDGE-1   | ethernet-1/3   | 10.0.1.5/30      |
| DIST-2   | ethernet-1/1   | 10.0.1.6/30      |

### DIST-1 to DIST-2 (Inter-switch routed link, OSPF Area 0)
| Device   | Interface      | IP Address       |
|----------|----------------|------------------|
| DIST-1   | ethernet-1/2   | 10.0.1.9/30      |
| DIST-2   | ethernet-1/2   | 10.0.1.10/30     |

## VLAN / IRB Configuration

| VLAN | Name        | Subnet       | Switch | IRB Interface | Gateway IP   |
|------|-------------|--------------|--------|---------------|--------------|
| 10   | Engineering | 10.0.10.0/24 | DIST-1 | irb0.10       | 10.0.10.2/24 |
| 20   | Sales       | 10.0.20.0/24 | DIST-2 | irb0.20       | 10.0.20.3/24 |
| 30   | Servers     | 10.0.30.0/24 | DIST-2 | irb0.30       | 10.0.30.3/24 |

## Host Addressing

| Host        | Interface | IP Address     | Gateway    | Connected To     |
|-------------|-----------|----------------|------------|------------------|
| HOST-ENG    | eth1      | 10.0.10.100/24 | 10.0.10.2  | DIST-1 e1-3      |
| HOST-SALES  | eth1      | 10.0.20.100/24 | 10.0.20.3  | DIST-2 e1-3      |
| HOST-SERVER | eth1      | 10.0.30.100/24 | 10.0.30.3  | DIST-2 e1-4      |

## BGP ASN Assignments

| Device   | ASN   | Role     |
|----------|-------|----------|
| ISP-RTR  | 65000 | ISP      |
| EDGE-1   | 65001 | Branch   |

## Routing Summary
- OSPF Area 0 on all inter-switch links and loopbacks
- eBGP between EDGE-1 (AS 65001) and ISP-RTR (AS 65000)
- EDGE-1 originates default route into OSPF from BGP
- IRB interfaces added as passive OSPF interfaces for subnet advertisement
- Inter-VLAN traffic routes via L3 point-to-point links (no trunk, no L2 extension)
