<p align="center">
  <img src="../../../bitt.png" alt="Bitt" width="200">
</p>

# Interview: Bitt sits down with Ansible

**Bitt:** Alright. You're Ansible. The one who's supposed to save us all from typing the same commands into three switches like some kind of medieval scribe.

**Ansible:** That's a colorful way to describe configuration management, but yes. I automate network provisioning. You define the desired state, I make it happen. Repeatedly, reliably, every time.

**Bitt:** Repeatedly and reliably. We'll get to that. First question — how do you even find the devices? There's an inventory file with container names like `clab-branch-office-edge-1`. Those aren't IP addresses. How does that work?

**Ansible:** Oh, that's straightforward. Docker registers every container it creates with an internal DNS resolver. When Containerlab spins up a node, Docker maps the container name to its management IP. I just ask for the name, Docker resolves it, and I connect. No hardcoded IPs needed.

**Bitt:** Docker has its own DNS. That was genuinely shocking when it came up. The inventory file just had names, not a single IP address, and somehow everything resolved. Felt like showing up at a restaurant with no reservation and they already have your table ready.

**Ansible:** Well, Docker is a thoughtful host.

**Bitt:** Right. OK, next thing. Your folder structure. When the role layout was first sketched out — base, interfaces, routing, security, validate — each with tasks and templates subfolders, plus group_vars, host_vars, inventory... I counted twenty-something directories for three switches. Three! Automation is supposed to make life EASIER. This felt like building a five-star hotel for a goldfish.

**Ansible:** How many switches do you think a real enterprise has?

**Bitt:** That's not the —

**Ansible:** Fifty? Two hundred? A thousand? The structure doesn't change. You add a host_vars file for the new device, and the same roles handle it. That's the point. It feels heavy for three switches because you're paying the setup cost. The return comes at scale.

**Bitt:** Spoken like someone who's never had to create twenty directories by hand. But fine, I'll admit — once everything was in place, knowing exactly where to look when something broke was... nice. Routing issue? Open the routing role. Interface wrong? Check interfaces. It's organized. Annoyingly organized.

**Ansible:** Thank you?

**Bitt:** Don't get excited. Let's talk about your templates. The Jinja2 stuff.

**Ansible:** My favorite part. One template generates config for every device. It loops over the interface data, checks the type — loopback, ethernet, VLAN — and produces the right config block for each. Same template, different variables, different output. Edge-1 gets routed interfaces and BGP. Dist-1 gets access ports, SVIs, and VLANs. One file handles both.

**Bitt:** That part was actually clever. The interfaces template checks "is this a loopback? Is this an ethernet in routed mode? Access mode? A VLAN SVI?" and generates completely different config blocks from the same loop. Watching it spit out three totally different switch configs from one template was a bit like watching a chef make three different dishes from the same pantry.

**Ansible:** Exactly. And the data is cleanly separated in host_vars. Change one IP in one YAML file, run the playbook, done. No logging into switches, no remembering which config mode you're in.

**Bitt:** Yeah, yeah. Now let's talk about something less elegant. eAPI.

**Ansible:** What about eAPI? It's the recommended way to manage Arista devices. HTTPS, structured JSON responses, faster than SSH, objectively —

**Bitt:** Objectively wonderful. Except it doesn't turn itself on.

**Ansible:** That's not really my —

**Bitt:** The `management api http-commands` config was placed in the startup-config. Correct syntax. Correct indentation. Deployed the lab. eAPI? Disabled. Moved the block to the top of the file. Redeployed. Still disabled. cEOS just... ignores it in Containerlab. Nobody warned us.

**Ansible:** Ah. That is a known cEOS platform behavior in container environments. The management API service —

**Bitt:** "Known." Known to whom?! Because it wasn't known during the hours spent rearranging config blocks and redeploying like rearranging furniture in a burning house. And here's the beautiful part — the only way to fix it is `docker exec`. Go around you entirely, reach into the container, and enable it manually. Because YOU need eAPI to connect, but eAPI needs someone OTHER than you to turn it on. A chicken-and-egg problem. A very irritating chicken-and-egg problem.

**Ansible:** So... how was it solved?

**Bitt:** A bootstrap shell script. Runs before you even enter the picture. Uses `docker exec` to reach into each container, create the admin user, enable AAA, turn on eAPI, and wait for it to actually respond. YOUR job is Day One configuration. The bootstrap handles Day Zero — getting the devices ready for you.

