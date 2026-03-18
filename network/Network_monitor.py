import time
import threading
import csv
import os

class NetworkMonitor:
    def __init__(self, interface="ens33", interval=1, output_file="network_usage.csv"):
        self.interface   = interface
        self.interval    = interval
        self.output_file = output_file
        self.running     = False
        self.thread      = None

    def _read_net_dev(self):
        """Prečíta RX/TX bajty pre zadané rozhranie z /proc/net/dev."""
        try:
            with open("/proc/net/dev", "r") as f:
                for line in f:
                    # OPRAVA: strip() + startswith() zabráni falošnému matchovaniu
                    # napr. "ens3:" by chybne matchovalo aj riadok "ens33:"
                    if line.strip().startswith(self.interface + ":"):
                        parts    = line.split(":")[1].split()
                        rx_total = int(parts[0])   # Stĺpec 1  = prijaté bajty (RX)
                        tx_total = int(parts[8])   # Stĺpec 9  = odoslané bajty (TX)
                        return rx_total, tx_total
        except (FileNotFoundError, IndexError, ValueError) as e:
            print(f"Error reading network stats: {e}")
        return None, None

    def verify_interface(self):
        """Overí, či zadané rozhranie existuje na tomto systéme."""
        rx, tx = self._read_net_dev()
        return rx is not None

    def list_interfaces(self):
        """Vráti zoznam všetkých dostupných sieťových rozhraní."""
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
        """Hlavná monitorovacia slučka – beží v samostatnom vlákne."""
        prev_rx, prev_tx = self._read_net_dev()
        if prev_rx is None:
            print(f"Interface {self.interface} not found.")
            return

        try:
            with open(self.output_file, "w", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["timestamp", "rx_total", "tx_total", "rx_kbps", "tx_kbps"])
                writer.writerow([int(time.time()), prev_rx, prev_tx, 0.0, 0.0])
                csvfile.flush()

                while self.running:
                    t_before = time.time()
                    time.sleep(self.interval)
                    actual_elapsed = time.time() - t_before  # skutočný interval

                    rx_total, tx_total = self._read_net_dev()
                    if rx_total is None:
                        continue

                    rx_diff = max(0, rx_total - prev_rx)
                    tx_diff = max(0, tx_total - prev_tx)

                    rx_kBps = rx_diff / 1024 / actual_elapsed
                    tx_kBps = tx_diff / 1024 / actual_elapsed

                    prev_rx, prev_tx = rx_total, tx_total

                    writer.writerow([
                        int(time.time()),
                        rx_total,
                        tx_total,
                        round(rx_kBps, 3),
                        round(tx_kBps, 3)
                    ])
                    csvfile.flush()

        except Exception as e:
            print(f"Error in monitoring loop: {e}")

    def start(self):
        """Spustí monitoring v daemonickom vlákne na pozadí."""
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
        """Zastaví monitoring a počká kým vlákno korektne skončí (max 5 s)."""
        if not self.running:
            print("Network monitoring is not running.")
            return

        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        print(f"Network monitoring stopped. CSV saved to {self.output_file}")


if __name__ == "__main__":
    _out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "network_usage.csv")
    monitor = NetworkMonitor(interface="ens33", interval=1, output_file=_out)

    try:
        monitor.start()
        time.sleep(10)
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    finally:
        monitor.stop()

