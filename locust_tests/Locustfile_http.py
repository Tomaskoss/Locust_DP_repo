from locust import events, HttpUser, task, between
from datetime import datetime
from dotenv import load_dotenv
import os
import socket
import csv
import random
import threading
import time
import sys
from pathlib import Path
from requests.adapters import HTTPAdapter
import urllib3.util.connection as urllib3_conn
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "network"))
from Network_monitor import NetworkMonitor

BASE_DIR       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR       = os.path.join(BASE_DIR, "data")
IP_POOL_FILE   = os.path.join(BASE_DIR, "ip_pool.txt")
PORT_POOL_FILE = os.path.join(BASE_DIR, "port_pool.txt")
METADATA_FILE  = os.path.join(DATA_DIR, "report_metadata.csv")
NETWORK_FILE   = os.path.join(DATA_DIR, "network_usage.csv")

load_dotenv(dotenv_path=os.path.join(BASE_DIR, ".env"))


# ============================================================
#  HELPER FUNCTIONS
# ============================================================

def is_ipv6(ip):
    """Vráti True ak je ip platná IPv6 adresa."""
    try:
        socket.inet_pton(socket.AF_INET6, ip)
        return True
    except (socket.error, OSError):
        return False


def parse_ports(port_str):
    if not port_str or not port_str.strip():
        return None
    port_str = port_str.strip()
    if "-" in port_str and "," not in port_str:
        parts = port_str.split("-")
        return list(range(int(parts[0]), int(parts[1]) + 1))
    else:
        return [int(p.strip()) for p in port_str.split(",")]


def load_ip_pool():
    if not Path(IP_POOL_FILE).exists():
        print(f"ERROR: {IP_POOL_FILE} not found!")
        sys.exit(1)
    try:
        with open(IP_POOL_FILE) as f:
            ips = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        if not ips:
            print(f"ERROR: {IP_POOL_FILE} is empty!")
            sys.exit(1)
        v6_count = sum(1 for ip in ips if is_ipv6(ip))
        v4_count = len(ips) - v6_count
        print(f"✓ Loaded {len(ips)} IP addresses from {IP_POOL_FILE} "
              f"(IPv4: {v4_count}, IPv6: {v6_count})")
        return ips
    except Exception as e:
        print(f"ERROR: Failed to load IP pool: {e}")
        sys.exit(1)


def load_port_pool():
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
    try:
        with open("/proc/net/dev", "r") as f:
            lines = f.readlines()[2:]
            for line in lines:
                interface = line.split(":")[0].strip()
                if interface != "lo" and not interface.startswith("docker"):
                    return interface
    except Exception:
        pass
    return "ens33"



# ============================================================
#  TEST METADATA & EVENTS
# ============================================================

TEST_TYPE       = os.getenv("TEST_TYPE", "Locust Load Test")
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
    interface       = os.getenv("INTERFACE") or detect_network_interface()
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
        clean_host = (
            target_host
            .replace("https://", "")
            .replace("http://", "")
            .split("/")[0]
        )

        if clean_host.startswith("["):
            clean_host = clean_host.split("]")[0].lstrip("[")
        else:
            clean_host = clean_host.split(":")[0]

        try:
            socket.inet_pton(socket.AF_INET6, clean_host)
            target_ip = clean_host
            print(f"Target is IPv6 address: {target_ip}")
        except OSError:
            try:
                socket.inet_pton(socket.AF_INET, clean_host)
                target_ip = clean_host
                print(f"Target is IPv4 address: {target_ip}")
            except OSError:
                try:
                    infos     = socket.getaddrinfo(clean_host, None, socket.AF_INET6)
                    target_ip = infos[0][4][0]
                    print(f"Resolved {clean_host} → {target_ip} (IPv6)")
                except socket.gaierror:
                    target_ip = socket.gethostbyname(clean_host)
                    print(f"Resolved {clean_host} → {target_ip} (IPv4)")

    except Exception as e:
        print(f"Warning: Could not resolve hostname: {e}")
        target_ip = "Unknown"

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
            writer.writerow(["start_time", "end_time", "duration",
                             "test_type", "target_host", "target_ip"])
            writer.writerow([start_time, end_time, str(duration),
                             TEST_TYPE, environment.host, target_ip])
        print(f"✓ Metadata saved to {METADATA_FILE}")
    except Exception as e:
        print(f"✗ Failed to save metadata: {e}")


# ============================================================
#  SOURCE IP + PORT ADAPTER  (IPv4 + IPv6)
# ============================================================

class SourceIPAdapter(HTTPAdapter):
    def __init__(self, source_ip, source_port=0, **kwargs):
        self.source_ip   = source_ip
        self.source_port = source_port
        self._use_v6     = is_ipv6(source_ip)
        super().__init__(**kwargs)

    def init_poolmanager(self, *args, **kwargs):
        kwargs["source_address"] = (self.source_ip, self.source_port)
        super().init_poolmanager(*args, **kwargs)

    def send(self, request, **kwargs):
        old_create = urllib3_conn.create_connection
        src_ip     = self.source_ip
        src_port   = self.source_port
        use_v6     = self._use_v6

        def patched_create(address, timeout=None, source_address=None,
                           socket_options=None):
            host, port = address
            af    = socket.AF_INET6 if use_v6 else socket.AF_INET
            infos = socket.getaddrinfo(host, port, af, socket.SOCK_STREAM)
            af, socktype, proto, _, sockaddr = infos[0]
            sock  = socket.socket(af, socktype, proto)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            if socket_options:
                for opt in socket_options:
                    sock.setsockopt(*opt)
            if use_v6:
                sock.bind((src_ip, src_port, 0, 0))
            else:
                sock.bind((src_ip, src_port))
            sock.settimeout(timeout)
            sock.connect(sockaddr)
            return sock

        urllib3_conn.create_connection = patched_create
        try:
            result = super().send(request, **kwargs)
        finally:
            urllib3_conn.create_connection = old_create
        return result


# ============================================================
#  USER CLASS
# ============================================================

class MyUser(HttpUser):
    _ip_pool   = None
    _port_pool = None
    _pool_lock = threading.Lock()
    wait_time  = between(1, 2)

    @classmethod
    def get_ip_pool(cls):
        if cls._ip_pool is None:
            with cls._pool_lock:
                if cls._ip_pool is None:
                    cls._ip_pool = load_ip_pool()
        return cls._ip_pool

    @classmethod
    def get_port_pool(cls):
        if cls._port_pool is None:
            with cls._pool_lock:
                if cls._port_pool is None:
                    cls._port_pool = load_port_pool() or []
        return cls._port_pool

    def on_start(self):
        ip_pool          = self.get_ip_pool()
        self.source_ip   = random.choice(ip_pool)

        port_pool        = self.get_port_pool()
        self.source_port = random.choice(port_pool) if port_pool else 0

        print(
            f"User started → IP: {self.source_ip} "
            f"({'IPv6' if is_ipv6(self.source_ip) else 'IPv4'})  "
            f"Port: {self.source_port if self.source_port else 'random (OS)'}"
        )

        adapter = SourceIPAdapter(self.source_ip, self.source_port)
        self.client.mount("http://",  adapter)
        self.client.mount("https://", adapter)

    @task
    def index(self):
        self.client.get("/")

