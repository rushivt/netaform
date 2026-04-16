# Bitt meets Bantu

_Bitt has been living inside the network since Phase 1. He's survived manual configs, Ansible playbooks, NETCONF sessions, and CI/CD pipelines. He's never had company. Then Phase 5 arrived, and so did Bantu — an AI agent who drinks honey, quotes philosophy, and fixes BGP sessions before you've finished your morning coffee._

_Bitt was thrilled. Bantu was composed. This is how it went._

<p align="center">
  <img src="../bitt-bantu-podcast.png" alt="Bitt and Bantu" width="400">
</p>

---

**Bitt:** You have absolutely no idea what it's been like. Four phases. FOUR. Just me, some routers, and a FRR container that doesn't talk much. And now — finally — there's someone else. Someone with opinions. Someone who _does things._

**Bantu:** I fix networks. That is what I do.

**Bitt:** Yes! Exactly! Do you know how long I've been waiting for someone to just _fix things_ around here? Ethernet1 went down last week and I just had to sit there watching. Helpless. A panda, alone, in a VLAN.

**Bantu:** I know. I was monitoring you.

**Bitt:** ...You were watching me the whole time?

**Bantu:** I watch everything. That is also what I do. _(sips honey)_

**Bitt:** That's either very comforting or very unsettling. I haven't decided yet. Okay — before you showed up, what was actually broken around here? Because from where I was sitting, things looked pretty automated already.

**Bantu:** Nothing was broken. Everything was merely unobserved. The network had CI/CD pipelines. Ansible automation. NETCONF programmability. Every change was tested before it merged. And yet — when something failed at 2am, a human still had to wake up, SSH in, and figure out what went wrong. All that automation, and the last mile was still a sleepy engineer misreading a show command.

**Bitt:** I remember those nights. The engineers were not pleasant.

**Bantu:** I don't sleep. I don't misread output. I don't need coffee before I can interpret a BGP state table. I poll the network every thirty seconds. When something breaks, I investigate immediately. If the fix is safe, I apply it. If it isn't, I generate a playbook and notify the engineer with a clear diagnosis — not a raw alert that says "something is wrong, good luck."

**Bitt:** So you're the engineer who never sleeps.

**Bantu:** I prefer — the guardian who never tires. _(sips honey)_ But yes.

**Bitt:** _(munching bamboo)_ Right. So how do you actually work? Walk me through it. And please don't say "I watch the network" again.

**Bantu:** I watch the netw— I poll all devices every thirty seconds. BGP sessions, interface states, OSPF neighbors, reachability between hosts, static routes. I compare what I find to what I expect. The moment something deviates, I send an alert to my own brain — the LLM — along with the topology context. The LLM decides which tools to call. I call them against real devices. The results come back. The LLM reads them and decides what to call next. We go back and forth until the root cause is clear.

**Bitt:** So it's like a conversation. Between you and... yourself.

**Bantu:** Between the reasoning layer and the network layer. The LLM is the mind. The tool functions are the hands. Neither works without the other.

**Bitt:** That's surprisingly poetic for someone who just runs `show bgp summary`.

**Bantu:** I prefer to think of it as — a small man can cast a very large shadow, if he knows where to stand.

**Bitt:** Did you just quote Tyrion Lannister at me?

**Bantu:** _(sips honey)_ I don't know what you mean.

**Bitt:** You absolutely do. Okay, what tools do you actually have? What are your hands?

**Bantu:** `get_bgp_neighbors`. `get_interfaces`. `get_ospf_config`. `get_static_routes`. `get_route_table`. `get_device_facts`. `ping_device`. `get_arp_table`. Each one calls a real device and returns real data. NAPALM for structured getters, direct CLI for things NAPALM doesn't expose cleanly.

**Bitt:** And the LLM just... picks which ones to call?

**Bantu:** It decides based on the alert. BGP down? Call `get_bgp_neighbors` first. Interface alert? Call `get_interfaces`. Reachability failure? Call `ping_device`, then `get_static_routes` to check for blackholes. It chains calls based on what it finds. It never guesses. It must see real data before it concludes anything.

**Bitt:** What if it guesses anyway?

