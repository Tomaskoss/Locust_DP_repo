import customtkinter as ctk
import subprocess
import threading
import sys
import os
import time
import csv
import queue
import socket
import random
import requests
import pandas as pd
from requests.adapters import HTTPAdapter
import urllib3.util.connection as urllib3_conn

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, os.path.join(BASE_DIR, "network"))
sys.path.insert(0, os.path.join(BASE_DIR, "report"))

from Create_topology        import create_topology_diagram
from Locust_report_v2       import create_pdf_report
from Create_IP_Pool_skript  import main as create_pool
from Remove_IP_Pool_skript  import main as remove_pool

DATA_DIR   = os.path.join(BASE_DIR, "data")
REPORT_DIR = os.path.join(BASE_DIR, "report")


# ============================================================
#  HELPER
# ============================================================

def parse_ports(port_str):
    """
    "1024-65535"     → list(range(1024, 65536))
    "1025,1620,3550" → [1025, 1620, 3550]
    ""  or  None     → None
    """
    if not port_str or not port_str.strip():
        return None
    port_str = port_str.strip()
    if "-" in port_str and "," not in port_str:
        parts = port_str.split("-")
        return list(range(int(parts[0]), int(parts[1]) + 1))
    else:
        return [int(p.strip()) for p in port_str.split(",")]


class LocustGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Locust Test GUI")
        self.geometry("900x800")
        self.minsize(800, 600)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.locust_process = None
        self.log_queue      = queue.Queue()

        self.scroll = ctk.CTkScrollableFrame(self, corner_radius=0)
        self.scroll.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.scroll.grid_columnconfigure(0, weight=1)

        self._build_header()
        self._build_config()
        self._build_buttons()
        self._build_comment()
        self._build_log()
        self._build_statusbar()

        self._poll_log_queue()

    # ================================================================
    # BUILD UI
    # ================================================================

    def _build_header(self):
        header = ctk.CTkFrame(self.scroll, corner_radius=12, fg_color="#1a1a2e")
        header.grid(row=0, column=0, padx=15, pady=(15, 5), sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text="🦗  Locust Test GUI",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color="#4A90D9"
        ).grid(row=0, column=0, padx=20, pady=(14, 2), sticky="w")

        ctk.CTkLabel(
            header,
            text="Load testing & PDF report generator",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        ).grid(row=1, column=0, padx=20, pady=(0, 12), sticky="w")

    def _build_config(self):
        frame = ctk.CTkFrame(self.scroll, corner_radius=12)
        frame.grid(row=1, column=0, padx=15, pady=5, sticky="ew")
        frame.grid_columnconfigure(1, weight=1)
        frame.grid_columnconfigure(3, weight=1)

        ctk.CTkLabel(
            frame, text="⚙  Test Configuration",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, columnspan=4, padx=15, pady=(12, 8), sticky="w")

        fields_left = [
            ("🌐  Target host",  "target",     "https://google.sk"),
            ("📡  Interface",    "interface",  "ens33"),
            ("👥  Users",        "users",      "1"),
            ("⚡  Spawn rate",   "spawn_rate", "1"),
            ("🏷  Test type",    "test_type",  "Load Test"),
        ]
        fields_right = [
            ("🔢  IP range start", "ip_start",  "192.168.10.10"),
            ("🔢  IP range end",   "ip_end",    "192.168.10.40"),
            ("🔌  Source ports",   "src_ports", ""),
            ("⏱  Run time (s)",   "run_time",  "20"),
            ("🔄  Processes",      "processes", "-1"),
        ]

        self.entries = {}

        for i, (label, key, default) in enumerate(fields_left):
            ctk.CTkLabel(frame, text=label, font=ctk.CTkFont(size=12),
                         anchor="w").grid(row=i+1, column=0, padx=(15, 5), pady=4, sticky="w")
            e = ctk.CTkEntry(frame, width=200, placeholder_text=default)
            e.insert(0, default)
            e.grid(row=i+1, column=1, padx=(0, 20), pady=4, sticky="ew")
            self.entries[key] = e

        for i, (label, key, default) in enumerate(fields_right):
            ctk.CTkLabel(frame, text=label, font=ctk.CTkFont(size=12),
                         anchor="w").grid(row=i+1, column=2, padx=(10, 5), pady=4, sticky="w")
            if key == "src_ports":
                ph = "e.g. 1024-65535 or 1025,1620,3550"
            else:
                ph = default
            e = ctk.CTkEntry(frame, width=200, placeholder_text=ph)
            if default:
                e.insert(0, default)
            e.grid(row=i+1, column=3, padx=(0, 15), pady=4, sticky="ew")
            self.entries[key] = e

        # ── REACHABILITY SEPARATOR ────────────────────────────────
        ctk.CTkLabel(
            frame,
            text="── Reachability ─────────────────────────────────",
            font=ctk.CTkFont(size=11),
            text_color="gray",
            anchor="w"
        ).grid(row=7, column=0, columnspan=4, padx=15, pady=(10, 2), sticky="w")

        reach_fields_left = [
            ("🔁  Interval (s)",        "reach_interval",  "5"),
            ("⏳  Timeout (s)",         "reach_timeout",   "5"),
        ]
        reach_fields_right = [
            ("🖧  Source IP",            "reach_src_ip",    ""),
            ("🔌  Interface",            "reach_interface", ""),
            ("📉  Failure threshold (%)", "reach_threshold", "50"),
        ]

        for i, (label, key, default) in enumerate(reach_fields_left):
            ctk.CTkLabel(frame, text=label, font=ctk.CTkFont(size=12),
                         anchor="w").grid(row=i+8, column=0, padx=(15, 5), pady=4, sticky="w")
            e = ctk.CTkEntry(frame, width=200, placeholder_text=default)
            e.insert(0, default)
            e.grid(row=i+8, column=1, padx=(0, 20), pady=4, sticky="ew")
            self.entries[key] = e

        for i, (label, key, default) in enumerate(reach_fields_right):
            ctk.CTkLabel(frame, text=label, font=ctk.CTkFont(size=12),
                         anchor="w").grid(row=i+8, column=2, padx=(10, 5), pady=4, sticky="w")
            if key == "reach_src_ip":
                ph = "= IP range start"
            elif key == "reach_interface":
                ph = "= main interface"
            else:
                ph = default
            e = ctk.CTkEntry(frame, width=200, placeholder_text=ph)
            if default:
                e.insert(0, default)
            e.grid(row=i+8, column=3, padx=(0, 15), pady=4, sticky="ew")
            self.entries[key] = e

        ctk.CTkLabel(frame, text="").grid(row=11, column=0, pady=(0, 4))

    def _build_buttons(self):
        frame = ctk.CTkFrame(self.scroll, corner_radius=12)
        frame.grid(row=2, column=0, padx=15, pady=5, sticky="ew")
        frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        ctk.CTkLabel(
            frame, text="🚀  Steps",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, columnspan=4, padx=15, pady=(12, 8), sticky="w")

        btn_cfg = [
            ("1.  Setup\nIP Pool + Topology",      self.setup_env,       "#2471A3", "white"),
            ("2.  Start\nLocust + Reachability",   self.run_test,        "#1E8449", "white"),
            ("3.  Generate\nPDF Report",            self.generate_report, "#7D3C98", "white"),
            ("4.  Cleanup\nRemove IP Pool",         self.cleanup,         "#922B21", "white"),
        ]

        self.btn_refs = {}
        for i, (text, cmd, color, fg) in enumerate(btn_cfg):
            btn = ctk.CTkButton(
                frame, text=text, command=cmd,
                fg_color=color, hover_color=self._darken(color),
                font=ctk.CTkFont(size=12, weight="bold"),
                corner_radius=10, height=55
            )
            btn.grid(row=1, column=i, padx=8, pady=(0, 14), sticky="ew")
            self.btn_refs[i] = btn

        self.stop_btn = ctk.CTkButton(
            frame, text="⛔  Stop Locust",
            command=self.stop_locust,
            fg_color="#641E16", hover_color="#922B21",
            font=ctk.CTkFont(size=11),
            corner_radius=8, height=30,
            state="disabled"
        )
        self.stop_btn.grid(row=2, column=0, columnspan=4,
                           padx=8, pady=(0, 10), sticky="e")

    def _build_comment(self):
        frame = ctk.CTkFrame(self.scroll, corner_radius=12)
        frame.grid(row=3, column=0, padx=15, pady=5, sticky="ew")
        frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            frame, text="📝  Report Comment",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, padx=15, pady=(12, 4), sticky="w")

        self.comment_text = ctk.CTkTextbox(
            frame, height=80, corner_radius=8,
            font=ctk.CTkFont(size=12, family="Courier New")
        )
        self.comment_text.grid(row=1, column=0, padx=15, pady=(0, 12), sticky="ew")
        self.comment_text.insert("0.0", "Write a comment for the report...")

    def _build_log(self):
        frame = ctk.CTkFrame(self.scroll, corner_radius=12)
        frame.grid(row=4, column=0, padx=15, pady=5, sticky="ew")
        frame.grid_columnconfigure(0, weight=1)

        header_row = ctk.CTkFrame(frame, fg_color="transparent")
        header_row.grid(row=0, column=0, padx=15, pady=(12, 4), sticky="ew")
        header_row.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header_row, text="📋  Output / Log",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            header_row, text="🗑  Clear",
            command=self.clear_log,
            fg_color="#4A4A4A", hover_color="#666666",
            font=ctk.CTkFont(size=11),
            corner_radius=6, height=28, width=100
        ).grid(row=0, column=1, sticky="e")

        self.log = ctk.CTkTextbox(
            frame, corner_radius=8,
            height=300,
            font=ctk.CTkFont(size=11, family="Courier New"),
            fg_color="#0d1117", text_color="#c9d1d9",
            state="disabled"
        )
        self.log.grid(row=1, column=0, padx=15, pady=(0, 12), sticky="ew")

    def _build_statusbar(self):
        self.status_bar = ctk.CTkLabel(
            self.scroll, text="● Ready",
            font=ctk.CTkFont(size=11),
            text_color="gray",
            anchor="w",
            fg_color="#1a1a2e",
            corner_radius=0,
            height=28
        )
        self.status_bar.grid(row=5, column=0, padx=0, pady=(0, 5), sticky="ew")

    # ================================================================
    # HELPERS
    # ================================================================

    def _darken(self, hex_color):
        hex_color = hex_color.lstrip("#")
        r, g, b   = tuple(max(0, int(hex_color[i:i+2], 16) - 40) for i in (0, 2, 4))
        return f"#{r:02x}{g:02x}{b:02x}"

    def write_log(self, msg):
        self.log_queue.put(msg)

    def _poll_log_queue(self):
        try:
            while True:
                msg = self.log_queue.get_nowait()
                self.log.configure(state="normal")
                self.log.insert("end", msg + "\n")
                self.log.see("end")
                self.log.configure(state="disabled")
                self.status_bar.configure(text=f"● {msg[:90]}")
        except queue.Empty:
            pass
        finally:
            self.after(100, self._poll_log_queue)

    def clear_log(self):
        self.log.configure(state="normal")
        self.log.delete("0.0", "end")
        self.log.configure(state="disabled")
        self.status_bar.configure(text="● Log cleared")

    def get(self, key):
        return self.entries[key].get().strip()

    def get_comment(self):
        text = self.comment_text.get("0.0", "end").strip()
        if text == "Write a comment for the report...":
            return ""
        return text

    def _get_target_clean(self):
        return (
            self.get("target")
            .replace("https://", "")
            .replace("http://", "")
            .split("/")[0]
        )

    def _get_source_range(self):
        return f"{self.get('ip_start')}-{self.get('ip_end').split('.')[-1]}"

    def _save_port_pool(self):
        port_str  = self.get("src_ports")
        port_file = os.path.join(BASE_DIR, "port_pool.txt")
        if port_str:
            ports = parse_ports(port_str)
            if ports:
                with open(port_file, "w") as f:
                    f.write(port_str)
                self.write_log(f"✓ Port pool saved ({len(ports)} ports) → port_pool.txt")
            else:
                self.write_log("⚠ Invalid port format — port_pool.txt not created")
        else:
            if os.path.exists(port_file):
                os.remove(port_file)
            self.write_log("ℹ Source ports: OS will assign port automatically")

    def _save_test_config(self, script_dir):
        config_file  = os.path.join(script_dir, "test_config.csv")
        target_clean = self._get_target_clean()
        try:
            resolved_ip = socket.gethostbyname(target_clean)
        except Exception:
            resolved_ip = target_clean

        src_ip      = self.get("reach_src_ip")    or self.get("ip_start")
        reach_iface = self.get("reach_interface") or self.get("interface")

        with open(config_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "target", "target_clean", "target_ip",
                "ip_start", "ip_end", "source_range",
                "src_ports",
                "interface", "users", "run_time",
                "reach_timeout", "reach_src_ip",
                "reach_interface", "reach_threshold",
                "test_type",
            ])
            writer.writeheader()
            writer.writerow({
                "target":          self.get("target"),
                "target_clean":    target_clean,
                "target_ip":       resolved_ip,
                "ip_start":        self.get("ip_start"),
                "ip_end":          self.get("ip_end"),
                "source_range":    self._get_source_range(),
                "src_ports":       self.get("src_ports"),
                "interface":       self.get("interface"),
                "users":           self.get("users"),
                "run_time":        self.get("run_time"),
                "reach_timeout":   self.get("reach_timeout")   or "5",
                "reach_src_ip":    src_ip,
                "reach_interface": reach_iface,
                "reach_threshold": self.get("reach_threshold") or "50",
                "test_type":       self.get("test_type"),
                
            })
        self.write_log(f"✓ Test config saved → {target_clean} ({resolved_ip})")

    def _load_test_config(self, script_dir):
        config_file = os.path.join(script_dir, "test_config.csv")
        if os.path.exists(config_file):
            try:
                cfg             = pd.read_csv(config_file).iloc[0]
                target_clean    = str(cfg.get("target_clean",    self._get_target_clean()))
                target_ip       = str(cfg.get("target_ip",       target_clean))
                source_range    = str(cfg.get("source_range",    self._get_source_range()))
                interface       = str(cfg.get("interface",       self.get("interface")))
                reach_threshold = float(cfg.get("reach_threshold", 50))
                test_type_cfg   = str(cfg.get("test_type",       self.get("test_type")))
                self.write_log(
                    f"✓ Test parameters: {target_clean} ({target_ip}) | "
                    f"{source_range} | {interface} | threshold={reach_threshold}%"
                )
                return target_clean, target_ip, source_range, interface, reach_threshold, test_type_cfg
            except Exception as e:
                self.write_log(f"⚠ Error reading test_config.csv: {e}")
        else:
            self.write_log("⚠ test_config.csv not found – using current GUI values")

        return (
            self._get_target_clean(),
            self._get_target_clean(),
            self._get_source_range(),
            self.get("interface"),
            float(self.get("reach_threshold") or 50),
            self.get("test_type"),
        )

    # ================================================================
    # STEP 1 – SETUP
    # ================================================================

    def setup_env(self):
        threading.Thread(target=self._setup_thread, daemon=True).start()

    def _setup_thread(self):
        try:
            self.write_log("=" * 60)
            self.write_log("▶ SETUP – Adding IP addresses to interface...")
            create_pool(
                ip_start    = self.get("ip_start"),
                ip_end      = self.get("ip_end"),
                interface   = self.get("interface"),
                output_file = os.path.join(BASE_DIR, "ip_pool.txt")
            )
            self.write_log("✓ IP pool created")

            self.write_log("▶ Generating topology diagram...")
            create_topology_diagram(
                target_ip   = self._get_target_clean(),
                source_ip   = self._get_source_range(),
                interface   = self.get("interface"),
                output_file = os.path.join(REPORT_DIR, "topology_diagram.png")
            )
            self.write_log("✓ Topology diagram generated")
            self.write_log("✓ SETUP COMPLETE")
            self.write_log("=" * 60)

        except Exception as e:
            self.write_log(f"✗ Setup error: {e}")

    # ================================================================
    # STEP 2 – TEST
    # ================================================================

    def run_test(self):
        self.btn_refs[1].configure(state="disabled")
        self.stop_btn.configure(state="normal")
        threading.Thread(target=self._run_test_thread, daemon=True).start()

    def _run_test_thread(self):
        try:
            run_time = int(self.get("run_time"))
            interval = int(self.get("reach_interval") or 5)

            self._save_port_pool()
            self._save_test_config(BASE_DIR)

            self.write_log("=" * 60)
            self.write_log("▶ Starting Reachability monitoring (parallel)...")
            reach_thread = threading.Thread(
                target=self._run_reachability,
                args=(run_time, interval),
                daemon=True
            )
            reach_thread.start()

            self.write_log("▶ Starting Locust test...")
            self.write_log("-" * 60)

            locust_file = os.path.join(BASE_DIR, "locust_tests", "Locustfile_test.py")
            csv_prefix  = os.path.join(DATA_DIR, "report")

            cmd = [
                "locust",
                "-f", locust_file,
                "--headless",
                "-u", self.get("users"),
                "-r", self.get("spawn_rate"),
                "--run-time", f"{run_time}s",
                "-H", self.get("target"),
                "--processes", self.get("processes"),
                "--csv", csv_prefix,
            ]
            self.write_log(f"CMD: {' '.join(cmd)}")
            self.write_log("-" * 60)

            self.locust_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True, bufsize=1,
                cwd=BASE_DIR
            )
            for line in self.locust_process.stdout:
                line = line.rstrip()
                if line:
                    self.write_log(line)

            self.locust_process.wait()
            reach_thread.join(timeout=5)

            self.write_log("-" * 60)
            if self.locust_process.returncode == 0:
                self.write_log("✓ Locust test completed successfully")
            else:
                self.write_log(
                    f"✗ Locust finished with error (code {self.locust_process.returncode})"
                )
            self.write_log("=" * 60)

        except Exception as e:
            self.write_log(f"✗ Test error: {e}")
        finally:
            self.btn_refs[1].configure(state="normal")
            self.stop_btn.configure(state="disabled")

    def stop_locust(self):
        if self.locust_process and self.locust_process.poll() is None:
            self.locust_process.terminate()
            self.write_log("⛔ Locust test stopped by user")
        self.btn_refs[1].configure(state="normal")
        self.stop_btn.configure(state="disabled")

    def _run_reachability(self, duration, interval):

        class SourceIPAdapter(HTTPAdapter):
            def __init__(self, source_ip, source_port=0, **kwargs):
                self.source_ip   = source_ip
                self.source_port = source_port
                super().__init__(**kwargs)

            def init_poolmanager(self, *args, **kwargs):
                kwargs["source_address"] = (self.source_ip, self.source_port)
                super().init_poolmanager(*args, **kwargs)

            def send(self, request, **kwargs):
                old_create = urllib3_conn.create_connection
                src_ip     = self.source_ip
                src_port   = self.source_port

                def patched_create(address, timeout=None, source_address=None,
                                   socket_options=None):
                    host, port = address
                    infos = socket.getaddrinfo(
                        host, port,
                        socket.AF_INET,
                        socket.SOCK_STREAM
                    )
                    af, socktype, proto, _, sockaddr = infos[0]
                    sock = socket.socket(af, socktype, proto)
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    if socket_options:
                        for opt in socket_options:
                            sock.setsockopt(*opt)
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

        timeout_val = float(self.get("reach_timeout")   or 5)
        src_ip      = self.get("reach_src_ip")          or self.get("ip_start")
        threshold   = float(self.get("reach_threshold") or 50) / 100
        reach_iface = self.get("reach_interface")       or self.get("interface")

        port_pool = parse_ports(self.get("src_ports"))
        src_port  = random.choice(port_pool) if port_pool else 0

        self.write_log(
            f"[Reachability] src={src_ip}:{src_port if src_port else 'random'} | "
            f"iface={reach_iface} | interval={interval}s | "
            f"timeout={timeout_val}s | failure_threshold={int(threshold*100)}%"
        )

        session = requests.Session()
        adapter = SourceIPAdapter(src_ip, source_port=src_port)
        session.mount("http://",  adapter)
        session.mount("https://", adapter)

        os.makedirs(DATA_DIR, exist_ok=True)
        reach_file = os.path.join(DATA_DIR, "reachability.csv")

        with open(reach_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp", "status_code", "elapsed_time_s"])
            start = time.time()
            while time.time() - start < duration:
                ts = time.strftime("%Y-%m-%d %H:%M:%S")
                try:
                    r = session.get(self.get("target"), timeout=timeout_val)
                    writer.writerow([ts, r.status_code, r.elapsed.total_seconds()])
                    self.write_log(
                        f"[Reachability] {ts} → {r.status_code} "
                        f"({r.elapsed.total_seconds():.3f}s)"
                    )
                except Exception as ex:
                    writer.writerow([ts, "FAIL", -1])
                    self.write_log(f"[Reachability] {ts} → FAIL ({ex})")
                f.flush()
                time.sleep(interval)

        self.write_log("✓ Reachability monitoring complete → data/reachability.csv")

    # ================================================================
    # STEP 3 – REPORT
    # ================================================================

    def generate_report(self):
        threading.Thread(target=self._generate_report_thread, daemon=True).start()

    def _generate_report_thread(self):
        try:
            target_clean, target_ip, source_range, interface, reach_threshold, test_type_cfg = \
                self._load_test_config(BASE_DIR)

            self.write_log("=" * 60)
            self.write_log("▶ Generating PDF report...")

            create_pdf_report(
                stats_file      = os.path.join(DATA_DIR,   "report_stats.csv"),
                history_file    = os.path.join(DATA_DIR,   "report_stats_history.csv"),
                output_file     = os.path.join(REPORT_DIR, "Locust_Report.pdf"),
                meta_file       = os.path.join(DATA_DIR,   "report_metadata.csv"),
                network_file    = os.path.join(DATA_DIR,   "network_usage.csv"),
                comment         = self.get_comment(),
                target_ip       = target_ip,
                source_ip       = source_range,
                interface       = interface,
                reach_threshold = reach_threshold / 100,
                test_type       = test_type_cfg,
                src_ports       = self.get("src_ports") or None, 
            )

            self.write_log("✓ Locust_Report.pdf generated")
            self.write_log("=" * 60)

            pdf_path = os.path.join(REPORT_DIR, "Locust_Report.pdf")
            if sys.platform.startswith("linux"):
                subprocess.Popen(["xdg-open", pdf_path])
            elif sys.platform == "darwin":
                subprocess.Popen(["open", pdf_path])
            else:
                os.startfile(pdf_path)

        except Exception as e:
            self.write_log(f"✗ Report error: {e}")

    # ================================================================
    # STEP 4 – CLEANUP
    # ================================================================

    def cleanup(self):
        threading.Thread(target=self._cleanup_thread, daemon=True).start()

    def _cleanup_thread(self):
        try:
            self.write_log("=" * 60)
            self.write_log("▶ Removing IP pool from interface...")
            remove_pool(
                ip_start  = self.get("ip_start"),
                ip_end    = self.get("ip_end"),
                interface = self.get("interface"),
                pool_file = os.path.join(BASE_DIR, "ip_pool.txt")
            )
            self.write_log("✓ Cleanup complete")
            self.write_log("=" * 60)

        except Exception as e:
            self.write_log(f"✗ Cleanup error: {e}")


# ================================================================
# MAIN
# ================================================================

if __name__ == "__main__":
    app = LocustGUI()
    app.mainloop()

