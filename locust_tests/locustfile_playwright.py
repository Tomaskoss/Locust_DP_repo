"""
locustfile_http_playwright.py
─────────────────────────────
Replays a browser session recorded by playwright_recorder.py.

Workflow:
  1. Run playwright_recorder.py → session.json
  2. Start the Locust GUI, pick this file as the Locustfile
  3. Every virtual user replays the full recorded journey (or a random
     subset – see TASK_MODE below) using a dedicated source IP from the pool.

Configuration via config.env (same keys as Locustfile_http.py):
  SESSION_FILE   – path to the JSON file produced by the recorder
                   (default: <project_root>/session.json)
  REPLAY_TYPES   – comma-separated resource types to replay
                   (default: document,xhr,fetch,websocket)
                   Set to "all" to replay every recorded request.
  TASK_MODE      – "sequential"  → replay all requests in recorded order (default)
                   "random"      → pick one random request per task tick
  THINK_TIME_MS  – extra per-request think-time in milliseconds (default 0)
"""

# ============================================================
#  IMPORTS
# ============================================================

from locust import events, HttpUser, task, LoadTestShape
from locust.runners import WorkerRunner
from datetime import datetime
from dotenv import load_dotenv
import os, sys, csv, json, time as _time, socket, random, threading
from pathlib import Path
from requests.adapters import HTTPAdapter
from urllib.parse import urlparse
import urllib3
import urllib3.util.connection as urllib3_conn

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
#  PLAYWRIGHT SESSION CONFIG
# ============================================================

SESSION_FILE  = os.getenv("SESSION_FILE",  os.path.join(BASE_DIR, "session.json"))
REPLAY_TYPES  = os.getenv("REPLAY_TYPES", "document,stylesheet,script,image,font,other")
TASK_MODE     = os.getenv("TASK_MODE",    "sequential")   # "sequential" | "random"
THINK_TIME_MS = float(os.getenv("THINK_TIME_MS", "0"))    # extra delay between requests


def _load_session(path: str) -> list[dict]:
    """
    Loads session.json and filters by REPLAY_TYPES.
    Returns a list of request dicts: {method, url, path, resource}
    """
    if not Path(path).exists():
        print(f"[ERROR] Session file not found: {path}")
        print("        Run playwright_recorder.py first to generate a session.")
        sys.exit(1)

    with open(path, encoding="utf-8") as f:
        raw: list[dict] = json.load(f)

    if not raw:
        print(f"[ERROR] Session file is empty: {path}")
        sys.exit(1)

    if REPLAY_TYPES.strip().lower() == "all":
        filtered = raw
    else:
        allowed  = {t.strip().lower() for t in REPLAY_TYPES.split(",")}
        filtered = [r for r in raw if r.get("resource", "").lower() in allowed]

    if not filtered:
        print(
            f"[ERROR] No requests matched REPLAY_TYPES='{REPLAY_TYPES}'.\n"
            f"        Available types in session: "
            f"{sorted({r.get('resource') for r in raw})}"
        )
        sys.exit(1)

    # Deduplicate by method+url (preserve order)
    seen, deduped = set(), []
    for req in filtered:
        key = f"{req['method']}:{req['url']}"
        if key not in seen:
            seen.add(key)
            deduped.append(req)

    print(
        f"[Session] Loaded {len(deduped)} unique requests from {Path(path).name} "
        f"(filtered from {len(raw)} total, types={REPLAY_TYPES})"
    )
    for rtype in sorted({r.get("resource", "?") for r in deduped}):
        count = sum(1 for r in deduped if r.get("resource") == rtype)
        print(f"  {rtype:<25} {count}x")

    return deduped


# Load once at module level so all workers share the same list
SESSION_REQUESTS: list[dict] = _load_session(SESSION_FILE)

# ============================================================
#  SSL WARNINGS
# ============================================================

if os.getenv("SSL_VERIFY", "true").lower() == "false":
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ============================================================
#  TIMEOUT CONFIG
# ============================================================

CONNECT_TIMEOUT = float(os.getenv("CONNECT_TIMEOUT", "5"))
READ_TIMEOUT    = float(os.getenv("READ_TIMEOUT",    "15"))

# ============================================================
#  SOURCE-IP SOCKET PATCH  (identical to Locustfile_http.py)
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

def is_ipv6(ip: str) -> bool:
    try:
        socket.inet_pton(socket.AF_INET6, ip)
        return True
    except (socket.error, OSError):
        return False


