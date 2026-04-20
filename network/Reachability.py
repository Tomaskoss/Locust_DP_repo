import os
import socket
import requests
import time
import csv
import threading
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
CSV_FILE = os.path.join(DATA_DIR, "reachability.csv")

load_dotenv(dotenv_path=os.path.join(BASE_DIR, "config.env"))

SOURCE_IP = os.getenv("REACH_SRC_IP",    "10.10.10.20")
URL       = os.getenv("TARGET_HOST",     "https://www.vut.cz")
INTERVAL  = int(os.getenv("REACH_INTERVAL", 5))
DURATION  = int(os.getenv("RUN_TIME", 10))
TIMEOUT   = float(os.getenv("REACH_TIMEOUT",  5))   


# ============================================================
#  HELPERS
# ============================================================

def is_ipv6(ip):
    try:
        socket.inet_pton(socket.AF_INET6, ip)
        return True
    except (socket.error, OSError):
        return False


def validate_source_ip(ip):
    for family in (socket.AF_INET, socket.AF_INET6):
        try:
            socket.inet_pton(family, ip)
            return
        except OSError:
            pass
    raise ValueError(f"Invalid SOURCE_IP: '{ip}' — must be a valid IPv4 or IPv6 address.")


# ============================================================
#  SOURCE IP ADAPTER
# ============================================================

class SourceIPAdapter(HTTPAdapter):

    def __init__(self, source_ip, **kwargs):
        self.source_ip = source_ip
        self._use_v6   = is_ipv6(source_ip)
        super().__init__(**kwargs)

    

    def init_poolmanager(self, *args, **kwargs):
        kwargs["source_address"] = (self.source_ip, 0)
        return super().init_poolmanager(*args, **kwargs)

    def proxy_manager_for(self, proxy, **proxy_kwargs):
        proxy_kwargs["source_address"] = (self.source_ip, 0)
        return super().proxy_manager_for(proxy, **proxy_kwargs)


# ============================================================
#  REACHABILITY CHECK
# ============================================================

def run(source_ip=SOURCE_IP, url=URL, interval=INTERVAL,
        duration=DURATION, timeout=TIMEOUT, csv_file=CSV_FILE,
        stop_event=None):
    """
    Spustí reachability check zo zdrojovej IP voči URL.
    Výsledky ukladá do CSV súboru.

    Args:
        stop_event: voliteľný threading.Event — umožňuje zastaviť
                    beh zvonku (napr. z GUI vlákna).
    """
    validate_source_ip(source_ip)

    if stop_event is None:
        stop_event = threading.Event()

    
    session = requests.Session()
    session.headers.update({"Connection": "close"})
    adapter = SourceIPAdapter(source_ip)
    session.mount("http://",  adapter)
    session.mount("https://", adapter)

    dir_path = os.path.dirname(csv_file)
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)

    ip_ver = "IPv6" if is_ipv6(source_ip) else "IPv4"
    print(f"Reachability check | src: {source_ip} ({ip_ver}) -> {url}")
    print(f"Interval: {interval}s | Duration: {duration}s | "
          f"Timeout: {timeout}s | CSV: {csv_file}")
    print("-" * 60)

    flush_counter = 0
    start_time    = time.time()

    try:
        with open(csv_file, mode="w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["timestamp", "unix_timestamp",
                             "status_code", "elapsed_time_s", "error"])

            while not stop_event.is_set() and (time.time() - start_time) < duration:

                now            = time.time()
                timestamp      = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now))
                unix_timestamp = round(now, 3)
                t0             = now
                error_msg      = ""

                try:
                    r       = session.get(url, timeout=timeout)
                    elapsed = round(time.time() - t0, 4)
                    status  = r.status_code
                except Exception as e:
                    elapsed   = round(time.time() - t0, 4)
                    status    = 0
                    error_msg = str(e)[:200]

                writer.writerow([timestamp, unix_timestamp,
                                 status, elapsed, error_msg])

                label = str(status) if status else "FAIL"
                print(f"{timestamp}  status={label:>4}  elapsed={elapsed:>8.4f}s"
                      + (f"  ERR: {error_msg}" if error_msg else ""))

                flush_counter += 1
                if flush_counter % 5 == 0:
                    csvfile.flush()

                remaining = duration - (time.time() - start_time)
                if stop_event.wait(timeout=min(interval, max(0.0, remaining))):
                    break

            csvfile.flush()

    except KeyboardInterrupt:
        print("\nReachability check stopped by user.")
    finally:
        session.close()
        print("-" * 60)
        print(f"Done. Results saved to {csv_file}")


if __name__ == "__main__":
    run()

