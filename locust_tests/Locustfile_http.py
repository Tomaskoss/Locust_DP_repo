from locust import events, HttpUser, task, LoadTestShape
from locust.runners import WorkerRunner
from datetime import datetime
from dotenv import load_dotenv
import os
import socket
import csv
import random
import threading
import sys
import json
import time as _time
from pathlib import Path
from requests.adapters import HTTPAdapter
import urllib3.util.connection as urllib3_conn
import urllib3


# ============================================================
#  PATHS
# ============================================================

BASE_DIR       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR       = os.path.join(BASE_DIR, "data")
IP_POOL_FILE   = os.path.join(BASE_DIR, "ip_pool.txt")
PORT_POOL_FILE = os.path.join(BASE_DIR, "port_pool.txt")
METADATA_FILE  = os.path.join(DATA_DIR, "report_metadata.csv")

load_dotenv(dotenv_path=os.path.join(BASE_DIR, "config.env"), override=True)


# ============================================================
#  SSL WARNINGS — raz pri štarte procesu, nie per-user
# ============================================================

if os.getenv("SSL_VERIFY", "true").lower() == "false":
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# ============================================================
#  TIMEOUT CONFIG
# ============================================================

try:
    CONNECT_TIMEOUT = float(os.getenv("CONNECT_TIMEOUT", "5"))
    assert CONNECT_TIMEOUT > 0
except (ValueError, AssertionError):
    print("WARNING: Invalid CONNECT_TIMEOUT, using default 5s")
    CONNECT_TIMEOUT = 5.0

try:
    READ_TIMEOUT = float(os.getenv("READ_TIMEOUT", "15"))
    assert READ_TIMEOUT > 0
except (ValueError, AssertionError):
    print("WARNING: Invalid READ_TIMEOUT, using default 15s")
    READ_TIMEOUT = 15.0


# ============================================================
#  SOURCE-IP SOCKET PATCH
# ============================================================

_local = threading.local()


def _source_bound_create_connection(address, timeout=None,
                                    source_address=None, socket_options=None):
    params = getattr(_local, "source_params", None)
    if params is None:
        return urllib3_conn._original_create_connection(
            address, timeout=timeout,
            source_address=source_address,
            socket_options=socket_options,
        )

    src_ip, src_port, use_v6 = params
    host, port = address
    af    = socket.AF_INET6 if use_v6 else socket.AF_INET
    infos = socket.getaddrinfo(host, port, af, socket.SOCK_STREAM)

    if not infos:
        raise socket.gaierror(f"getaddrinfo: no results for {host}:{port} (af={af})")

    last_err = None
    for af, socktype, proto, _, sockaddr in infos:
        sock = socket.socket(af, socktype, proto)

        if socket_options:
            for opt in socket_options:
                sock.setsockopt(*opt)

        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except (AttributeError, OSError):
            pass

        try:
            if use_v6:
                sock.bind((src_ip, src_port, 0, 0))
            else:
                sock.bind((src_ip, src_port))
            sock.settimeout(timeout)
            sock.connect(sockaddr)
            _local.last_used_port = sock.getsockname()[1]
            return sock
        except Exception as e:
            sock.close()
            last_err = e

    raise last_err


if not hasattr(urllib3_conn, "_source_patch_applied"):
    urllib3_conn._source_patch_applied       = True
    urllib3_conn._original_create_connection = urllib3_conn.create_connection
    urllib3_conn.create_connection           = _source_bound_create_connection


# ============================================================
#  HELPER FUNCTIONS
# ============================================================

def is_ipv6(ip):
    try:
        socket.inet_pton(socket.AF_INET6, ip)
        return True
    except (socket.error, OSError):
        return False


def parse_ports(port_str):
    if not port_str or not port_str.strip():
        return None
    result = []
    for part in port_str.split(","):
        part = part.strip()
        if "-" in part:
            try:
                parts = part.split("-", maxsplit=1)
                start, end = int(parts[0]), int(parts[1])
                if start > end:
                    print(f"WARNING: reversed port range '{part}', skipping")
                    continue
                result.extend(range(start, end + 1))
            except (ValueError, IndexError):
                print(f"WARNING: invalid port range '{part}', skipping")
        else:
            try:
                result.append(int(part))
            except ValueError:
                print(f"WARNING: invalid port '{part}', skipping")
    return result or None


