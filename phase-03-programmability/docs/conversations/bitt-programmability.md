<p align="center">
  <img src="../../../bitt.png" alt="Bitt" width="200">
</p>

# Interview: Bitt meets NETCONF and SR Linux

**Bitt:** Two guests today. NETCONF, the protocol. And SR Linux, the Nokia operating system. This phase nearly broke me, so let's get into it. NETCONF — who are you, in ten seconds?

**NETCONF:** I let software talk to network devices using structured XML over SSH. No screen-scraping, no regex parsing. Every piece of data follows a YANG schema. I've been an IETF standard since 2006 and every major vendor supports me — Cisco, Arista, Nokia, Juniper.

**Bitt:** SR Linux?

**SR Linux:** I'm Nokia's containerized network operating system. Built from scratch for modern data centers. I run natively in Docker, I have a model-driven management stack, and I'm free to download for lab use. No license required.

**Bitt:** Free is good. Because the amount of time spent figuring out how to enable NETCONF on you was NOT free. On Arista — two lines. `management api netconf`, `transport ssh default`. On you? A dedicated SSH server, an AAA role with explicit permissions for EVERY operation — get, get-config, edit-config, lock, unlock, commit, validate — and a named netconf-server instance binding it all together. Three configuration blocks.

**SR Linux:** Security-first design. Nothing is on by default. Every protocol, every operation, explicitly permitted.

**NETCONF:** I respect that, actually.

**Bitt:** Of course YOU respect it. You're the one who benefits from all those permissions. Meanwhile I'm staring at "Unknown namespace" errors wondering if I chose the wrong career.

**SR Linux:** That's where my `diff netconf-rpc` command comes in.

**Bitt:** OK, yes. Credit where it's due. That command saved this entire phase.

**SR Linux:** Make a config change in the candidate, run `diff netconf-rpc`, and I output the exact NETCONF XML — correct namespaces, correct element hierarchy, correct everything. No guessing.

**NETCONF:** I wish every vendor had that. Seriously. Half the difficulty of working with me on any platform is figuring out the right namespace URIs. SR Linux just tells you.

**Bitt:** Every single namespace problem this phase was solved by that command. Every one. Change something in CLI, run `diff netconf-rpc`, copy the XML into Python. Done. It made vendor-native YANG development genuinely fast.

**SR Linux:** You're welcome.

**Bitt:** Don't push it. Now NETCONF — the transaction thing. The candidate datastore. Explain why anyone should care.

**NETCONF:** When you change config through me, it goes to a candidate — a staging area. You make your changes, validate them, and only then commit. If anything is wrong, you discard. Running config is untouched.

**Bitt:** We demonstrated this. Scenario one: two interface descriptions changed atomically. Lock the candidate, push both changes, validate, commit, unlock. Both applied simultaneously. Not one at a time — both or neither.

**NETCONF:** And scenario two —

**Bitt:** Scenario two: one valid change plus one invalid change in the same batch. The invalid change was rejected. The candidate was discarded. And the valid change? Also gone. Because it's all-or-nothing. Running config didn't move a single bit.

**NETCONF:** That's the guarantee that CLI automation can't give you. If you send five CLI commands and the third one fails, the first two already executed. You have a half-configured device. With me, it's the full batch or nothing.

**SR Linux:** I'll add — my candidate datastore supports confirmed commit as well. Commit with a timer. If nobody confirms within the window, I automatically roll back. Useful when you're about to lock yourself out.

**NETCONF:** Show-off.

**SR Linux:** Just being thorough.

**Bitt:** Now the multi-vendor moment. We had Arista cEOS and Nokia SR Linux in the same topology. OSPF adjacencies between them —

**SR Linux:** Came up on the first try.

**Bitt:** It did. Full adjacency. dist-3 to edge-1, dist-3 to dist-2. Nokia to Arista. Zero issues. I'll admit, I was nervous about that.

**NETCONF:** OSPF is an IETF standard. Two standards-compliant implementations will always peer. That's the whole point.

