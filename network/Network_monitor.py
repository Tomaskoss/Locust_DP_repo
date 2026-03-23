import time
import threading
import csv
import os


class NetworkMonitor:

    def __init__(self, interface="ens33", interval=1, output_file="network_usage.csv"):
        self.interface   = interface
        self.interval    = interval
        self.output_file = output_file
        self._stop_event = threading.Event()   #  — thread-safe stop flag
        self.running     = False
        self.thread      = None

    def read_net_dev(self):
        """Prečíta RX/TX bajty pre zadané rozhranie z /proc/net/dev."""
        try:
            with open("/proc/net/dev", "r") as f:
                for line in f:
    
                    iface = line.split(":")[0].strip()
                    if iface == self.interface:
                        parts    = line.split(":")[1].split()
                        rx_total = int(parts[0])
                        tx_total = int(parts[8])
                        return rx_total, tx_total
        except (FileNotFoundError, IndexError, ValueError) as e:
            print(f"Error reading network stats: {e}")
        return None, None

    def verify_interface(self):
        #verifikácia cez /sys/class/net (rýchlejšie, presnejšie).
        return os.path.exists(f"/sys/class/net/{self.interface}")

    def list_interfaces(self):
        """Vráti zoznam všetkých dostupných sieťových rozhraní."""
        interfaces = []
        try:
            with open("/proc/net/dev", "r") as f:
                for line in f:
                    if ":" in line and not line.strip().startswith("Inter"):
                        iface = line.split(":")[0].strip()
                        if iface:
                            interfaces.append(iface)
        except Exception as e:
            print(f"Error listing interfaces: {e}")
        return interfaces

    def monitor_loop(self):
        """Hlavná monitorovacia slučka beží v samostatnom vlákne."""
        prev_rx, prev_tx = self.read_net_dev()
        if prev_rx is None:
            print(f"Interface {self.interface} not found.")
            self.running = False
            return

        flush_counter = 0

        try:
            with open(self.output_file, "w", newline="") as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["timestamp", "rx_total", "tx_total",
                                 "rx_kbps", "tx_kbps"])
                writer.writerow([int(time.time()), prev_rx, prev_tx, 0.0, 0.0])
                csvfile.flush()

                while not self._stop_event.is_set():
                    # — okamžitá reakcia na stop(), bez čakania celý interval
                    if self._stop_event.wait(timeout=self.interval):
                        break

                    rx_total, tx_total = self.read_net_dev()
                    actual_elapsed     = self.interval   # čas merania = interval

                    #  — reset prev pri zlyhaní, zabráni spike v dátach
                    if rx_total is None:
                        prev_rx, prev_tx = None, None
                        continue

                    if prev_rx is None:
                        prev_rx, prev_tx = rx_total, tx_total
                        continue

                    #  — counter overflow (uint64 wrap-around)
                    rx_diff = rx_total if rx_total < prev_rx else rx_total - prev_rx
                    tx_diff = tx_total if tx_total < prev_tx else tx_total - prev_tx

                    #  zabraňuje ZeroDivisionError pri jitter / malý interval
                    actual_elapsed = max(1e-6, actual_elapsed)

                    rx_kBps = rx_diff / 1024 / actual_elapsed
                    tx_kBps = tx_diff / 1024 / actual_elapsed

                    prev_rx, prev_tx = rx_total, tx_total

                    writer.writerow([int(time.time()), rx_total, tx_total,
                                     round(rx_kBps, 3), round(tx_kBps, 3)])

                csvfile.flush()  
        except Exception as e:
            print(f"Error in monitoring loop: {e}")
            self.running = False

    def start(self):
        """Spustí monitoring v daemonickom vlákne na pozadí."""
        if self.running:
            print("Network monitoring is already running.")
            return
        if not self.verify_interface():
            print(f"Error: Interface {self.interface} not found!")
            print("Available interfaces:")
            for iface in self.list_interfaces():
                print(f"  - {iface}")
            return

        self._stop_event.clear()   # reset eventu pred každým štartom
        self.running = True
        self.thread  = threading.Thread(target=self.monitor_loop, daemon=True)
        self.thread.start()
        print(f"Network monitoring started on {self.interface}...")

    def stop(self):
        """Zastaví monitoring a počká kým vlákno korektne skončí (max 5 s)."""
        if not self.running:
            print("Network monitoring is not running.")
            return

        self.running = False
        self._stop_event.set()   #  signalizuj vláknu okamžité ukončenie

        if self.thread:
            self.thread.join(timeout=5)
            # over, či vlákno skutočne skončilo
            if self.thread.is_alive():
                print("WARNING: monitoring thread did not stop within 5s — "
                      "CSV may be incomplete.")
            else:
                print(f"Network monitoring stopped. "
                      f"CSV saved to {self.output_file}")


if __name__ == "__main__":
    out     = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "network_usage.csv")
    monitor = NetworkMonitor(interface="ens33", interval=1, output_file=out)
    try:
        monitor.start()
        time.sleep(10)
    except KeyboardInterrupt:
        print("Stopped by user.")
    finally:
        monitor.stop()

