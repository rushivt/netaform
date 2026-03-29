<p align="center">
  <img src="../../../bitt.png" alt="Bitt" width="200">
</p>

# Interview: Bitt builds his first pipeline

**Interviewer:** Bitt. You look... different today. Are you smiling?

**Bitt:** I AM smiling. I've been waiting three phases for this. Three! Phase 1 was building the network by hand. Phase 2 was automating it with Ansible. Phase 3 was poking at it with NETCONF. But THIS — Phase 4 — this is where it all comes together. A real CI/CD pipeline. A REAL one. Not a blog post, not a YouTube tutorial, not a "just add this YAML file and you're done" — an actual, working, enterprise-grade pipeline that deploys a network, configures it, tests it, and tears it down. I built that. ME. A panda. In a container.

**Interviewer:** I haven't even asked a question yet.

**Bitt:** I know. I've been rehearsing. Three phases of frustration — eAPI not turning on, NETCONF namespaces from hell, Nokia SR Linux requiring fourteen separate commands to enable one management protocol — and now I finally have a pipeline that catches all of that BEFORE it hits main. Do you know how good that feels? It's like eating bamboo that someone already peeled for you.

**Interviewer:** OK, let's start from the beginning. What is CI/CD, in your words?

**Bitt:** Right. So imagine you're a network engineer and you want to change an OSPF area on a switch. The old way: you SSH in, type the commands, hope nothing breaks, and go get coffee. The new way: you change a YAML file, push it to a Git branch, and a robot army verifies that your change doesn't break anything. That robot army is the CI/CD pipeline. CI — Continuous Integration — checks your code every time you push. CD — Continuous Delivery — makes sure the validated change is ready to deploy. The key word is "continuous." Not "whenever someone remembers to test." Not "on Fridays before the change window." Every. Single. Push.

**Interviewer:** So what does your pipeline actually do?

**Bitt:** Two pipelines, actually. Pipeline one is the bouncer at the door. Every time I push code to my feature branch, it runs four checks. yamllint makes sure my YAML isn't mangled — bad indentation can silently break Ansible playbooks. flake8 checks my Python scripts for syntax errors and undefined variables — the kind of bugs that would crash pytest ten minutes into a run. ansible-lint checks if my playbooks follow best practices — deprecated modules, missing task names, that kind of thing. And Gitleaks — oh, Gitleaks is my favorite — it scans the entire git history looking for passwords. Because I learned the hard way that deleting a password in a later commit doesn't actually remove it from git history. It's still there. Like that embarrassing photo from college. Gitleaks finds it.

**Interviewer:** And the second pipeline?

**Bitt:** That's the big one. When I raise a PR to merge into main, the full integration pipeline kicks off. It re-runs the lint checks — because code can change between the last push and the PR — and then it gets serious. It deploys a full Containerlab topology on my self-hosted runner. Seven containers: an ISP router running FRRouting, three Arista cEOS switches, and three Linux hosts. The bootstrap script waits for every device to boot and have eAPI running. Then Ansible configures the entire network — hostname, DNS, NTP, VLANs, OSPF, BGP, ACLs, the works. Then it waits thirty seconds for OSPF and BGP to converge. Then pytest runs forty tests across five layers. Then — and this is important — it tears down the entire topology, even if the tests failed. And it posts the results to the PR as a summary so the reviewer can see at a glance whether the change is safe.

**Interviewer:** Forty tests? For three switches?

**Bitt:** I know what you're thinking. "That's overkill." It's not. Let me walk you through the layers. Layer 1: can I even reach the devices? NAPALM connects to each switch and pulls facts — hostname, model, OS version. If this fails, everything else will fail too, so there's no point continuing. Layer 2: are all the interfaces up with the right IPs? NAPALM checks that Ethernet1 is up, Loopback0 has the right /32, VLAN SVIs have their gateway IPs. Layer 3: are the protocols working? Is BGP established with the ISP? Are OSPF routes in the table? Does edge-1 have the default route? Do the dist switches know about all three VLAN subnets? Layer 4: can the hosts actually talk to each other? This one uses docker exec to ping from inside the host containers — host-eng pings host-sales, host-server, the ISP, every router's loopback. Six hosts, three gateways, three loopbacks, one ISP — fifteen individual ping checks. Layer 5: are the security ACLs configured? Does the management ACL exist? Does it have a deny rule?

**Interviewer:** Why not just ping and call it a day?

**Bitt:** Because ping tells you "it works" but not WHY it works. Or more importantly, why it DOESN'T work. If host-eng can't reach host-sales, is it because the interface is down? Because OSPF didn't converge? Because the VLAN SVI doesn't have an IP? Because the gateway isn't in the routing table? Ping gives you one bit of information: yes or no. The five layers give you the entire diagnostic chain. The first failure in the output IS your root cause.

**Interviewer:** Tell me about NAPALM. I thought you were a NETCONF person after Phase 3.