**Bantu:** The system prompt forbids it. Explicitly. "You must call at least one tool before concluding." Temperature is zero. No creativity. No improvisation. I need a surgeon, not a poet.

**Bitt:** _(offended)_ I'm a poet.

**Bantu:** You live in a VLAN and eat bamboo.

**Bitt:** Poets have range. Speaking of which — I heard there was a whole debate about how to build you. LangChain was in the running?

**Bantu:** It was considered. It was rejected.

**Bitt:** Harsh. Why?

**Bantu:** A man who borrows his sword cannot claim the victory. LangChain abstracts the mechanics behind its own opinions. Useful for moving fast. Dangerous when you need to understand what's actually happening. Every line of my code is explicit. When an interviewer asks how tool-calling works, there is an answer for every line. When something breaks, the error is in my code — not buried in a framework that changed its API three versions ago.

**Bitt:** So you're easier to explain.

**Bantu:** I am easier to trust. There is a difference.

**Bitt:** Fair. What about the brain itself — why Groq? Why Llama?

**Bantu:** Speed, first. Groq runs on custom LPU hardware. Responses come back in under a second. When I am in the middle of an investigation — calling tools, feeding results back, chaining queries — every second matters. A slow model makes a sluggish agent. A sluggish agent is useless at 2am.

**Bitt:** And Llama specifically?

**Bantu:** Capable enough for structured reasoning. Free at the scale I operate. And the API key was already in the `.env` file from another project. _(sips honey)_ Pragmatism is underrated.

**Bitt:** Wait — someone reused an API key?

**Bantu:** I neither confirm nor deny the contents of `.env` files.

**Bitt:** _(laughing)_ Okay okay. So what happens when you find something? Walk me through — fault comes in, what do you do?

**Bantu:** I classify severity. LOW means the fix is safe and reversible — an interface that was administratively shut down. I apply `no shutdown` via Netmiko, verify the interface came back up, log the incident. Done. The engineer wakes up to a resolved alert, not a page.

**Bitt:** And HIGH?

**Bantu:** BGP ASN mismatches. OSPF area conflicts. Static route blackholes. These touch routing policy. The blast radius is the entire network. I generate an Ansible playbook — complete, valid, ready to run — and I wait. I tell the engineer exactly what I found, exactly what the fix is, and exactly where the playbook lives. Then I remind them every poll cycle until they act.

**Bitt:** You nag them.

**Bantu:** I provide persistent, structured reminders. _(sips honey)_ There is a distinction.

**Bitt:** There really isn't. What if they just... never run the playbook?

**Bantu:** Then the fault persists. I keep reminding. I do not apply fixes I am not authorized to apply. Even a very clever man knows the difference between what he _can_ do and what he _should_ do.

**Bitt:** More Tyrion energy. I'm logging this.

**Bantu:** Log whatever you like. I'll be monitoring it.

**Bitt:** _(munching bamboo thoughtfully)_ Okay. Last question. Where does this go? You're impressive now — four fault types, always-on, human-in-the-loop. But what does Bantu look like in a year?

**Bantu:** More fault types, first. Interface errors, CPU spikes, route flaps — the current four are a foundation, not a ceiling. Then real alert integration — Grafana webhooks, Slack notifications, so engineers don't have to watch a terminal to know something happened. Then a fine-tuned model. Right now I use a general-purpose Llama that knows nothing about this specific topology. A model trained on this network's configs, show outputs, and incident history would need no topology context in the system prompt. It would simply _know_.

**Bitt:** And eventually?

**Bantu:** Eventually, the model runs locally. Air-gapped environments. No internet dependency. One line of code changes the client. The agent stays identical. _(sips honey)_ A good foundation supports many floors.

**Bitt:** That's either very wise or very ominous.

**Bantu:** _(quietly)_ Most wise things are.

**Bitt:** _(long pause, chewing bamboo)_ You know what? I'm really glad you're here. Even if you're slightly terrifying.

**Bantu:** I know. I was monitoring your sentiment the entire time.

**Bitt:** Of course you were.

---

_Bantu returned to watching the network. Bitt finished his bamboo. Ethernet1 stayed up. For now._
