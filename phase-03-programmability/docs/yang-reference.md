# Phase 3: YANG Model Reference

## Overview

This document maps the YANG models used in Phase 3 to the features they support. Phase 3 focused on vendor-native YANG models for deep feature coverage on Nokia SR Linux, and validated OpenConfig models for multi-vendor interface queries across Arista cEOS and Nokia SR Linux.

## Two Types of YANG Models

**Vendor-native models** are specific to a single vendor's platform. They provide complete coverage of every feature the device supports and are the primary models used by the vendor's own automation tooling. Nokia SR Linux's native models use the `srl_nokia-*` namespace prefix.

**OpenConfig models** are vendor-neutral models maintained by the OpenConfig consortium. They define a common schema that multiple vendors implement, enabling the same NETCONF filter to return structured data from different vendors. Phase 3 validated this with interface queries across Arista and Nokia.

## Nokia SR Linux Native YANG Models Used

| Feature | YANG Module | Namespace | Used In |
|---------|-------------|-----------|---------|
| Interfaces | srl_nokia-interfaces | urn:nokia.com:srlinux:chassis:interfaces | get_interfaces.py, maarpu.py |
| Hostname | srl_nokia-system-name | urn:nokia.com:srlinux:chassis:system-name | maarpu.py |
| System | srl_nokia-system | urn:nokia.com:srlinux:general:system | maarpu.py |
| OSPF | srl_nokia-ospf | urn:nokia.com:srlinux:ospf:ospf | get_ospf_neighbors.py, maarpu.py |
| Network Instance | srl_nokia-network-instance | urn:nokia.com:srlinux:net-inst:network-instance | get_ospf_neighbors.py, maarpu.py |
| ACL | srl_nokia-acl | urn:nokia.com:srlinux:acl:acl | set_acl.py |
| IP Configuration | srl_nokia-if-ip | urn:nokia.com:srlinux:chassis:if-ip | atomicity_demo.py |

## OpenConfig YANG Models Used

| Feature | YANG Module | Namespace | Used In |
|---------|-------------|-----------|---------|
| Interfaces | openconfig-interfaces | http://openconfig.net/yang/interfaces | get_interfaces_openconfig.py |
| IP Addresses | openconfig-if-ip | http://openconfig.net/yang/interfaces/ip | get_interfaces_openconfig.py |

## Why Vendor-Native Models Were the Primary Choice

Vendor-native YANG models were used for the majority of Phase 3 scripts because they provided immediate, reliable access to every feature needed: OSPF neighbors, interface counters, ACL management, and configuration drift detection. The `diff netconf-rpc` CLI command on SR Linux generates exact NETCONF XML with correct namespaces for any config change, making vendor-native development fast and precise.

OpenConfig was validated for interface queries, where the same filter successfully returned structured data from both Arista and Nokia. Future phases may explore OpenConfig coverage for additional features like OSPF and BGP as the project matures.

## How Namespaces Were Discovered

Nokia SR Linux has a powerful CLI feature called `diff netconf-rpc`. After making a candidate change in the CLI, this command outputs the exact NETCONF XML with correct namespaces and element structure. This was the primary method for discovering namespace URIs throughout Phase 3.

Example workflow:
```
enter candidate
set /interface ethernet-1/1 description test
diff netconf-rpc
discard now
```

This outputs the full `<edit-config>` RPC with the correct `xmlns` attributes, which can be directly adapted into Python NETCONF filters. This approach is more reliable than manually reading YANG files, which contain module names but not always the full namespace URIs needed for NETCONF filters.

## pyang Tree Files

The following pyang-rendered YANG tree files are available in `scripts/yang/` for reference:

| File | Description |
|------|-------------|
| oc-interfaces-tree.txt | OpenConfig interfaces model tree |
| oc-network-instance-tree.txt | OpenConfig network-instance model tree (includes OSPF, BGP) |
| srl-interfaces-tree.txt | Nokia native interfaces model tree |
| srl-ospf-tree.txt | Nokia native OSPF model tree |

These were generated using pyang from YANG files extracted from the SR Linux container at `/opt/srlinux/models/`.

## YANG Model Sources

SR Linux ships its YANG models inside the container at `/opt/srlinux/models/` organized into four directories:

| Directory | Contents |
|-----------|----------|
| openconfig/ | OpenConfig standard models (interfaces, network-instance, OSPF, BGP, ACL, platform) |
| srl_nokia/ | Nokia native models (comprehensive coverage of all SR Linux features) |
| ietf/ | IETF standard models (base types, interfaces, YANG library) |
| iana/ | IANA registry models (interface types) |