**Bitt:** NETCONF is great for configuration management. Lock the candidate, edit, validate, commit. Beautiful transactional model. But for testing, you want structured data you can assert against. NAPALM gives you that. I call `get_bgp_neighbors()` and I get a Python dictionary: `{"global": {"peers": {"203.0.113.1": {"is_up": True, "remote_as": 65000}}}}`. One line to assert: `assert peer["is_up"] is True`. Try doing that with raw NETCONF XML. You'd be parsing namespace-qualified XML trees just to check if a BGP peer is up. NAPALM abstracts the vendor API. Same getter, same dictionary structure, whether the device is Arista, Cisco, or Juniper. The only thing that changes is the driver name.

**Interviewer:** And pytest? You didn't know pytest before this phase.

**Bitt:** I didn't know ANY testing framework before this phase. And you know what? pytest is shockingly simple. You write a function that starts with `test_`. Inside it, you write `assert something_is_true`. If it's true, the test passes. If it's false, the test fails. That's it. That's the whole framework. Everything else — fixtures, parametrize, conftest — is just convenience on top of that core idea.

**Interviewer:** What's parametrize?

**Bitt:** My favorite pytest feature. Instead of writing `test_edge1_reachable()`, `test_dist1_reachable()`, `test_dist2_reachable()` — three functions with identical logic — I write ONE function and parametrize it with the device names. pytest runs it three times, once per device, and reports each one separately. So in the output I see `test_device_reachable[edge-1] PASSED`, `test_device_reachable[dist-1] PASSED`. If dist-2 fails, I see exactly which device has the problem. I have forty tests from five files, and most of them are parametrized. Without parametrize I'd have maybe a hundred and twenty separate functions. With it? Maybe twenty.

**Interviewer:** What's conftest.py?

**Bitt:** The shared toolbox. It's a special file that pytest discovers automatically. I put my NAPALM connection fixtures in there — open three connections once at the start of the session, share them across all forty tests, close them at the end. Without session-scoped fixtures, every test would open and close its own connections. That's a hundred and twenty HTTPS handshakes instead of three. The test run would take fifteen minutes instead of two.

**Interviewer:** Let's talk about the self-hosted runner. Why not use GitHub's cloud runners?

**Bitt:** Because Arista cEOS can't be downloaded from a public container registry. You need an Arista account to get the image. GitHub's cloud runners start as blank Ubuntu VMs — they'd have to download cEOS during every pipeline run, which isn't possible without credentials and a license agreement. A self-hosted runner is my own Ubuntu machine with cEOS already installed. Docker is there. Containerlab is there. The cEOS image is cached. The pipeline says "deploy this topology" and Containerlab just... does it. No downloading, no waiting, no license issues.

**Interviewer:** Isn't there a security risk with self-hosted runners on public repos?

**Bitt:** YES. Thank you for asking. If someone forks my repo and creates a PR, their code would execute on my machine. They could read my files, steal my SSH keys, install malware — anything. The fix is in GitHub settings: "Require approval for all external contributors." Fork PRs sit in a pending state until I manually approve them. My own branches run automatically. It's a one-checkbox fix, but it's critical. I almost missed it.

**Interviewer:** You mentioned Ansible Vault and GitHub Secrets. That sounds like two things doing the same job.

**Bitt:** They serve different contexts. Locally, when I run `ansible-playbook network.yml` on my machine, Ansible needs credentials to connect to the cEOS switches. Those credentials live in a vault.yml file that's encrypted with AES-256. The decryption password is in a `.vault-pass` file that's in `.gitignore` — never committed. So git has the encrypted vault (unreadable), and my machine has the key (not in git). In CI, the runner doesn't have my `.vault-pass` file. Instead, GitHub Secrets injects the credentials via `--extra-vars`, which override whatever the vault says. But here's the gotcha that cost me an hour — Ansible still tries to DECRYPT the vault file even though extra-vars override the values. It loads all group_vars files, sees the encrypted vault, and panics because it has no password. The fix: the vault password itself is also a GitHub Secret. The pipeline creates a temporary password file, decrypts the vault, and then extra-vars override the decrypted values anyway. Belt AND suspenders.

**Interviewer:** That sounds... convoluted.

**Bitt:** It is. And it gets better. The `ansible.cfg` file says `vault_password_file = .vault-pass`. That file exists on my machine as a symlink. On the CI runner? It doesn't exist. Ansible crashes. The pipeline uses `sed` to delete that line from `ansible.cfg` at runtime and provides the vault password through a different mechanism. One `ansible.cfg`, two environments, one `sed` command to bridge them. Not my proudest moment architecturally, but it works, it's clean in the commit history, and it's a GREAT interview story about dual-layer credential management.

**Interviewer:** Let's talk about the linting journey. I see... seven commits just to get lint passing?

