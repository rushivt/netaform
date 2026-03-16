#!/bin/bash
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
   no shutdown"
  echo "  Bootstrapped ${device}"
done

echo "Waiting for eAPI to come up..."

for device in edge-1 dist-1 dist-2; do
  echo -n "  Waiting for ${device} eAPI..."
  until curl -sk -u admin:admin https://clab-branch-office-${device}:443/command-api -d '{"jsonrpc":"2.0","method":"runCmds","params":{"version":1,"cmds":["show version"]},"id":1}' > /dev/null 2>&1; do
    sleep 5
  done
  echo " ready"
done

echo "Bootstrap complete. Ready for Ansible."