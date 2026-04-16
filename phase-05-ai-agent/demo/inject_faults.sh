#!/bin/bash
# ---------------------------------------------------------------------------
# FAULT INJECTION SCRIPTS
# Manually introduce faults into the running network for Bantu demos.
# USAGE: ./demo/inject_faults.sh <fault_name>
# ---------------------------------------------------------------------------

FAULT=$1

if [ -z "$FAULT" ]; then
    echo "Usage: $0 <fault_name>"
    echo "Available: interface_down, bgp_asn_mismatch, acl_blocking, ospf_area_mismatch"
    exit 1
fi

case $FAULT in

  interface_down)
    echo "[Inject] Shutting Ethernet1 on edge-1..."
    docker exec clab-netaform-p4-ceos-edge-1 Cli -p 15 -c "
      configure
      interface Ethernet1
      shutdown
      end
      write memory
    "
    echo "[Inject] Done — Ethernet1 on edge-1 is now DOWN"
    ;;

  bgp_asn_mismatch)
    echo "[Inject] Changing BGP ASN on edge-1 to wrong value..."
    docker exec clab-netaform-p4-ceos-edge-1 Cli -p 15 -c "
      configure
      router bgp 65001
      no neighbor 203.0.113.1 remote-as 65000
      neighbor 203.0.113.1 remote-as 65999
      end
      write memory
    "
    echo "[Inject] Done — BGP ASN mismatch injected on edge-1"
    ;;

  acl_blocking)
    echo "[Inject] Adding static blackhole route for Server VLAN on dist-1..."
    docker exec clab-netaform-p4-ceos-dist-1 Cli -p 15 -c "
      configure
      ip route 10.0.30.0/24 Null0
      end
      write memory
    "
    echo "[Inject] Done — Static blackhole for 10.0.30.0/24 injected on dist-1"
    ;;

  ospf_area_mismatch)
    echo "[Inject] Changing OSPF area on dist-1 to wrong area..."
    docker exec clab-netaform-p4-ceos-dist-1 Cli -p 15 -c "
      configure
      router ospf 1
      no network 10.0.1.8/30 area 0.0.0.0
      no network 10.0.30.0/24 area 0.0.0.0
      no network 10.0.1.0/30 area 0.0.0.0
      no network 10.0.20.0/24 area 0.0.0.0
      no network 10.0.255.11/32 area 0.0.0.0
      no network 10.0.10.0/24 area 0.0.0.0
      network 10.0.1.8/30 area 0.0.0.1
      network 10.0.30.0/24 area 0.0.0.1
      network 10.0.1.0/30 area 0.0.0.1
      network 10.0.20.0/24 area 0.0.0.1
      network 10.0.255.11/32 area 0.0.0.1
      network 10.0.10.0/24 area 0.0.0.1
      end
      write memory
    "
    echo "[Inject] Done — OSPF area mismatch injected on dist-1"
    ;;

  *)
    echo "Unknown fault: $FAULT"
    exit 1
    ;;

esac