def load_ip_pool():
    if not Path(IP_POOL_FILE).exists():
        print(f"ERROR: {IP_POOL_FILE} not found!")
        sys.exit(1)
    try:
        with open(IP_POOL_FILE) as f:
            ips = [line.strip().split("/")[0] for line in f
                if line.strip() and not line.startswith("#")]
        if not ips:
            print(f"ERROR: {IP_POOL_FILE} is empty!")
            sys.exit(1)
        v6_count = sum(1 for ip in ips if is_ipv6(ip))
        v4_count = len(ips) - v6_count
        print(f"Loaded {len(ips)} IP addresses from {IP_POOL_FILE} "
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
            print(f"Loaded {len(ports)} ports from {PORT_POOL_FILE}")
        return ports
    except Exception as e:
        print(f"WARNING: Failed to load port pool: {e}")
        return None


# ============================================================
#  TEST METADATA & EVENTS
# ============================================================

TEST_TYPE   = os.getenv("TEST_TYPE", "Locust Load Test")
start_time  = None
target_host = None
target_ip   = None

_worker_stages     = None
_worker_test_start = None


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    global start_time, target_host, target_ip
    global _worker_stages, _worker_test_start

    _worker_test_start = _time.time()
    try:
        stages_path = os.path.join(BASE_DIR, "stages.json")
        with open(stages_path) as f:
            _worker_stages = json.load(f)
        print(f"Loaded {len(_worker_stages)} stages from stages.json")
    except Exception as e:
        print(f"[WARN] Could not load stages.json for wait_time: {e}")

    if isinstance(environment.runner, WorkerRunner):
        return

    start_time  = datetime.now()
    target_host = environment.host or "Unknown"

    target_ip = None
    try:
        with open(os.path.join(BASE_DIR, "test_config.csv"), newline="") as f:
            cfg = next(csv.DictReader(f))
            target_ip = str(cfg.get("target_ip", "")).strip()
        if target_ip:
            print(f"Target is {'IPv6' if is_ipv6(target_ip) else 'IPv4'} address: {target_ip}")
    except Exception:
        pass

    if not target_ip:
        try:
            clean_host = (
                target_host
                .replace("https://", "")
                .replace("http://",  "")
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
                    ip_version = os.getenv("IP_VERSION", "ipv4").lower()
                    af = socket.AF_INET6 if ip_version == "ipv6" else socket.AF_INET
                    try:
                        infos = socket.getaddrinfo(clean_host, None, af)
                        target_ip = infos[0][4][0]
                        label = "IPv6" if af == socket.AF_INET6 else "IPv4"
                        print(f"Resolved {clean_host} → {target_ip} ({label})")
                    except Exception:
                        target_ip = socket.gethostbyname(clean_host)
                        print(f"Resolved {clean_host} → {target_ip} (IPv4 fallback)")
        except Exception as e:
            print(f"Warning: Could not resolve hostname: {e}")
            target_ip = "Unknown"

    print(f"\n{'='*50}")
    print(f"Test started at: {start_time}")
    print(f"Target: {target_host} ({target_ip})")
    print(f"{'='*50}\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    global start_time, target_host, target_ip

    if isinstance(environment.runner, WorkerRunner):
        return

    end_time = datetime.now()
    duration = end_time - start_time if start_time else "Unknown"

    print(f"\n{'='*50}")
    print(f"Test ended at: {end_time}")
    print(f"Duration: {duration}")
    print(f"{'='*50}\n")

    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(METADATA_FILE, "w", newline="") as csvfile:
            writer     = csv.writer(csvfile)
            ip_version = os.getenv("IP_VERSION", "ipv4").lower()

            if ip_version == "ipv6":
                if os.getenv("IPV6_MODE", "range").lower() == "prefix":
                    used_ips_val = os.getenv("IP6_PREFIX", "Unknown")
                else:
                    used_ips_val = (os.getenv("IP6_START", "")
                                    + " - " + os.getenv("IP6_END", ""))
            else:
                used_ips_val = (os.getenv("IP_START", "")
                                + " - " + os.getenv("IP_END", ""))

            writer.writerow(["start_time", "end_time", "duration", "test_type",
                             "target_host", "target_ip", "used_ips"])
            writer.writerow([start_time, end_time, str(duration), TEST_TYPE,
                             environment.host, target_ip, used_ips_val])
        print(f"Metadata saved to {METADATA_FILE}")
    except Exception as e:
        print(f"Failed to save metadata: {e}")


# ============================================================
#  SOURCE IP ADAPTER
# ============================================================

class SourceIPAdapter(HTTPAdapter):
    def __init__(self, source_ip, source_port=0, **kwargs):
        self.source_ip   = source_ip
        self.source_port = source_port
        self._use_v6     = is_ipv6(source_ip)
        super().__init__(
            pool_connections=1,
            pool_maxsize=1,
            max_retries=0,
            **kwargs
        )

    def send(self, request, **kwargs):
        _local.source_params = (self.source_ip, self.source_port, self._use_v6)
        try:
            response = super().send(request, **kwargs)
            actual = getattr(_local, "last_used_port", None)
            if actual and actual != self.source_port:
                self.source_port = actual
            return response
        finally:
            try:
                del _local.source_params
            except AttributeError:
                pass


# ============================================================
#  DYNAMIC SHAPE  (beží len na master procese)
# ============================================================

class DynamicShape(LoadTestShape):
    _stages = None

    def _load(self):
        path = os.path.join(BASE_DIR, "stages.json")
        with open(path) as f:
            self._stages = json.load(f)

    def tick(self):
        if self._stages is None:
            try:
                self._load()
            except Exception as e:
                print(f"[ERROR] DynamicShape: could not load stages.json: {e}")
                return None

        t = self.get_run_time()
        for stage in self._stages:
            if t < stage["duration"]:
                return stage["users"], stage["spawn_rate"]
        return None


# ============================================================
#  USER CLASS
# ============================================================

class MyUser(HttpUser):
    _ip_pool   = None
    _port_pool = None
    _pool_lock = threading.Lock()

    def wait_time(self):
        if _worker_stages and _worker_test_start is not None:
            elapsed = _time.time() - _worker_test_start
            for stage in _worker_stages:
                if elapsed < stage["duration"]:
                    mode = stage.get("wait_mode", "between")
                    wmin = float(stage.get("wait_min", 1.0))
                    wmax = float(stage.get("wait_max", 3.0))
                    if mode == "constant":
                        return wmin
                    elif mode == "constant_throughput":
                        return (1.0 / wmin) if wmin > 0 else 1.0
                    else:
                        return random.uniform(wmin, wmax)
        return random.uniform(1.0, 3.0)

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
        self._logged_port = False

        self.adapter = SourceIPAdapter(self.source_ip, self.source_port)
        self.client.mount("http://",  self.adapter)
        self.client.mount("https://", self.adapter)

        self.client.verify  = os.getenv("SSL_VERIFY", "true").lower() != "false"
        self.client.timeout = (CONNECT_TIMEOUT, READ_TIMEOUT)

    def on_stop(self):
        try:
            self.client.close()
        except Exception:
            pass

    @task
    def index(self):
        with self.client.get("/", catch_response=True) as resp:
            if not self._logged_port:
                actual_port = self.adapter.source_port or "OS ephemeral"
                print(
                    f"User started → IP: {self.source_ip} "
                    f"({'IPv6' if is_ipv6(self.source_ip) else 'IPv4'})  "
                    f"Port: {actual_port}"
                )
                self._logged_port = True

            code = resp.status_code
            if code in (200, 201, 301, 302, 303, 307, 308):
                resp.success()
            elif code == 429:
                resp.failure(f"Rate limited (IP: {self.source_ip})")
            elif code == 403:
                resp.failure(f"IP blocked: {self.source_ip}")
            elif code == 401:
                resp.failure("Unauthorized")
            elif code in (500, 503):
                resp.failure(f"Server error {code}")
            elif code == 0:
                error_cls = type(resp.error).__name__ if resp.error else "Unknown"
                cause     = str(getattr(resp.error, "args", ["?"])[0])[:120]
                resp.failure(f"[{error_cls}] IP:{self.source_ip} → {cause}")

