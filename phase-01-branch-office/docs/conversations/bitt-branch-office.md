<p align="center">
  <img src="../../../bitt.png" alt="Bitt" width="200">
</p>

# Interview: Bitt gets real about the Branch Office

**Interviewer:** Welcome back, Bitt. So, Phase 1. A branch office. Sounds... boring?

**Bitt:** Boring?! BORING?! Do you know how many companies in the world run a branch office exactly like this? A border router talking to an ISP, a pair of distribution switches, some VLANs? This is the bread and butter of networking. Well, the bread and bamboo, in my case. If you can't build this, you can't build anything.

**Interviewer:** OK OK, calm down. Tell me about the topology.

**Bitt:** Right. So picture this. At the top, you've got an ISP router. That's the outside world. It speaks eBGP — which is how the internet actually works, by the way. Below that, you've got EDGE-1, the border router. It's the gatekeeper. One foot in the outside world via BGP, one foot in the internal network via OSPF.

**Interviewer:** Two different protocols? Isn't that complicated?

**Bitt:** That's how every company does it. BGP is the language of the internet — it's how networks owned by different organizations talk to each other. OSPF is the language used inside your own network. EDGE-1 is basically bilingual. It translates between the two. Think of it like an airport — international flights on one side, domestic on the other. Same building, different rules.

**Interviewer:** OK, that makes sense. What about the switches?

**Bitt:** DIST-1 and DIST-2. They're Layer 3 switches — not just dumb switches passing frames around. These guys can route. They run OSPF to talk to EDGE-1 and to each other, and they handle VLANs for department segmentation.

**Interviewer:** VLANs. I've heard the word a hundred times but honestly...

**Bitt:** Think of a VLAN like an invisible wall inside a switch. You've got the Engineering team, Sales team, and servers. You don't want Sales accidentally flooding the Engineering network with their massive PowerPoint presentations. So you put them in separate VLANs. VLAN 10 for Engineering, VLAN 20 for Sales, VLAN 30 for Servers. Even though they're plugged into the same physical switches, they can't see each other at Layer 2. If they want to talk, the traffic has to go up to Layer 3 and get routed. And that's where you can apply rules.

**Interviewer:** So how does traffic actually flow? Say someone in Engineering pings the server.

**Bitt:** Oh, you want the full tour? Buckle up. So HOST-ENG sits in VLAN 10 on DIST-1. It wants to reach HOST-SERVER in VLAN 30 on DIST-2. Here's what happens, step by step.

HOST-ENG says "I need to reach 10.0.30.100, that's not in my subnet, so I'll send it to my gateway." The gateway is DIST-1's VLAN 10 interface at 10.0.10.2. DIST-1 receives the packet, looks at the destination, and checks its routing table. OSPF has already told DIST-1 that the 10.0.30.0/24 network is reachable through DIST-2. So DIST-1 forwards the packet across the inter-switch link to DIST-2. DIST-2 receives it, sees that 10.0.30.100 is in its local VLAN 30, and delivers it to HOST-SERVER. The reply takes the reverse path. Done.

**Interviewer:** And if Engineering wants to reach the internet?

**Bitt:** Same thing, but the packet goes further. HOST-ENG sends to DIST-1, DIST-1 doesn't have a specific route for wherever the internet destination is, but it has a default route learned from OSPF. That default route points to EDGE-1. EDGE-1 received that default route from the ISP via BGP. So EDGE-1 forwards the packet to the ISP router, and off it goes. The return traffic follows the same chain backwards — ISP knows about our internal subnets because EDGE-1 advertises them via BGP.

**Interviewer:** So EDGE-1 is the translator between BGP and OSPF?

**Bitt:** Exactly. It takes the default route from BGP and pushes it into OSPF so the internal devices know how to reach the internet. And it takes the internal subnets from OSPF and pushes them into BGP so the ISP knows how to send traffic back. Two-way translation. Without EDGE-1 doing this, the internal network and the ISP would be completely blind to each other.

**Interviewer:** That's actually pretty elegant. Now, what's this FRRouting thing for the ISP? Sounds like a knockoff brand.

**Bitt:** Ha! FRRouting — FRR for short — is actually a serious open-source routing suite. It's the routing engine inside SONiC switches, Cumulus Linux, and a bunch of cloud infrastructure you use every day without knowing it. We use it to simulate the ISP because it's free, lightweight, and speaks BGP perfectly. In real life, you never know or care what your ISP runs internally — could be Cisco, Juniper, a potato with firmware. All that matters is it speaks BGP. FRR does that job.

**Interviewer:** A potato with firmware?

**Bitt:** You'd be surprised what's out there.

**Interviewer:** Why Arista cEOS for the switches?

**Bitt:** Three reasons. One — it's a native container, so it's lightweight and boots fast. No heavy VM needed. Two — it's the same software that runs on real Arista hardware in actual data centers. What you learn here transfers directly to production. Three — the automation ecosystem around Arista is mature. Ansible collections, NETCONF support, gNMI telemetry, REST APIs — all of it works and is well documented.

**Interviewer:** I noticed the hosts are just Alpine Linux containers. Why not something fancier?

**Bitt:** Because hosts don't need to be fancy. In real life, what does a workstation do on the network? It has an IP address and sends traffic. That's it from the network's perspective. Alpine Linux is 5 megabytes. It can ping. It can run traffic generators later. It's perfect. Why would I waste resources on a full Ubuntu desktop just to send a ping?

**Interviewer:** Let me make sure I understand the big picture. You've got seven containers, wired together by Containerlab, running three different protocols, across two different vendors. And it all fits on a laptop?

**Bitt:** Now you're getting it. Four network nodes — one FRR router, three Arista cEOS switches. Three Linux hosts. One YAML file defines the whole thing. One command to deploy, one command to destroy. You can tear down the entire branch office and rebuild it from scratch in under five minutes. Try doing that with real hardware.

**Interviewer:** That does sound powerful. What's the IP addressing scheme?

**Bitt:** Everything is planned out. 203.0.113.0/30 for the ISP link — that's an RFC 5737 documentation range, by the way, which means it's specifically reserved for examples and labs. Real professionals use it. Internal point-to-point links use /30 subnets from the 10.0.1.x range. VLANs get /24s — 10.0.10.0 for Engineering, 10.0.20.0 for Sales, 10.0.30.0 for Servers. Loopbacks sit in 10.0.255.x. Clean, documented, no overlaps. Just like a real network should be.

**Interviewer:** You really thought this through.

**Bitt:** If your IP plan is messy, everything built on top of it will be messy. This is the foundation. Get it right now, and Phases 2 through 20 get a lot easier.

**Interviewer:** Speaking of — what's next?

**Bitt:** Phase 2 is Ansible. I finally get automated instead of hand-configured. About time. My configs were getting typos and I was too polite to say anything. Even a patient panda has limits.

**Interviewer:** Thanks, Bitt.

**Bitt:** Anytime. And hey — if you clone this repo and something breaks, check the Lessons Learned section before panicking. Odds are, we already broke it the same way and wrote down the fix. Now if you'll excuse me, I have some packets to chew on.
