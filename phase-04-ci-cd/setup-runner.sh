#!/bin/bash
set -e

echo "============================================="
echo "  Netaform Phase 4 - Self-Hosted Runner Setup"
echo "============================================="
echo ""

PASS="✓"
FAIL="✗"
WARN="!"
errors=0

# --- Prerequisite Checks ---
echo "--- Checking Prerequisites ---"
echo ""

# Docker
if command -v docker &> /dev/null; then
    DOCKER_VER=$(docker --version | awk '{print $3}' | tr -d ',')
    echo "  $PASS Docker: $DOCKER_VER"
else
    echo "  $FAIL Docker: NOT INSTALLED"
    echo "    Install: sudo apt update && sudo apt install -y docker.io"
    errors=$((errors + 1))
fi

# Containerlab
if command -v containerlab &> /dev/null; then
    CLAB_VER=$(containerlab version | grep "version:" | awk '{print $2}')
    echo "  $PASS Containerlab: $CLAB_VER"
else
    echo "  $FAIL Containerlab: NOT INSTALLED"
    echo "    Install: sudo bash -c \"\$(curl -sL https://get.containerlab.dev)\""
    errors=$((errors + 1))
fi

# Arista cEOS image
CEOS_IMAGE=$(docker images --format "{{.Repository}}:{{.Tag}}" | grep -i ceos | head -1)
if [ -n "$CEOS_IMAGE" ]; then
    echo "  $PASS Arista cEOS: $CEOS_IMAGE"
else
    echo "  $FAIL Arista cEOS: NO IMAGE FOUND"
    echo "    Download from arista.com and import with: docker import <file> ceos:<version>"
    errors=$((errors + 1))
fi

# Python
if command -v python3 &> /dev/null; then
    PY_VER=$(python3 --version | awk '{print $2}')
    echo "  $PASS Python: $PY_VER"
else
    echo "  $FAIL Python 3: NOT INSTALLED"
    echo "    Install: sudo apt install -y python3 python3-pip"
    errors=$((errors + 1))
fi

# Ansible
if command -v ansible &> /dev/null; then
    ANS_VER=$(ansible --version | head -1 | awk '{print $3}' | tr -d ']')
    echo "  $PASS Ansible: $ANS_VER"
else
    echo "  $WARN Ansible: NOT INSTALLED"
    echo "    Install: pip3 install ansible"
    errors=$((errors + 1))
fi

# Arista EOS Ansible collection
if ansible-galaxy collection list 2>/dev/null | grep -q "arista.eos"; then
    echo "  $PASS Ansible collection: arista.eos"
else
    echo "  $WARN Ansible collection: arista.eos NOT FOUND"
    echo "    Installing arista.eos collection..."
    ansible-galaxy collection install arista.eos
    echo "  $PASS Ansible collection: arista.eos (installed)"
fi

# pytest
if python3 -m pytest --version &> /dev/null; then
    PYTEST_VER=$(python3 -m pytest --version | awk '{print $2}')
    echo "  $PASS pytest: $PYTEST_VER"
else
    echo "  $WARN pytest: NOT INSTALLED"
    echo "    Installing pytest..."
    pip3 install pytest pytest-html
    echo "  $PASS pytest: (installed)"
fi

# NAPALM
if python3 -c "import napalm" &> /dev/null; then
    NAPALM_VER=$(python3 -c "import napalm; print(napalm.__version__)")
    echo "  $PASS NAPALM: $NAPALM_VER"
else
    echo "  $WARN NAPALM: NOT INSTALLED"
    echo "    Installing napalm and napalm-eos..."
    pip3 install napalm
    echo "  $PASS NAPALM: (installed)"
fi

echo ""

# --- Stop if critical tools are missing ---
if [ $errors -gt 0 ]; then
    echo "  $FAIL $errors critical prerequisite(s) missing. Fix them and re-run this script."
    exit 1
fi

echo "  All prerequisites satisfied."
echo ""

# --- GitHub Runner Registration ---
echo "--- GitHub Actions Runner Setup ---"
echo ""

RUNNER_DIR="$HOME/actions-runner"

# Check if runner is already installed
if [ -d "$RUNNER_DIR" ] && [ -f "$RUNNER_DIR/run.sh" ]; then
    echo "  $PASS Runner already installed at $RUNNER_DIR"
    echo ""
    echo "  To start the runner:"
    echo "    cd $RUNNER_DIR && ./run.sh"
    echo ""
    echo "  To reconfigure:"
    echo "    cd $RUNNER_DIR && ./config.sh remove"
    echo "    Then re-run this script."
    exit 0
fi

# Download and install runner
echo "  Downloading GitHub Actions runner..."
mkdir -p "$RUNNER_DIR" && cd "$RUNNER_DIR"

RUNNER_VERSION="2.333.0"
RUNNER_ARCH=$(uname -m)
if [ "$RUNNER_ARCH" = "x86_64" ]; then
    RUNNER_FILE="actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz"
elif [ "$RUNNER_ARCH" = "aarch64" ]; then
    RUNNER_FILE="actions-runner-linux-arm64-${RUNNER_VERSION}.tar.gz"
else
    echo "  $FAIL Unsupported architecture: $RUNNER_ARCH"
    exit 1
fi

curl -sO -L "https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/${RUNNER_FILE}"
tar xzf "$RUNNER_FILE"
rm -f "$RUNNER_FILE"

echo "  $PASS Runner downloaded to $RUNNER_DIR"
echo ""

# Guide user through registration
echo "  --- Registration ---"
echo ""
echo "  1. Go to: https://github.com/rushivt/netaform/settings/actions/runners/new"
echo "  2. Copy the token from the 'Configure' section"
echo "  3. Paste it below"
echo ""
read -p "  Enter your registration token: " REG_TOKEN

if [ -z "$REG_TOKEN" ]; then
    echo "  $FAIL No token provided. Run this to register manually:"
    echo "    cd $RUNNER_DIR && ./config.sh --url https://github.com/rushivt/netaform --token <YOUR_TOKEN> --labels self-hosted,linux,containerlab,ceos"
    exit 1
fi

./config.sh \
    --url https://github.com/rushivt/netaform \
    --token "$REG_TOKEN" \
    --name "netaform-lab" \
    --labels "self-hosted,linux,containerlab,ceos" \
    --work "_work" \
    --unattended

echo ""
echo "  $PASS Runner registered successfully!"
echo ""
echo "============================================="
echo "  Setup Complete"
echo "============================================="
echo ""
echo "  Runner name   : netaform-lab"
echo "  Labels        : self-hosted, linux, containerlab, ceos"
echo "  Location      : $RUNNER_DIR"
echo ""
echo "  To start (interactive):"
echo "    cd $RUNNER_DIR && ./run.sh"
echo ""
echo "  To install as service (starts on boot):"
echo "    cd $RUNNER_DIR"
echo "    sudo ./svc.sh install"
echo "    sudo ./svc.sh start"
echo ""