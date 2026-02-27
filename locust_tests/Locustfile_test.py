from locust import events, HttpUser, task, between
from datetime import datetime
import os
import socket
import csv
import random
from requests.adapters import HTTPAdapter
import threading
import time
import sys
from pathlib import Path

BASE_DIR      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR      = os.path.join(BASE_DIR, "data")

IP_POOL_FILE  = os.path.join(BASE_DIR, "ip_pool.txt")
METADATA_FILE = os.path.join(DATA_DIR, "report_metadata.csv")
NETWORK_FILE  = os.path.join(DATA_DIR, "network_usage.csv")
PORT_POOL_FILE = os.path.join(BASE_DIR, "port_pool.txt")


# ============================================================
#  HELPER FUNCTIONS
# ============================================================

def parse_ports(port_str):
    """
    "1024-65535"     → list(range(1024, 65536))
    "1025,1620,3550" → [1025, 1620, 3550]
    ""  alebo  None  → None  (OS vyberie port sám = 0)
    """
    if not port_str or not port_str.strip():
        return None
    port_str = port_str.strip()
    if "-" in port_str and "," not in port_str:
        parts = port_str.split("-")
        return list(range(int(parts[0]), int(parts[1]) + 1))
    else:
        return [int(p.strip()) for p in port_str.split(",")]


def load_ip_pool():
    """Load IP addresses from file with validation"""
    if not Path(IP_POOL_FILE).exists():
        print(f"ERROR: {IP_POOL_FILE} not found!")
        sys.exit(1)
    try:
        with open(IP_POOL_FILE) as f:
            ips = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        if not ips:
            print(f"ERROR: {IP_POOL_FILE} is empty!")
            sys.exit(1)
        print(f"✓ Loaded {len(ips)} IP addresses from {IP_POOL_FILE}")
        return ips
    except Exception as e:
        print(f"ERROR: Failed to load IP pool: {e}")
        sys.exit(1)


def load_port_pool():
    """Load port pool from file (optional)"""
    if not Path(PORT_POOL_FILE).exists():
        return None
    try:
        with open(PORT_POOL_FILE) as f:
            content = f.read().strip()
        ports = parse_ports(content)
        if ports:
            print(f"✓ Loaded {len(ports)} ports from {PORT_POOL_FILE}")
        return ports
    except Exception as e:
        print(f"WARNING: Failed to load port pool: {e}")
        return None


def detect_network_interface():
    """Auto-detect primary network interface"""
    try:
        with open("/proc/net/dev", "r") as f:
            lines = f.readlines()[2:]
            for line in lines:
                interface = line.split(":")[0].strip()
                if interface != "lo" and not interface.startswith("docker"):
                    return interface
    except Exception:
        pass
    return "eth0"


# ============================================================
#  NETWORK MONITOR
# ============================================================

class NetworkMonitor:
    def __init__(self, interface="ens33", interval=1, output_file=None):
        self.interface   = interface
        self.interval    = interval
        self.output_file = output_file or NETWORK_FILE
        self.running     = False
        self.thread      = None

    def _read_net_dev(self):
        try:
            with open("/proc/net/dev", "r") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith(self.interface + ":"):
                        parts    = line.split(":")[1].split()
                        rx_total = int(parts[0])
                        tx_total = int(parts[8])
                        return rx_total, tx_total
        except (FileNotFoundError, IndexError, ValueError) as e:
            print(f"Error reading /proc/net/dev: {e}")
        return None, None

    def _monitor_loop(self):
        prev_rx, prev_tx = self._read_net_dev()
        if prev_rx is None:
            print(f"ERROR: Interface {self.interface} not found.")
            return

        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)

        try:
            with open(self.output_file, "w", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["timestamp", "rx_total", "tx_total", "rx_kbps", "tx_kbps"])
                writer.writerow([int(time.time()), prev_rx, prev_tx, 0.0, 0.0])
                csvfile.flush()

                flush_counter = 0
                while self.running:
                    time.sleep(self.interval)
                    rx_total, tx_total = self._read_net_dev()
                    if rx_total is None:
                        continue

                    rx_diff = max(0, rx_total - prev_rx)
                    tx_diff = max(0, tx_total - prev_tx)
                    rx_kbps = rx_diff / 1024
                    tx_kbps = tx_diff / 1024
                    prev_rx, prev_tx = rx_total, tx_total

                    writer.writerow([
                        int(time.time()),
                        rx_total,
                        tx_total,
                        round(rx_kbps, 3),
                        round(tx_kbps, 3)
                    ])

                    flush_counter += 1
                    if flush_counter >= 10:
                        csvfile.flush()
                        flush_counter = 0
        except Exception as e:
            print(f"ERROR in network monitor: {e}")

    def start(self):
        if self.running:
            print("Network monitor already running")
            return
        self.running = True
        self.thread  = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        print(f"✓ Network monitoring started on interface '{self.interface}'")

    def stop(self):
        if not self.running:
            return
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
        print(f"✓ Network monitoring stopped. Data saved to {self.output_file}")


