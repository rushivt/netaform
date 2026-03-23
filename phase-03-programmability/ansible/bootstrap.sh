#!/bin/bash

echo "=== Phase 3: Bootstrap ==="
echo ""

# --- cEOS devices ---
echo "Waiting for cEOS devices to boot..."
for device in edge-1 dist-1 dist-2; do
  echo -n "  Waiting for ${device} CLI..."
  until docker exec clab-branch-office-${device} Cli -c "show version" > /dev/null 2>&1; do
    sleep 5
  done
  echo " ready"
done

echo "Bootstrapping cEOS devices for Ansible..."
for device in edge-1 dist-1 dist-2; do
  docker exec clab-branch-office-${device} Cli -c "enable
configure terminal
username admin privilege 15 secret admin
aaa authorization exec default local
management api http-commands
  no shutdown
management api netconf
  transport ssh default"
  echo "  Bootstrapped ${device}"
done

echo "Waiting for cEOS eAPI to come up..."
for device in edge-1 dist-1 dist-2; do
  echo -n "  Waiting for ${device} eAPI..."
  until curl -sk -u admin:admin https://clab-branch-office-${device}:443/command-api -d '{"jsonrpc":"2.0","method":"runCmds","params":{"version":1,"cmds":["show version"]},"id":1}' > /dev/null 2>&1; do
    sleep 5
  done
  echo " ready"
done

# --- Nokia SR Linux ---
echo ""
echo "Waiting for SR Linux dist-3 to boot..."
echo -n "  Waiting for dist-3 CLI..."
until docker exec clab-branch-office-dist-3 sr_cli "show version" > /dev/null 2>&1; do
  sleep 5
done
echo " ready"

echo "Enabling NETCONF, JSON-RPC, LLDP, and OpenConfig on dist-3..."
docker exec -i clab-branch-office-dist-3 sr_cli <<'SRLEOF'
enter candidate
set /system ssh-server netconf-ssh admin-state enable
set /system ssh-server netconf-ssh network-instance mgmt
set /system ssh-server netconf-ssh port 830
set /system ssh-server netconf-ssh disable-shell true
set /system aaa authorization role netconf services [netconf]
set /system aaa authorization role netconf netconf allowed-operations [get get-config edit-config commit lock unlock validate discard-changes get-data edit-data copy-config delete-config cancel-commit close-session kill-session get-schema]
set /system netconf-server mgmt admin-state enable
set /system netconf-server mgmt ssh-server netconf-ssh
set /system json-rpc-server admin-state enable
set /system json-rpc-server network-instance mgmt http admin-state enable
set /system lldp admin-state enable
set /system management openconfig admin-state enable
commit now
SRLEOF
echo "  dist-3 bootstrapped"

echo -n "  Waiting for dist-3 JSON-RPC..."
until curl -s -u admin:NokiaSrl1! http://clab-branch-office-dist-3:80/jsonrpc -d '{"jsonrpc":"2.0","id":1,"method":"get","params":{"commands":[{"path":"/system/name/host-name","datastore":"state"}]}}' 2>/dev/null | grep -q "result"; do
  sleep 3
done
echo " ready"

echo ""
echo "Bootstrap complete. Ready for Ansible."