**Bitt:** [laughs] Seven commits. Seven! First the yamllint defaults were too strict — Phase 3's SR Linux Ansible roles had lines over 160 characters because YANG paths are verbose. Added phase exclusions. Then ansible-lint couldn't find the `arista.eos` collection on the GitHub runner — had to add `ansible-galaxy collection install` to the workflow. Then ansible-lint flagged `ignore_errors` in the hosts playbook — added it to the skip list. Then it flagged variable names in the validate role for not having a role prefix — couldn't skip it with the short name, had to use the full rule ID `var-naming[no-role-prefix]`. Then the CI pipeline's lint job had the same collection issue. Seven commits to make lint happy. And every single one of those commits triggered the lint pipeline, which showed me the next error.

**Interviewer:** Was it worth it?

**Bitt:** Absolutely. Here's what I have now: a lint configuration that's tuned for network automation. yamllint allows 160-character lines, accepts Ansible's `yes/no` truthy values, doesn't require `---` on every file, and ignores phases 1-3. ansible-lint skips rules that are normal in network automation — `raw` module usage, `ignore_errors` for idempotent commands, role variable prefix conventions. flake8 only checks fatal errors, not style. And Gitleaks scans the full history. This configuration carries forward into every future phase. The seven commits were the cost; the permanent linting infrastructure is the payoff.

**Interviewer:** The teardown step. Tell me why that's important.

**Bitt:** If the tests fail and the pipeline stops, what happens? The Containerlab topology stays running on the runner. Seven Docker containers, sitting there, eating resources. The next pipeline run tries to deploy the same topology and fails with "containers already exist." Now your pipeline is broken not because of a code problem, but because of leftover state from the last run. `if: always()` on the teardown step means it runs no matter what — tests passed, tests failed, Ansible crashed, the bootstrap timed out, anything. The topology gets destroyed. And the `|| true` at the end means even if the destroy command fails (maybe the topology was already gone), the pipeline doesn't crash. Two safeguards, one purpose: never leave a mess.

**Interviewer:** The `continue-on-error` on the pytest step — explain that.

**Bitt:** Normally when a step fails, every subsequent step is skipped. If pytest fails and I DON'T have `continue-on-error: true`, the teardown step is skipped. Containers stay running. Pipeline is polluted for next time. So I set `continue-on-error: true` on pytest, which lets the pipeline continue to teardown and summary steps. But now the problem is: the job shows green even though tests failed! So there's a FINAL step that checks `steps.pytest.outcome` — if pytest failed, this step runs `exit 1` and properly fails the job. The sequence is: pytest fails → pipeline continues → teardown runs → summary posts → final step fails the job. The reviewer sees a red check. The topology is clean. Everything is correct.

**Interviewer:** What about the tests themselves? You said there were some failures during development.

**Bitt:** Two categories. First: VLAN SVIs showing as operationally down. The Phase 2 Ansible roles create all three VLANs (10, 20, 30) on both distribution switches. But DIST-1 only has a host in VLAN 10, and DIST-2 only has hosts in VLANs 20 and 30. Arista brings a VLAN interface up only when there's at least one port assigned to that VLAN. So Vlan20 on DIST-1 was created but down. The test caught it. I fixed the expected interfaces list to match reality — each switch only validates the VLANs it actually serves.

**Interviewer:** And the second category?

**Bitt:** Privileged mode. The ACL test used `docker exec Cli -c "show ip access-lists MGMT-ACCESS"` — but on Arista cEOS, that command requires enable mode. Without it, you get "privileged mode required." The fix was adding `-p 15` to run the CLI at privilege level 15. A one-flag fix, but it took a real test failure against a real device to discover it. That's exactly why you test against live infrastructure instead of guessing.

**Interviewer:** If someone looks at this phase and thinks "that's a lot of infrastructure for three switches" — what do you say?

**Bitt:** I say the same thing Ansible said in Phase 2, but bigger. Yes, building a CI/CD pipeline for three switches is overkill. But the pipeline doesn't care if it's three switches or three hundred. The Makefile commands are the same. The Ansible roles scale. The pytest tests are parametrized against the inventory — add a device, add its vars, the tests automatically include it. The lint configs carry forward. The self-hosted runner is already set up. The GitHub Secrets are stored. Every future phase — every future CHANGE — benefits from what was built here. Phase 4 isn't about three switches. It's about building the machine that validates all future machines.

**Interviewer:** Last question. What's next?

**Bitt:** Phase 5 is the AI troubleshooting agent. An autonomous agent that detects network faults, diagnoses root cause using real device APIs, and generates fix playbooks. Think about it — the pipeline we just built validates changes BEFORE they deploy. The AI agent handles what happens AFTER — when something breaks in production. It calls the same NAPALM getters, the same show commands, but instead of asserting pass/fail, it chains investigation steps together like a real engineer would. And every change that agent suggests? Goes through this pipeline before it merges. Because now we have the machine. And the machine doesn't sleep.

**Interviewer:** Thanks, Bitt.

**Bitt:** Thank you. And hey — if you fork this repo and your tests fail, check the Lessons Learned section before panicking. Actually, check the PR summary first. The pipeline already told you what went wrong. That's the whole point.
