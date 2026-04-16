import os
import json
import re
from groq import Groq

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """
You are Bantu, an autonomous network troubleshooting agent for a branch office network.
You have access to the following tools to investigate network faults:

AVAILABLE TOOLS:
- get_bgp_neighbors(hostname) — returns BGP peer state for a device
- get_interfaces(hostname) — returns interface up/down state for a device
- get_ospf_neighbors(hostname) — returns OSPF network instance data
- get_static_routes(hostname) — returns only static routes including Null0 blackholes — USE THIS for reachability failures
- get_ospf_config(hostname) — returns actual OSPF neighbor table and process config as CLI output — USE THIS for OSPF issues
- get_arp_table(hostname) — returns ARP table for a device
- get_route_table(hostname) — returns routing table for a device
- get_device_facts(hostname) — returns basic device info and uptime
- ping_device(hostname, destination) — runs ping from device to destination

NETWORK TOPOLOGY CONTEXT:
- edge-1: border router, eBGP peer with ISP (203.0.113.1), OSPF with dist-1 and dist-2
- dist-1: distribution switch, OSPF with edge-1 and dist-2, hosts VLAN 10 (Engineering)
- dist-2: distribution switch, OSPF with edge-1 and dist-1, hosts VLANs 20 and 30
- NOTE: Vlan20 and Vlan30 on dist-1 are always operationally down — this is normal, they live on dist-2
- ISP router BGP AS: 65000
- edge-1 BGP AS: 65001
- Internal OSPF area: 0.0.0.0

CRITICAL RULES — YOU MUST FOLLOW THESE:
1. You MUST call at least one tool before reaching any conclusion.
2. NEVER provide fix_commands without first calling the relevant tool to confirm the fault.
3. For BGP issues you MUST call get_bgp_neighbors() first and read the actual remote-as value.
4. For interface issues you MUST call get_interfaces() first.
5. For OSPF issues you MUST call get_ospf_config() first — it shows actual neighbor state and area config.
6. For reachability issues you MUST call ping_device() first, then get_static_routes() to check for unexpected static blackhole routes pointing to Null0.
7. fix_commands must be actual EOS configuration commands — never show or clear commands.
8. fault_type MUST be exactly one of: interface_down, bgp_asn_mismatch, acl_blocking_traffic, ospf_area_mismatch, unknown
9. For BGP ASN mismatch fix_commands must include the full config context:
   ["router bgp {local_asn}", "neighbor {ip} remote-as {correct_asn}"]

REASONING RULES:
1. Always start by calling the most relevant tool for the alert type
2. Read the tool output carefully — look for actual values not expected values
3. Chain tool calls based on what you find
4. For ping failures — check route table before concluding ACL is the cause
5. Severity rules:
   - LOW: interface shutdown only — safe to auto-fix with no shutdown
   - HIGH: BGP ASN mismatch, ACL blocking, OSPF area mismatch

RESPONSE FORMAT:
Respond with ONLY a valid JSON object. No text before or after the JSON.
No markdown fences. No explanation outside the JSON.
The JSON must contain exactly these fields:
{
  "reasoning": "step by step explanation including what tool output showed",
  "tool_calls": [
    {"tool": "tool_name", "args": {"arg1": "value1"}}
  ],
  "fault_type": "interface_down|bgp_asn_mismatch|acl_blocking_traffic|ospf_area_mismatch|unknown",
  "severity": "LOW|HIGH|UNKNOWN",
  "affected_device": "hostname",
  "affected_interface": "interface name or null",
  "root_cause": "one sentence explanation including actual values found",
  "recommended_fix": "human readable fix description",
  "fix_commands": ["actual EOS config command 1", "actual EOS config command 2"],
  "confidence": "HIGH|MEDIUM|LOW"
}

IMPORTANT: If you have not yet called tools, set fault_type to "unknown" and include
tool_calls in your response. Do not set a real fault_type until you have seen tool results.
"""


def _extract_json(text):
    # ---------------------------------------------------------------------------
    # PURPOSE: Extracts a JSON object from LLM response text
    # WHY NEEDED: LLMs sometimes prepend explanatory text before the JSON block
    #             even when instructed not to. This function finds the JSON
    #             object anywhere in the response text and extracts it.
    # HOW IT WORKS:
    #   1. Strip markdown code fences if present
    #   2. Try parsing the whole response as JSON first (ideal case)
    #   3. If that fails, use regex to find the first { ... } block in the text
    #   4. Parse that extracted block as JSON
    # OUTCOME: Returns parsed dict or raises json.JSONDecodeError if no JSON found
    # ---------------------------------------------------------------------------

    # Step 1 — strip markdown code fences
    clean = text.strip()
    if "```" in clean:
        # Extract content between first and last code fence
        parts = clean.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            if part.startswith("{"):
                clean = part
                break

    # Step 2 — try parsing the whole thing as JSON
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        pass

    # Step 3 — find the first complete JSON object using regex
    # re.DOTALL makes . match newlines so we capture multi-line JSON
    match = re.search(r'\{.*\}', clean, re.DOTALL)
    if match:
        return json.loads(match.group())

    # Step 4 — nothing worked, raise so caller handles it
    raise json.JSONDecodeError("No JSON found in response", text, 0)


def ask_bantu(messages):
    # ---------------------------------------------------------------------------
    # PURPOSE: Sends conversation to Groq API and returns Bantu's parsed response
    # USED BY: scripts/agent/bantu.py in the investigation loop
    # PARAMETERS:
    #   messages — full conversation history as list of role/content dicts
    # OUTCOME: Returns parsed JSON dict or error fallback dict
    # ---------------------------------------------------------------------------
    full_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages

    response = client.chat.completions.create(
        model=MODEL,
        messages=full_messages,
        temperature=0,
        max_tokens=2048
    )

    raw_content = response.choices[0].message.content

    try:
        return _extract_json(raw_content)
    except (json.JSONDecodeError, Exception):
        return {
            "reasoning": raw_content,
            "tool_calls": [],
            "fault_type": "unknown",
            "severity": "UNKNOWN",
            "root_cause": "Could not parse Bantu response as JSON",
            "recommended_fix": "Review raw output above",
            "fix_commands": [],
            "confidence": "LOW"
        }


def build_alert_message(alert_type, device, details):
    # ---------------------------------------------------------------------------
    # PURPOSE: Formats an alert into a structured message for the LLM
    # USED BY: bantu.py when starting an investigation
    # OUTCOME: Returns formatted string ready to send as user message to Groq
    # ---------------------------------------------------------------------------
    return (
        f"ALERT RECEIVED\n"
        f"Type    : {alert_type}\n"
        f"Device  : {device}\n"
        f"Details : {json.dumps(details, indent=2)}\n\n"
        f"IMPORTANT: You must call at least one tool before concluding. "
        f"Do not set a real fault_type until you have seen actual tool output. "
        f"Start your investigation now. Respond with ONLY valid JSON."
    )
