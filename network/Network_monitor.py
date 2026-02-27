import os
import time
import threading
import csv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")


class NetworkMonitor:
    def __init__(self, interface="ens33", interval=1, output_file=None):
        self.interface   = interface
        self.interval    = interval
        self.output_file = output_file or os.path.join(DATA_DIR, "network_usage.csv")
        self.running     = False
        self.thread      = None

    def _read_net_dev(self):
        """Read network statistics from /proc/net/dev"""
        try:
            with open("/proc/net/dev", "r") as f:
                for line in f:
                    if self.interface + ":" in line:
                        parts    = line.split(":")[1].split()
                        rx_total = int(parts[0])
                        tx_total = int(parts[8])
                        return rx_total, tx_total
        except (FileNotFoundError, IndexError, ValueError) as e:
            print(f"Error reading network stats: {e}")
        return None, None

    def verify_interface(self):
        """Check if interface exists"""
        rx, tx = self._read_net_dev()
        return rx is not None

    def list_interfaces(self):
        """List all available network interfaces"""
        interfaces = []
        try:
            with open("/proc/net/dev", "r") as f:
                for line in f:
                    if ":" in line and not line.strip().startswith("Inter"):
                        iface = line.split(":")[0].strip()
                        interfaces.append(iface)
        except Exception as e:
            print(f"Error listing interfaces: {e}")
        return interfaces

    def _monitor_loop(self):
        """Main monitoring loop that collects network statistics"""
        prev_rx, prev_tx = self._read_net_dev()
        if prev_rx is None:
            print(f"Interface {self.interface} not found.")
            return

        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)

        try:
            with open(self.output_file, "w", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["timestamp", "rx_total", "tx_total", "rx_kbps", "tx_kbps"])

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
                    csvfile.flush()

        except Exception as e:
            print(f"Error in monitoring loop: {e}")

    def start(self):
        """Start network monitoring in a separate thread"""
        if self.running:
            print("Network monitoring is already running.")
            return

        if not self.verify_interface():
            print(f"Error: Interface '{self.interface}' not found!")
            print("Available interfaces:")
            for iface in self.list_interfaces():
                print(f"  - {iface}")
            return

        self.running = True
        self.thread  = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        print(f"Network monitoring started on {self.interface}...")

    def stop(self):
        """Stop network monitoring"""
        if not self.running:
            print("Network monitoring is not running.")
            return

        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        print(f"Network monitoring stopped. CSV saved to {self.output_file}")


if __name__ == "__main__":
    monitor = NetworkMonitor(interface="ens33", interval=1)

    try:
        monitor.start()
        time.sleep(10)
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    finally:
        monitor.stop()