def parse_ports(port_str: str) -> list[int] | None:
    if not port_str or not port_str.strip():
        return None
    result = []
    for part in port_str.split(","):
        part = part.strip()
        if "-" in part:
            try:
                lo, hi = part.split("-", maxsplit=1)
                result.extend(range(int(lo), int(hi) + 1))
            except (ValueError, IndexError):
                print(f"[WARN] Invalid port range '{part}', skipping")
        else:
            try:
                result.append(int(part))
            except ValueError:
                print(f"[WARN] Invalid port '{part}', skipping")
    return result or None


def load_ip_pool() -> list[str]:
    if not Path(IP_POOL_FILE).exists():
        print(f"[ERROR] {IP_POOL_FILE} not found!")
        sys.exit(1)
    with open(IP_POOL_FILE) as f:
        ips = [
            line.strip().split("/")[0]
            for line in f
            if line.strip() and not line.startswith("#")
        ]
    if not ips:
        print(f"[ERROR] {IP_POOL_FILE} is empty!")
        sys.exit(1)
    v6 = sum(1 for ip in ips if is_ipv6(ip))
    print(f"[Pool] Loaded {len(ips)} IPs (IPv4: {len(ips)-v6}, IPv6: {v6})")
    return ips


def load_port_pool() -> list[int] | None:
    if not Path(PORT_POOL_FILE).exists():
        return None
    try:
        with open(PORT_POOL_FILE) as f:
            content = f.read().strip()
        ports = parse_ports(content)
        if ports:
            print(f"[Pool] Loaded {len(ports)} source ports")
        return ports
    except Exception as e:
        print(f"[WARN] Failed to load port pool: {e}")
        return None

# ============================================================
#  TEST METADATA & EVENTS  (identical pattern to Locustfile_http.py)
# ============================================================