# ============================================================
#  TEST METADATA & EVENTS
# ============================================================

TEST_TYPE       = "Locust Load Test"
start_time      = None
target_host     = None
target_ip       = None
network_monitor = None

@events.init.add_listener
def on_locust_init(environment, **kwargs):
    global network_monitor
    if hasattr(environment.runner, 'worker_index'):
        print("This is a worker process - network monitoring disabled")
        return
    interface       = detect_network_interface()
    network_monitor = NetworkMonitor(interface=interface, interval=1)
    print(f"Network monitor initialized for interface: {interface}")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    global start_time, target_host, target_ip
    if hasattr(environment.runner, 'worker_index'):
        return

    start_time  = datetime.now()
    target_host = environment.host or "Unknown"
    try:
        clean_host = target_host.replace("https://", "").replace("http://", "").split("/")[0]
        target_ip  = socket.gethostbyname(clean_host)
    except Exception as e:
        print(f"Warning: Could not resolve hostname: {e}")
        target_ip  = "Unknown"

    print(f"\n{'='*50}")
    print(f"Test started at: {start_time}")
    print(f"Target: {target_host} ({target_ip})")
    print(f"{'='*50}\n")

    if network_monitor:
        network_monitor.start()


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    global start_time, target_host, target_ip
    if hasattr(environment.runner, 'worker_index'):
        return

    if network_monitor:
        network_monitor.stop()

    end_time = datetime.now()
    duration = end_time - start_time if start_time else "Unknown"

    print(f"\n{'='*50}")
    print(f"Test ended at: {end_time}")
    print(f"Duration: {duration}")
    print(f"{'='*50}\n")

    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(METADATA_FILE, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["start_time", "end_time", "duration", "test_type", "target_host", "target_ip"])
            writer.writerow([start_time, end_time, str(duration), TEST_TYPE, environment.host, target_ip])
        print(f"✓ Metadata saved to {METADATA_FILE}")
    except Exception as e:
        print(f"✗ Failed to save metadata: {e}")


# ============================================================
#  ADAPTER FOR SOURCE IP + PORT
# ============================================================

class SourceIPAdapter(HTTPAdapter):
    """HTTP adapter that binds to a specific source IP and optional port"""
    def __init__(self, source_ip, source_port=0, **kwargs):
        self.source_ip   = source_ip
        self.source_port = source_port  # 0 = OS vyberie sám
        super().__init__(**kwargs)

    def init_poolmanager(self, *args, **kwargs):
        kwargs['source_address'] = (self.source_ip, self.source_port)
        return super().init_poolmanager(*args, **kwargs)


# ============================================================
#  USER CLASS
# ============================================================

class MyUser(HttpUser):
    _ip_pool      = None
    _port_pool    = None
    _ip_pool_lock = threading.Lock()
    wait_time     = between(1, 2)

    @classmethod
    def get_ip_pool(cls):
        """Thread-safe lazy loading of IP pool"""
        if cls._ip_pool is None:
            with cls._ip_pool_lock:
                if cls._ip_pool is None:
                    cls._ip_pool = load_ip_pool()
        return cls._ip_pool

    @classmethod
    def get_port_pool(cls):
        """Thread-safe lazy loading of port pool"""
        if cls._port_pool is None:
            with cls._ip_pool_lock:
                if cls._port_pool is None:
                    cls._port_pool = load_port_pool() or []
        return cls._port_pool

    def on_start(self):
        """Called when a user starts"""
        ip_pool        = self.get_ip_pool()
        self.source_ip = random.choice(ip_pool)

        port_pool         = self.get_port_pool()
        self.source_port  = random.choice(port_pool) if port_pool else 0

        print(f"User started → IP: {self.source_ip}  Port: {self.source_port or 'random'}")

        adapter = SourceIPAdapter(self.source_ip, self.source_port)
        self.client.mount("http://",  adapter)
        self.client.mount("https://", adapter)

    @task
    def index(self):
        """Main task - request index page"""
        self.client.get("/")

