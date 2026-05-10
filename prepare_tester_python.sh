#!/usr/bin/env bash
set -euo pipefail

# ============================================================
#  DP Locust Tester Preparation Script
#  Installs all packages needed to run the Locust GUI project.
# ============================================================

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${PROJECT_DIR}/locust_env"
REQ_FILE="${PROJECT_DIR}/requirements.txt"

echo "============================================================"
echo " Preparing Locust tester environment"
echo " Project directory: ${PROJECT_DIR}"
echo "============================================================"

echo "▶ Updating package lists..."
sudo apt-get update

echo "▶ Installing system packages..."

PYTHON_PACKAGES="
python3
python3-pip
python3-venv
python3-tk
python3-dev
"

DEV_PACKAGES="
git
curl
wget
unzip
zip
build-essential
xdg-utils
ca-certificates
"

NETWORK_PACKAGES="
iproute2
iputils-ping
net-tools
tcpdump
traceroute
nload
netsniff-ng
libpcap-dev
libssl-dev
openssl
"

sudo apt-get install -y \
  ${PYTHON_PACKAGES} \
  ${DEV_PACKAGES} \
  ${NETWORK_PACKAGES}

echo "▶ Creating Python virtual environment..."

if [ ! -d "${VENV_DIR}" ]; then
  python3 -m venv "${VENV_DIR}"
else
  echo "ℹ Virtual environment already exists: ${VENV_DIR}"
fi

source "${VENV_DIR}/bin/activate"

echo "▶ Upgrading pip..."
python -m pip install --upgrade pip setuptools wheel

echo "▶ Creating requirements.txt if missing..."

if [ ! -f "${REQ_FILE}" ]; then
cat > "${REQ_FILE}" <<EOF
locust
requests
pandas
matplotlib
reportlab
python-dotenv
customtkinter
CTkToolTip
pyhanko
EOF
fi

echo "▶ Installing Python dependencies..."
pip install -r "${REQ_FILE}"

echo "▶ Creating required project directories..."
mkdir -p "${PROJECT_DIR}/data"
mkdir -p "${PROJECT_DIR}/report"
mkdir -p "${PROJECT_DIR}/IP_pool"
mkdir -p "${PROJECT_DIR}/network"
mkdir -p "${PROJECT_DIR}/locust_tests"

echo "▶ Creating default config.env if missing..."

if [ ! -f "${PROJECT_DIR}/config.env" ]; then
cat > "${PROJECT_DIR}/config.env" <<EOF
# ══════════════════════════════════════════════
#  LOCUST
# ══════════════════════════════════════════════
TARGET_HOST='http://127.0.0.1:8080'
PROCESSES='-1'
TEST_TYPE='Load Test'
STOP_TIMEOUT='30'
CONNECT_TIMEOUT='3'
READ_TIMEOUT='10'

# ══════════════════════════════════════════════
#  HTTP/S REQUEST
# ══════════════════════════════════════════════
HTTP_METHOD='GET'
ENDPOINT_PATH='/'
REQUEST_BODY='{"message": "hello", "user": "test"}'
SSL_VERIFY='false'
REQUEST_FAILURE_THRESHOLD='1'

# ══════════════════════════════════════════════
#  NETWORK / IP POOL
# ══════════════════════════════════════════════
INTERFACE='ens33'
IP_VERSION='ipv4'

IP_START='192.168.100.100'
IP_END='192.168.100.120'
IPV4PREFIX='32'

IP6_START='fd00:100::1000'
IP6_END='fd00:100::1050'
IP6_PREFIX='fd00:100::/64'
IPV6_MODE='range'
IPV6RPREFIX='64'

# ══════════════════════════════════════════════
#  REACHABILITY
# ══════════════════════════════════════════════
REACH_INTERVAL='5'
REACH_TIMEOUT='5'
REACH_SRC_IP=''
REACH_INTERFACE='ens33'
REACH_THRESHOLD='5'

# ══════════════════════════════════════════════
#  TEST STAGES
#  Duration = duration of one stage, not cumulative time
# ══════════════════════════════════════════════
STAGES='[{"duration": 60, "users": 10, "spawn_rate": 5, "wait_mode": "between", "wait_min": 1.0, "wait_max": 3.0}]'
EOF
else
  echo "ℹ config.env already exists — not overwritten"
fi

echo "▶ Setting executable permissions for shell scripts..."
find "${PROJECT_DIR}" -maxdepth 2 -name "*.sh" -exec chmod +x {} \;

echo "▶ Verifying Python imports..."
python - <<'PY'
import tkinter
import customtkinter
import pandas
import matplotlib
import reportlab
import dotenv
import locust
import requests
print("✓ Python dependencies OK")
PY

echo "============================================================"
echo "✓ Tester environment is ready"
echo
echo "To start the GUI:"
echo "  cd ${PROJECT_DIR}"
echo "  source locust_env/bin/activate"
echo "  python3 locust_gui.py"
echo "============================================================"
