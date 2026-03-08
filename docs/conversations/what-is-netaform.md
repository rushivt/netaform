<p align="center">
  <img src="../../bitt.png" alt="Bitt" width="200">
</p>

# Interview: Bitt explains what Netaform is all about

**Interviewer:** So, Bitt. What exactly is Netaform?

**Bitt:** Oh, finally someone asks. I've been sitting here in this container waiting for someone to notice me. Netaform is a network automation project. Real topologies. Real protocols. Real tools. Built phase by phase, like seasons of a really nerdy TV show.

**Interviewer:** Container? You live in a container?

**Bitt:** Docker container, yes. Don't look at me like that. It's cozy. Plenty of bamboo— I mean, bandwidth. I share it with a few routers and switches. We get along. Mostly.

**Interviewer:** So it's a lab? Like a network lab?

**Bitt:** It's not just "a lab." Every phase builds a realistic network scenario — the kind of stuff you'd actually see in a company. Branch offices, data centers, service provider cores. And each phase layers in new automation tools. First you build the network by hand, then you automate it, then you test it, then you monitor it, then you let an AI troubleshoot it. It's a journey.

**Interviewer:** That sounds like a lot. Why not just... learn one tool?

**Bitt:** Because that's not how the real world works! Nobody walks into a job and says "I only know Ansible, please don't show me anything else." Networks are messy. They have five tools duct-taped together, three vendors who don't agree on anything, and a monitoring system that was set up by someone who left the company in 2019. Netaform prepares you for that beautiful chaos.

**Interviewer:** OK, fair point. But why Containerlab? Why not just use GNS3 or EVE-NG like everyone else?

**Bitt:** Have you tried running EVE-NG on a laptop? Your fans would file a noise complaint. Containerlab is lightweight — everything runs as containers. You define your entire network in a YAML file, type one command, and boom — you have a working topology. Destroy it with one command when you're done. No leftover VMs eating your RAM at 3 AM.

**Interviewer:** YAML? I thought we were doing networking, not DevOps.

**Bitt:** Welcome to 2026. That line doesn't exist anymore. The network IS code. Your topology is YAML. Your configs are templates. Your changes go through CI/CD pipelines. If you're still configuring switches by hand through a console cable, I have some news for you, and you're not going to like it.

**Interviewer:** You said Containerlab runs on Linux. I have a Type 2 hypervisor on my Mac. I can just install a Linux VM on top of it and use Containerlab inside that. Right?

**Bitt:** You could. But you're going to hate yourself. A full Ubuntu desktop VM eats 2-4 gigs of RAM just sitting there. Boot times in the 30-60 second range. Fans spinning. Battery draining. Shared folders that need manual setup. And you're running all of that just to get a terminal. There's a better way. Two words: OrbStack.

**Interviewer:** OrbStack? Never heard of it.

**Bitt:** OrbStack uses Apple's native Virtualization framework to run a lightweight Linux VM on your Mac. A full Ubuntu VM boots in two seconds. Not thirty, not sixty. Two. Idle CPU usage? Near zero. Your fans stay off. Your battery survives. You type `orb` in your Mac terminal and you're inside Linux. No SSH config, no window switching. Your Mac's home directory is already mounted inside the VM through VirtioFS. Edit files in VS Code on macOS, run them in Linux instantly. It's like your Mac grew a Linux brain. And here's the thing most people don't realize — OrbStack runs Docker containers too. Full Docker engine built in. It replaces your hypervisor and your container runtime at the same time. One tool, two jobs.

**Interviewer:** Wait what? It's a hypervisor AND a container manager? How does that work?

**Bitt:** Under the hood, OrbStack runs a single lightweight Linux VM with a shared kernel. Your Linux VMs and your Docker containers all live inside that same efficient layer. But from your perspective, they feel like separate things. You create a Linux machine with one command, run Docker containers with the usual `docker` commands — everything just works. And every container automatically gets a `.orb.local` domain. Running Nginx in a container called "webapp"? Access it at `webapp.orb.local`. No port mapping flags, no `localhost:8080` guesswork. Docker Compose services each get their own domain too.

**Interviewer:** So that's why you chose OrbStack instead of other lightweight tools like Colima or Podman?

**Bitt:** Exactly. Colima and Podman are solid for running containers, but they don't give you a full Linux environment that's seamlessly integrated with macOS. For this project, we need both. A proper Linux VM where Containerlab runs natively, and a Docker engine for the network containers. OrbStack handles both without breaking a sweat. On Apple Silicon, it uses Rosetta for x86 emulation instead of QEMU, so even Intel-based network images run significantly better. ARM-native images like Arista cEOS-arm and Nokia SR Linux run at full speed. I've lived inside a lot of environments, and OrbStack is the nicest apartment I've ever had.

**Interviewer:** OK I'm convinced. Back to Netaform — who is this project for?

**Bitt:** Anyone who wants to learn network automation the practical way. Network engineers who keep hearing "you need to learn automation" but don't know where to start. DevOps folks who suddenly got told "you're also responsible for the network now." Students who want a portfolio project that actually means something. Or honestly, anyone who thinks blinking LEDs on a switch are satisfying. I don't judge.

**Interviewer:** What if I don't know Python or Ansible or any of that?

**Bitt:** That's the whole point! Phase 1 starts with zero automation. You build a network by hand, understand the fundamentals — routing, switching, BGP, OSPF. Then Phase 2 introduces Ansible. Phase 3 brings Python. Each phase adds one or two new things. You're never drowning in ten tools at once.

**Interviewer:** And what if I get stuck?

**Bitt:** Everything is documented. Every phase has a README, an IP plan, a topology diagram, and config files that actually work. Clone the repo, deploy the lab, break things, fix things. That's how you learn. You should know — I've been broken and fixed more times than I care to admit.

**Interviewer:** You've been broken?

**Bitt:** Oh, you have no idea. But we'll save those war stories for the phase READMEs. Every phase has a "Lessons Learned" section with the real things that went wrong and how they got fixed. No sugarcoating. This panda doesn't sugarcoat.

**Interviewer:** Last question — why the name "Netaform"?

**Bitt:** "Net" for network. "Form" for forming, shaping, building. And it sounds like "terraform" which is one of the tools we use later. Plus the logo has nodes connected by lines — that's basically my family portrait. We pandas love connections.

**Interviewer:** Thanks, Bitt. See you in Phase 1?

**Bitt:** I'll be there. Probably stuck in a VLAN somewhere, munching on packets. Come find me.
