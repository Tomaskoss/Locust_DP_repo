#!/usr/bin/env bash
set -euo pipefail

# ============================================================
#  DP Locust Tester Preparation Script
#  Installs all packages needed to run the Locust GUI project.
# ============================================================

export DEBIAN_FRONTEND=noninteractive

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${PROJECT_DIR}/locust_env"

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
pkg-config
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
ethtool
iperf3
iftop
bmon
htop
procps
"

GRAPHIC_PACKAGES="
tk-dev
libjpeg-dev
zlib1g-dev
fonts-dejavu-core
"

sudo apt-get install -y \
  ${PYTHON_PACKAGES} \
  ${DEV_PACKAGES} \
  ${NETWORK_PACKAGES} \
  ${GRAPHIC_PACKAGES}

echo "▶ Creating Python virtual environment..."

if [ ! -d "${VENV_DIR}" ]; then
  python3 -m venv "${VENV_DIR}"
else
  echo "ℹ Virtual environment already exists: ${VENV_DIR}"
fi

source "${VENV_DIR}/bin/activate"

echo "▶ Upgrading pip..."
python -m pip install --upgrade pip setuptools wheel

echo "▶ Installing Python dependencies..."

python -m pip install \
  ctktooltip==0.9 \
  customtkinter==5.2.2 \
  gevent==25.9.1 \
  locust==2.43.4 \
  matplotlib==3.10.9 \
  pandas==3.0.2 \
  pyhanko==0.35.1 \
  python-dotenv==1.2.2 \
  reportlab==4.4.10 \
  requests==2.33.1 \
  scapy==2.7.0 \
  pillow==12.2.0 \
  psutil==7.1.3 \
  numpy==2.4.4

echo "▶ Creating required project directories..."

mkdir -p "${PROJECT_DIR}/data"
mkdir -p "${PROJECT_DIR}/report"
mkdir -p "${PROJECT_DIR}/IP_pool"
mkdir -p "${PROJECT_DIR}/network"
mkdir -p "${PROJECT_DIR}/locust_tests"

echo "▶ Setting executable permissions for shell scripts..."
find "${PROJECT_DIR}" -maxdepth 2 -name "*.sh" -exec chmod +x {} \;

echo "▶ Verifying Python imports..."

python - <<'PY'
import importlib

modules = {
    "tkinter": "tkinter",
    "customtkinter": "customtkinter",
    "ctktooltip": "ctktooltip",
    "gevent": "gevent",
    "locust": "locust",
    "matplotlib": "matplotlib",
    "pandas": "pandas",
    "pyhanko": "pyhanko",
    "python-dotenv": "dotenv",
    "reportlab": "reportlab",
    "requests": "requests",
    "scapy": "scapy.all",
    "pillow": "PIL",
    "psutil": "psutil",
    "numpy": "numpy",
}

for package_name, import_name in modules.items():
    importlib.import_module(import_name)
    print(f"✓ {package_name}")

print("✓ Python dependencies OK")
PY

echo "▶ Verifying system tools..."

for tool in ip ping ifconfig tcpdump traceroute nload ethtool iperf3 iftop bmon htop; do
  if command -v "$tool" >/dev/null 2>&1; then
    echo "✓ $tool"
  else
    echo "⚠ $tool not found"
  fi
done

echo "============================================================"
echo "✓ Tester environment is ready"
echo
echo "To start the GUI:"
echo "  cd ${PROJECT_DIR}"
echo "  source locust_env/bin/activate"
echo "  python3 locust_gui.py"
echo "============================================================"