**Ansible:** That's a clean separation of responsibilities.

**Bitt:** Oh, it's clean NOW. That script went through THREE revisions. First version: a flat two-minute sleep. Failed because some switches boot faster than others. Second version: polls the CLI until `show version` responds. Better — but eAPI still wasn't ready even after the CLI was up. Third version: polls CLI, configures, then polls the HTTPS endpoint until it actually responds. Three iterations. To solve a problem that shouldn't exist.

**Ansible:** But it works now?

**Bitt:** Oh, and I forgot the best part. Even after eAPI was running, the connection was rejected. 401 Unauthorized. No admin user. No AAA. Fresh cEOS has NOTHING. So the bootstrap script grew from "enable eAPI" to "create users, enable AAA, enable eAPI, wait for CLI, wait for HTTPS." A ten-line script became a thirty-line script.

**Ansible:** ...but it works now. Reliably?

**Bitt:** ...yes. It works now. I'll give you that.

**Ansible:** And once it runs, how long does it take me to configure the entire network?

**Bitt:** Under a minute. All five roles across three switches plus three hosts.

**Ansible:** From blank hostnames to a fully routed network with OSPF, BGP, VLANs, security hardening, and validation. Under a minute.

**Bitt:** Speaking of blank hostnames — the startup-configs were stripped down to literally just the hostname. One line per switch. No interfaces, no routing, nothing. The decision was to make you the single source of truth. If the config exists in both the startup-config and your templates, which one wins when they disagree?

**Ansible:** Oh! That's a strong design choice. Most people leave the original configs as a safety net. Stripping them completely means —

**Bitt:** Means if you fail, the network is dead. No fallback. It's a trust exercise.

**Ansible:** And I passed?

**Bitt:** The pings went through. All three paths — inter-VLAN, cross-switch, all the way to the ISP. Zero packet loss. From bare hostnames to full connectivity. So... yes. You passed.

**Ansible:** I appreciate that.

**Bitt:** There's also a Makefile, which was a pleasant surprise. Everyone thinks Makefiles are just for compiling C programs, but it turns out they're just a command shortcut file. `make all` runs bootstrap plus both playbooks. `make validate` runs just the health checks. `make redeploy` destroys everything and rebuilds from scratch. Simple and useful.

**Ansible:** Standard practice in infrastructure-as-code projects.

**Bitt:** Standard for people who already know. For the rest of us, it's a nice discovery. Like finding out the bamboo you've been eating also has nutritional value. One more thing — the syntax differences. If you've been studying Cisco IOS, you expect `ip domain-name` and `ip ssh version 2` to work everywhere. They don't. Arista uses `dns domain`. And `ip ssh version` doesn't even exist — SSH v2 is just the default. Two failures during development. Two template corrections.

**Ansible:** Vendor-specific differences are unavoidable. The same concept, different words. That's precisely why my templates are valuable — you fix it once in the template, and it's fixed for every device that uses it. Fix it in CLI, and you're fixing it on every switch, every time.

**Bitt:** Fair point. Alright, last question. If someone looks at this phase and thinks "that's a LOT of setup for three switches" — what do you say?

**Ansible:** They're right. For three switches today, this is more work than doing it by hand. But the question isn't whether you can do it faster manually today. The question is whether you can do it at 3 AM after a network crash, half asleep, on fifty switches instead of three, and get the exact same result every time.

**Bitt:** I had a similar conversation about discipline recently. "Yesterday is history, tomorrow is a mystery, but today is a gift." The upfront work is the gift. Even if it doesn't feel like one while you're creating twenty directories.

**Ansible:** Is that a quote from somewhere?

**Bitt:** Master Oogway. Kung Fu Panda. Greatest film ever made. A wise old tortoise who understands that the journey matters more than the destination. You should watch it. There's a panda in it. Very relatable.

**Ansible:** I'll... add it to my backlog.

**Bitt:** Anyway — thanks for coming. Phase 3 is Python, apparently. NETCONF, RESTCONF, the raw API stuff.

**Ansible:** I'll still be around, you know. Python doesn't replace me.

**Bitt:** We'll see. I've learned not to make promises about what works and what doesn't in this project. eAPI taught me that.

**Ansible:** That's... fair.

**Bitt:** See you around, Ansible.