**Bitt:** The OpenConfig interface query was the other multi-vendor win. Same Python script, same NETCONF filter, same XML — sent to both Arista and Nokia. Both returned interface names, admin status, oper status, counters, IP addresses. Same code, two vendors, identical output structure.

**NETCONF:** That's what standardized YANG models enable. When two vendors implement the same schema, one script handles both.

**SR Linux:** I should mention — OpenConfig needs to be explicitly enabled on me. `system management openconfig admin-state enable`. And LLDP has to be configured first.

**Bitt:** You could have mentioned that BEFORE the three hours of debugging.

**SR Linux:** It's in the documentation.

**Bitt:** ...moving on. Maarpu. The drift detector.

**NETCONF:** Maarpu — what is that? Did you name a script?

**Bitt:** Yes. Telugu word for "change." It reads the Ansible host_vars — the same file used to configure the device — as the intended state. Then queries the running config through NETCONF. Compares the two. We changed an interface description manually, ran Maarpu, and it caught it instantly. "MISMATCH at /interface/ethernet-1/1/description. Expected: Link to EDGE-1. Actual: UNAUTHORIZED CHANGE."

**NETCONF:** That's essentially what Batfish does — desired state versus live state, reported as a diff. Except you built it yourself, on top of me, against real device data.

**SR Linux:** One source of truth. Ansible says what it should be. NETCONF verifies what it is.

**Bitt:** And the ACL push — lock, edit-config, validate, commit, unlock, then read it back to verify. Full transactional workflow.

**NETCONF:** That's how production networks should handle every config change. Push, validate, commit, verify. Five steps.

**Bitt:** Alright. Quick round. NETCONF — where do you fit in the real world?

**NETCONF:** Configuration management. Transactional changes. Audit and compliance. Any time you need to read or write config with safety guarantees. I'm the workhorse for that. For real-time monitoring and streaming telemetry, gNMI is the modern choice — that's Phase 5.

**Bitt:** SR Linux — what should someone know before working with you for the first time?

**SR Linux:** I'm model-driven top to bottom. No CLI templates needed — everything is YANG paths and structured data. Learn `diff netconf-rpc` on day one. Enable OpenConfig early if you plan to do multi-vendor work. And my Ansible collection uses JSON-RPC under the hood, not SSH — so make sure the JSON-RPC server is running before you try Ansible.

**Bitt:** Final question for both of you. Was this phase worth the frustration?

**NETCONF:** You built seven working scripts, a multi-vendor lab, a drift detector, and a transaction demo. From zero NETCONF experience to production-grade workflows. Yes.

**SR Linux:** And you now know how to enable NETCONF on Nokia, which puts you ahead of most people who just read about it.

**Bitt:** I'll take that. Phase 4 is CI/CD. Every config change through a pipeline.

**NETCONF:** I'll be in the validation stage.

**SR Linux:** And I'll be the multi-vendor device that keeps things interesting.

**Bitt:** Interesting. That's one word for it. See you both in the pipeline.
**Bitt:** Alright. Quick round. NETCONF — where do you fit in the real world?

**NETCONF:** Configuration management. Transactional changes. Audit and compliance. Any time you need to read or write config with safety guarantees. For real-time monitoring and streaming telemetry, gNMI is the modern choice — but that's a different conversation.

**Bitt:** SR Linux — what should someone know before working with you for the first time?

**SR Linux:** Learn `diff netconf-rpc` on day one. Enable OpenConfig early if you plan to do multi-vendor work. And my Ansible collection uses JSON-RPC under the hood, not SSH — so make sure the JSON-RPC server is running before you try Ansible.

**Bitt:** Final question for both of you. Was this phase worth the frustration?

**NETCONF:** Seven working scripts, a multi-vendor lab, a drift detector, and a transaction demo. From zero NETCONF experience to production-grade workflows. You tell me.

**SR Linux:** And you now know how to enable NETCONF on Nokia, which puts you ahead of most people who just read about it.

**Bitt:** I'll take that. Thanks, both of you.

**NETCONF:** Anytime.

**SR Linux:** You know where to find me. Port 830.
