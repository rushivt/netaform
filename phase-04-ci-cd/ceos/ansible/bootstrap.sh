#!/bin/bash
set -e

echo "=== Netaform Phase 4 (cEOS) - Bootstrap ==="
echo ""

# Credentials from environment or defaults
CEOS_USER="${CEOS_USER:-admin}"
CEOS_PASS="${CEOS_PASSWORD:-admin}"

echo "Waiting for cEOS devices to boot..."
for device in edge-1 dist-1 dist-2; do
    echo -n "  Waiting for ${device} CLI..."
    until docker exec clab-netaform-p4-ceos-${device} Cli -c "show version" > /dev/null 2>&1; do
        sleep 5
    done
    echo " ready"
done

echo ""
echo "Bootstrapping cEOS devices for Ansible..."
for device in edge-1 dist-1 dist-2; do
    docker exec clab-netaform-p4-ceos-${device} Cli -c "enable
configure terminal
username ${CEOS_USER} privilege 15 secret ${CEOS_PASS}
aaa authorization exec default local
management api http-commands
   no shutdown"
    echo "  Bootstrapped ${device}"
done

echo ""
echo "Waiting for eAPI to come up..."
for device in edge-1 dist-1 dist-2; do
    echo -n "  Waiting for ${device} eAPI..."
    until curl -sk -u ${CEOS_USER}:${CEOS_PASS} \
        https://clab-netaform-p4-ceos-${device}:443/command-api \
        -d '{"jsonrpc":"2.0","method":"runCmds","params":{"version":1,"cmds":["show version"]},"id":1}' \
        > /dev/null 2>&1; do
        sleep 5
    done
    echo " ready"
done

echo ""
echo "Waiting for FRR ISP router..."
echo -n "  Waiting for FRR daemons..."
until docker exec clab-netaform-p4-ceos-isp-rtr vtysh -c "show version" > /dev/null 2>&1; do
    sleep 3
done
echo " ready"

echo ""
echo "Waiting for host containers..."
for host in host-eng host-sales host-server; do
    echo -n "  Waiting for ${host}..."
    until docker exec clab-netaform-p4-ceos-${host} ip link show eth1 > /dev/null 2>&1; do
        sleep 2
    done
    echo " ready"
done

echo ""
echo "Bootstrap complete. All devices ready for Ansible."
