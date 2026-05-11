import os
import socket
import requests
import time
import csv
import threading
import urllib3
from urllib.parse import urlparse, urlunparse
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
SSL_VERIFY = str(os.getenv("SSL_VERIFY", "false")).strip().lower() in (
    "1", "true", "yes", "on"
)


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

def add_scope_to_link_local_url(url, interface=None):
    """
    Adds IPv6 zone/scope to link-local target URLs when needed.

    Example:
      http://[fe80::abcd]:8080
    becomes:
      http://[fe80::abcd%25ens33]:8080

    Only applies to fe80::/10 addresses and only when interface is set.
    """
    if not interface:
        return url

    try:
        parsed = urlparse(url)
        host = parsed.hostname

        if not host:
            return url

        # Only link-local IPv6 needs interface scope in the URL.
        if not host.lower().startswith("fe80:"):
            return url

        # Scope already present.
        if "%" in host:
            return url

        scoped_host = f"{host}%25{interface}"

        if parsed.port:
            netloc = f"[{scoped_host}]:{parsed.port}"
        else:
            netloc = f"[{scoped_host}]"

        return urlunparse((
            parsed.scheme,
            netloc,
            parsed.path or "/",
            parsed.params,
            parsed.query,
            parsed.fragment
        ))

    except Exception:
        return url

# ============================================================
#  SOURCE IP ADAPTER
# ============================================================

class SourceIPAdapter(HTTPAdapter):

    def __init__(self, source_ip, interface=None, **kwargs):
        self.source_ip = source_ip
        self.interface = interface.strip() if interface else None
        self._use_v6   = is_ipv6(source_ip)
        super().__init__(**kwargs)

    def _apply_socket_options(self, kwargs):
        """
        Bind outgoing reachability socket to a selected Linux interface.
        This is useful when the tester has multiple interfaces and the user
        wants reachability probes to use a different interface than the main test.
        """
        if not self.interface:
            return kwargs

        try:
            from urllib3.connection import HTTPConnection
            socket_options = list(HTTPConnection.default_socket_options)
        except Exception:
            socket_options = []

        # Linux SO_BINDTODEVICE. On some systems this may require elevated privileges.
        so_bindtodevice = getattr(socket, "SO_BINDTODEVICE", 25)
        socket_options.append(
            (socket.SOL_SOCKET, so_bindtodevice, self.interface.encode() + b"\0")
        )

        kwargs["socket_options"] = socket_options
        return kwargs

    def init_poolmanager(self, *args, **kwargs):
        kwargs["source_address"] = (self.source_ip, 0)
        kwargs = self._apply_socket_options(kwargs)
        return super().init_poolmanager(*args, **kwargs)

    def proxy_manager_for(self, proxy, **proxy_kwargs):
        proxy_kwargs["source_address"] = (self.source_ip, 0)
        proxy_kwargs = self._apply_socket_options(proxy_kwargs)
        return super().proxy_manager_for(proxy, **proxy_kwargs)


# ============================================================
#  REACHABILITY CHECK
# ============================================================

def run(source_ip=SOURCE_IP, url=URL, interval=INTERVAL,
        duration=DURATION, timeout=TIMEOUT, csv_file=CSV_FILE,
        stop_event=None, interface=None, ssl_verify=SSL_VERIFY):
    """
    Spustí reachability check zo zdrojovej IP voči URL.
    Výsledky ukladá do CSV súboru.

    Args:
        stop_event: voliteľný threading.Event — umožňuje zastaviť
                    beh zvonku (napr. z GUI vlákna).
    """
    validate_source_ip(source_ip)

    interface = interface.strip() if interface else None
    url = add_scope_to_link_local_url(url, interface)
    if not ssl_verify:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    if stop_event is None:
        stop_event = threading.Event()

    session = requests.Session()
    session.headers.update({"Connection": "close"})
    adapter = SourceIPAdapter(source_ip, interface=interface)
    session.mount("http://",  adapter)
    session.mount("https://", adapter)

    dir_path = os.path.dirname(csv_file)
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)

    ip_ver = "IPv6" if is_ipv6(source_ip) else "IPv4"
    iface_text = interface if interface else "auto"
    print(f"Reachability check | src: {source_ip} ({ip_ver}) | iface: {iface_text} -> {url}")
    print(f"Interval: {interval}s | Duration: {duration}s | "
          f"Timeout: {timeout}s | SSL verify: {ssl_verify} | CSV: {csv_file}")
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
                    r       = session.get(url, timeout=timeout,verify=ssl_verify)
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

