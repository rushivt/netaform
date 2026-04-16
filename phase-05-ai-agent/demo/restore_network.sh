#!/bin/bash
# ---------------------------------------------------------------------------
# NETWORK RESTORE SCRIPT
# Restores network to correct state after a fault demo.
# USAGE: ./demo/restore_network.sh <fault_name>
# ---------------------------------------------------------------------------

FAULT=$1

if [ -z "$FAULT" ]; then
    echo "Usage: $0 <fault_name>"
    echo "Available: interface_down, bgp_asn_mismatch, acl_blocking, ospf_area_mismatch"
    exit 1
fi

case $FAULT in

  interface_down)
    echo "[Restore] Bringing Ethernet1 back up on edge-1..."
    docker exec clab-netaform-p4-ceos-edge-1 Cli -p 15 -c "
      configure
      interface Ethernet1
      no shutdown
      end
      write memory
    "
    echo "[Restore] Done — Ethernet1 on edge-1 is UP"
    ;;

  bgp_asn_mismatch)
    echo "[Restore] Restoring correct BGP ASN on edge-1..."
    docker exec clab-netaform-p4-ceos-edge-1 Cli -p 15 -c "
      configure
      router bgp 65001
      no neighbor 203.0.113.1 remote-as 65999
      neighbor 203.0.113.1 remote-as 65000
      end
      write memory
    "
    echo "[Restore] Done — BGP ASN restored on edge-1"
    ;;

  acl_blocking)
    echo "[Restore] Removing static blackhole route on dist-1..."
    docker exec clab-netaform-p4-ceos-dist-1 Cli -p 15 -c "
      configure
      no ip route 10.0.30.0/24 Null0
      end
      write memory
    "
    echo "[Restore] Done — Static blackhole removed from dist-1"
    ;;

  ospf_area_mismatch)
    echo "[Restore] Restoring correct OSPF area on dist-1..."
    docker exec clab-netaform-p4-ceos-dist-1 Cli -p 15 -c "
      configure
      router ospf 1
      no network 0.0.0.0/0 area 0.0.0.1
      no network 10.0.1.8/30 area 0.0.0.1
      no network 10.0.30.0/24 area 0.0.0.1
      no network 10.0.1.0/30 area 0.0.0.1
      no network 10.0.20.0/24 area 0.0.0.1
      no network 10.0.255.11/32 area 0.0.0.1
      no network 10.0.10.0/24 area 0.0.0.1
      network 10.0.1.8/30 area 0.0.0.0
      network 10.0.30.0/24 area 0.0.0.0
      network 10.0.1.0/30 area 0.0.0.0
      network 10.0.20.0/24 area 0.0.0.0
      network 10.0.255.11/32 area 0.0.0.0
      network 10.0.10.0/24 area 0.0.0.0
      end
      write memory
    "
    echo "[Restore] Done — OSPF area restored on dist-1"
    ;;

  *)
    echo "Unknown fault: $FAULT"
    exit 1
    ;;

esac
