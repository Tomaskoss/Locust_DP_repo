from locust import events, HttpUser, task, between
from datetime import datetime
import socket
import csv
import random
from requests.adapters import HTTPAdapter
import threading
import time
import sys
from pathlib import Path

# ============================================================
#  NETWORK MONITOR
# ============================================================
class NetworkMonitor:
    def __init__(self, interface="eth0", interval=1, output_file="network_usage.csv"):
        self.interface = interface
        self.interval = interval
        self.output_file = output_file
        self.running = False
        self.thread = None

    def _read_net_dev(self):
        """Read network stats from /proc/net/dev"""
        try:
            with open("/proc/net/dev", "r") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith(self.interface + ":"):
                        parts = line.split(":")[1].split()
                        rx_total = int(parts[0])
                        tx_total = int(parts[8])
                        return rx_total, tx_total
        except (FileNotFoundError, IndexError, ValueError) as e:
            print(f"Error reading /proc/net/dev: {e}")
        return None, None

    def _monitor_loop(self):
        """Main monitoring loop"""
        prev_rx, prev_tx = self._read_net_dev()
        if prev_rx is None:
            print(f"ERROR: Interface {self.interface} not found.")
            return

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
                    
                    # Flush every 10 writes instead of every write
                    flush_counter += 1
                    if flush_counter >= 10:
                        csvfile.flush()
                        flush_counter = 0
        except Exception as e:
            print(f"ERROR in network monitor: {e}")

    def start(self):
        """Start monitoring in background thread"""
        if self.running:
            print("Network monitor already running")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        print(f"✓ Network monitoring started on interface '{self.interface}'")

    def stop(self):
        """Stop monitoring and wait for thread to finish"""
        if not self.running:
            return
            
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
        print(f"✓ Network monitoring stopped. Data saved to {self.output_file}")


# ============================================================
#  HELPER FUNCTIONS
# ============================================================
def detect_network_interface():
    """Auto-detect primary network interface"""
    try:
        with open("/proc/net/dev", "r") as f:
            lines = f.readlines()[2:]  # Skip header lines
            for line in lines:
                interface = line.split(":")[0].strip()
                # Skip loopback
                if interface != "lo" and not interface.startswith("docker"):
                    return interface
    except Exception:
        pass
    return "eth0"  # Fallback


def load_ip_pool():
    """Load IP addresses from file with validation"""
    ip_pool_file = "ip_pool.txt"
    
    if not Path(ip_pool_file).exists():
        print(f"ERROR: {ip_pool_file} not found!")
        sys.exit(1)
    
    try:
        with open(ip_pool_file) as f:
            ips = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        
        if not ips:
            print(f"ERROR: {ip_pool_file} is empty!")
            sys.exit(1)
        
        print(f"✓ Loaded {len(ips)} IP addresses from {ip_pool_file}")
        return ips
    except Exception as e:
        print(f"ERROR: Failed to load IP pool: {e}")
        sys.exit(1)


# ============================================================
#  TEST METADATA & MONITOR
# ============================================================
TEST_TYPE = "Locust Load Test"
start_time = None
target_host = None
target_ip = None
network_monitor = None

@events.init.add_listener
def on_locust_init(environment, **kwargs):
    """Initialize network monitor (runs once per process)"""
    global network_monitor
    
    # Only run on standalone or master, NOT on workers
    if hasattr(environment.runner, 'worker_index'):
        print("This is a worker process - network monitoring disabled")
        return
    
    # Auto-detect interfacenetwork_proc
    interface = detect_network_interface()
    network_monitor = NetworkMonitor(interface=interface, interval=1)
    print(f"Network monitor initialized for interface: {interface}")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when test starts"""
    global start_time, target_host, target_ip
    
    # Skip on workers
    if hasattr(environment.runner, 'worker_index'):
        return

    start_time = datetime.now()
    target_host = environment.host or "Unknown"
    
    # Resolve hostname to IP
    try:
        clean_host = target_host.replace("https://", "").replace("http://", "").split("/")[0]
        target_ip = socket.gethostbyname(clean_host)
    except Exception as e:
        print(f"Warning: Could not resolve hostname: {e}")
        target_ip = "Unknown"

    print(f"\n{'='*50}")
    print(f"Test started at: {start_time}")
    print(f"Target: {target_host} ({target_ip})")
    print(f"{'='*50}\n")

    # Start network monitoring
    if network_monitor:
        network_monitor.start()


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when test stops"""
    global start_time, target_host, target_ip
    
    # Skip on workers
    if hasattr(environment.runner, 'worker_index'):
        return

    # Stop network monitoring first
    if network_monitor:
        network_monitor.stop()

    end_time = datetime.now()
    duration = end_time - start_time if start_time else "Unknown"
    
    print(f"\n{'='*50}")
    print(f"Test ended at: {end_time}")
    print(f"Duration: {duration}")
    print(f"{'='*50}\n")

    # Save metadata
    try:
        with open("report_metadata.csv", "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["start_time", "end_time", "duration", "test_type", "target_host", "target_ip"])
            writer.writerow([start_time, end_time, str(duration), TEST_TYPE, environment.host, target_ip])
        print("✓ Metadata saved to report_metadata.csv")
    except Exception as e:
        print(f"✗ Failed to save metadata: {e}")


# ============================================================
#  ADAPTER FOR SOURCE IP
# ============================================================
class SourceIPAdapter(HTTPAdapter):
    """HTTP adapter that binds to a specific source IP"""
    def __init__(self, source_ip, **kwargs):
        self.source_ip = source_ip
        super().__init__(**kwargs)

    def init_poolmanager(self, *args, **kwargs):
        kwargs['source_address'] = (self.source_ip, 0)
        return super().init_poolmanager(*args, **kwargs)


# ============================================================
#  USER CLASS
# ============================================================
class MyUser(HttpUser):
    # Lazy-load IP pool to handle missing file gracefully
    _ip_pool = None
    _ip_pool_lock = threading.Lock()
    
    wait_time = between(1, 2)

    @classmethod
    def get_ip_pool(cls):
        """Thread-safe lazy loading of IP pool"""
        if cls._ip_pool is None:
            with cls._ip_pool_lock:
                if cls._ip_pool is None:  # Double-check
                    cls._ip_pool = load_ip_pool()
        return cls._ip_pool

    def on_start(self):
        """Called when a user starts"""
        ip_pool = self.get_ip_pool()
        self.source_ip = random.choice(ip_pool)
        print(f"User started with source IP: {self.source_ip}")
        
        # Bind HTTP client to source IP
        adapter = SourceIPAdapter(self.source_ip)
        self.client.mount("http://", adapter)
        self.client.mount("https://", adapter)

    @task
    def index(self):
        """Main task - request index page"""
        self.client.get("/")