TEST_TYPE  = os.getenv("TEST_TYPE", "Playwright Replay")
start_time = None
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
        with open(os.path.join(BASE_DIR, "stages.json")) as f:
            _worker_stages = json.load(f)
        print(f"[Stages] Loaded {len(_worker_stages)} stages")
    except Exception as e:
        print(f"[WARN] Could not load stages.json: {e}")

    if isinstance(environment.runner, WorkerRunner):
        return

    start_time  = datetime.now()
    target_host = environment.host or "Unknown"
    target_ip   = None

    try:
        with open(os.path.join(BASE_DIR, "test_config.csv"), newline="") as f:
            cfg = next(csv.DictReader(f))
            target_ip = str(cfg.get("target_ip", "")).strip()
    except Exception:
        pass

    if not target_ip:
        try:
            clean = (
                target_host
                .replace("https://", "").replace("http://", "")
                .split("/")[0].split(":")[0].lstrip("[").split("]")[0]
            )
            af = (socket.AF_INET6
                  if os.getenv("IP_VERSION", "ipv4").lower() == "ipv6"
                  else socket.AF_INET)
            try:
                infos = socket.getaddrinfo(clean, None, af)
                target_ip = infos[0][4][0]
            except Exception:
                target_ip = socket.gethostbyname(clean)
        except Exception as e:
            print(f"[WARN] Could not resolve hostname: {e}")
            target_ip = "Unknown"

    print(f"\n{'='*55}")
    print(f"  Playwright Replay — Test started at: {start_time}")
    print(f"  Target : {target_host} ({target_ip})")
    print(f"  Session: {Path(SESSION_FILE).name}  ({len(SESSION_REQUESTS)} requests)")
    print(f"  Mode   : {TASK_MODE}")
    print(f"{'='*55}\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    if isinstance(environment.runner, WorkerRunner):
        return

    end_time = datetime.now()
    duration = end_time - start_time if start_time else "Unknown"
    print(f"\n{'='*55}")
    print(f"  Test ended: {end_time}  |  Duration: {duration}")
    print(f"{'='*55}\n")

    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        ip_ver = os.getenv("IP_VERSION", "ipv4").lower()
        if ip_ver == "ipv6":
            used_ips_val = (
                os.getenv("IP6_PREFIX", "")
                if os.getenv("IPV6_MODE", "range").lower() == "prefix"
                else os.getenv("IP6_START", "") + " - " + os.getenv("IP6_END", "")
            )
        else:
            used_ips_val = os.getenv("IP_START", "") + " - " + os.getenv("IP_END", "")

        with open(METADATA_FILE, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["start_time", "end_time", "duration", "test_type",
                        "target_host", "target_ip", "used_ips"])
            w.writerow([start_time, end_time, str(duration), TEST_TYPE,
                        environment.host, target_ip, used_ips_val])
        print(f"[Meta] Saved → {METADATA_FILE}")
    except Exception as e:
        print(f"[WARN] Failed to save metadata: {e}")


# ============================================================
#  SOURCE IP ADAPTER
# ============================================================

class SourceIPAdapter(HTTPAdapter):
    def __init__(self, source_ip: str, source_port: int = 0, **kwargs):
        self.source_ip   = source_ip
        self.source_port = source_port
        self._use_v6     = is_ipv6(source_ip)
        super().__init__(pool_connections=1, pool_maxsize=1, max_retries=0, **kwargs)

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
#  DYNAMIC LOAD SHAPE  (identical to Locustfile_http.py)
# ============================================================

class DynamicShape(LoadTestShape):
    _stages = None

    def _load(self):
        with open(os.path.join(BASE_DIR, "stages.json")) as f:
            self._stages = json.load(f)

    def tick(self):
        if self._stages is None:
            try:
                self._load()
            except Exception:
                return None
        t = self.get_run_time()
        for stage in self._stages:
            if t < stage["duration"]:
                return stage["users"], stage["spawn_rate"]
        return None


# ============================================================
#  USER CLASS
# ============================================================

class PlaywrightReplayUser(HttpUser):
    """
    Replays the HTTP requests recorded by playwright_recorder.py.

    Sequential mode  → each task tick sends ALL recorded requests in order,
                       simulating a complete user journey through the site.
    Random mode      → each task tick sends one randomly chosen request,
                       useful for high-concurrency throughput tests.
    """

    _ip_pool   = None
    _port_pool = None
    _pool_lock = threading.Lock()

    # ── Wait time (stage-aware, mirrors Locustfile_http.py) ──────────

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

    # ── Pool loaders ─────────────────────────────────────────────────

    @classmethod
    def get_ip_pool(cls) -> list[str]:
        if cls._ip_pool is None:
            with cls._pool_lock:
                if cls._ip_pool is None:
                    cls._ip_pool = load_ip_pool()
        return cls._ip_pool

    @classmethod
    def get_port_pool(cls) -> list[int]:
        if cls._port_pool is None:
            with cls._pool_lock:
                if cls._port_pool is None:
                    cls._port_pool = load_port_pool() or []
        return cls._port_pool

    # ── Lifecycle ────────────────────────────────────────────────────

    def on_start(self):
        pool             = self.get_ip_pool()
        self.source_ip   = random.choice(pool)
        ports            = self.get_port_pool()
        self.source_port = random.choice(ports) if ports else 0
        self._logged     = False

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

    # ── Response handler ─────────────────────────────────────────────

    def _handle_response(self, resp, path: str):
        if not self._logged:
            actual_port = self.adapter.source_port or "OS ephemeral"
            print(
                f"User started → IP: {self.source_ip} "
                f"({'IPv6' if is_ipv6(self.source_ip) else 'IPv4'})  "
                f"Port: {actual_port}"
            )
            self._logged = True

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
        else:
            resp.success()   # treat 2xx variants, 304 etc. as success

    # ── Tasks ────────────────────────────────────────────────────────

    @task
    def replay(self):
        """
        Sequential mode  – sends every request in recorded order.
        Random mode      – sends one random request per tick.
        """
        if TASK_MODE == "random":
            req = random.choice(SESSION_REQUESTS)
            self._send(req)
        else:
            # Sequential: walk through full recorded journey
            for req in SESSION_REQUESTS:
                self._send(req)
                if THINK_TIME_MS > 0:
                    _time.sleep(THINK_TIME_MS / 1000.0)

    # ── Internal sender ──────────────────────────────────────────────

    def _send(self, req: dict):
        method  = req.get("method", "GET").upper()
        path    = req.get("path") or urlparse(req["url"]).path or "/"
        rtype   = req.get("resource", "?")
        # Use 'name' so Locust groups requests by path, not full URL
        kwargs  = {
            "catch_response": True,
            "name": f"[{rtype}] {path}",
        }

        try:
            if method == "GET":
                with self.client.get(path, **kwargs) as resp:
                    self._handle_response(resp, path)
            elif method == "POST":
                with self.client.post(path, **kwargs) as resp:
                    self._handle_response(resp, path)
            elif method == "PUT":
                with self.client.put(path, **kwargs) as resp:
                    self._handle_response(resp, path)
            elif method == "PATCH":
                with self.client.patch(path, **kwargs) as resp:
                    self._handle_response(resp, path)
            elif method == "DELETE":
                with self.client.delete(path, **kwargs) as resp:
                    self._handle_response(resp, path)
            elif method == "HEAD":
                with self.client.head(path, **kwargs) as resp:
                    self._handle_response(resp, path)
            else:
                # Fallback to GET for unsupported methods
                with self.client.get(path, **kwargs) as resp:
                    self._handle_response(resp, path)
        except Exception as e:
            # Network-level errors not caught by catch_response
            print(f"[ERR] {method} {path} — {type(e).__name__}: {e}")
