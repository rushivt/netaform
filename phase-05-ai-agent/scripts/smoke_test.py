import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env before anything else
load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))

# ---------------------------------------------------------------------------
# PATH SETUP
# Add both the scripts directory AND the scripts/agent directory to path
# so Python can find all modules regardless of where smoke_test.py is run from
# ---------------------------------------------------------------------------
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPTS_DIR)
sys.path.insert(0, os.path.join(SCRIPTS_DIR, "agent"))
sys.path.insert(0, os.path.join(SCRIPTS_DIR, "tools"))

from inventory import get_all_devices, get_napalm_config
from groq import Groq

GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
RESET  = "\033[0m"

def ok(msg):     print(f"{GREEN}  [PASS] {msg}{RESET}")
def fail(msg):   print(f"{RED}  [FAIL] {msg}{RESET}")
def warn(msg):   print(f"{YELLOW}  [WARN] {msg}{RESET}")
def header(msg): print(f"\n{msg}")


def test_env_variables():
    header("1. Checking environment variables...")
    required = ["GROQ_API_KEY", "DEVICE_USERNAME", "DEVICE_PASSWORD"]
    all_good = True
    for var in required:
        val = os.environ.get(var)
        if val:
            ok(f"{var} is set")
        else:
            fail(f"{var} is NOT set — check your .env file")
            all_good = False
    return all_good


def test_groq_connection():
    header("2. Testing Groq API connection...")
    try:
        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": "Reply with just the word: OK"}],
            max_tokens=10,
            temperature=0
        )
        reply = response.choices[0].message.content.strip()
        if "OK" in reply.upper():
            ok(f"Groq API responding — model replied: {reply}")
            return True
        else:
            warn(f"Groq API responded but unexpected reply: {reply}")
            return True
    except Exception as e:
        fail(f"Groq API connection failed: {str(e)}")
        return False


def test_napalm_connections():
    header("3. Testing NAPALM connections to devices...")
    import napalm

    username = os.environ.get("DEVICE_USERNAME", "admin")
    password = os.environ.get("DEVICE_PASSWORD", "admin")
    all_good = True

    for hostname in get_all_devices():
        try:
            cfg = get_napalm_config(hostname, username, password)
            driver = napalm.get_network_driver("eos")
            device = driver(**cfg)
            device.open()
            facts = device.get_facts()
            device.close()
            ok(f"{hostname} — connected — EOS {facts.get('os_version', 'unknown')}")
        except Exception as e:
            fail(f"{hostname} — {str(e)}")
            all_good = False

    return all_good


def test_imports():
    header("4. Testing module imports...")
    # ---------------------------------------------------------------------------
    # Import each module directly by filename since we added their directories
    # to sys.path above — no package prefix needed
    # ---------------------------------------------------------------------------
    modules = [
        ("network_tools",     "network_tools"),
        ("groq_client",       "groq_client"),
        ("playbook_generator","playbook_generator"),
        ("remediation",       "remediation"),
        ("fault_definitions", "fault_definitions"),
    ]
    all_good = True
    for module_path, label in modules:
        try:
            __import__(module_path)
            ok(f"{label} imported successfully")
        except Exception as e:
            fail(f"{label} import failed: {str(e)}")
            all_good = False
    return all_good


def main():
    print("=" * 50)
    print(" Bantu Smoke Test")
    print("=" * 50)

    results = []
    results.append(test_env_variables())
    results.append(test_groq_connection())
    results.append(test_imports())
    results.append(test_napalm_connections())

    print("\n" + "=" * 50)
    if all(results):
        print(f"{GREEN} All checks passed — Bantu is ready{RESET}")
    else:
        print(f"{RED} Some checks failed — fix issues above before running Bantu{RESET}")
    print("=" * 50)


if __name__ == "__main__":
    main()
