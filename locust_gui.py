#!/usr/bin/env python3
import tkinter as tk
import tkinter.filedialog as fd
import customtkinter as ctk
import subprocess
import threading
import sys
import os
import time
import queue
import socket
import pandas as pd
import csv
import glob
import json
from urllib.parse import urlparse
from dotenv import load_dotenv, set_key
from CTkToolTip import CTkToolTip


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "network"))
sys.path.insert(0, os.path.join(BASE_DIR, "report"))

load_dotenv(dotenv_path=os.path.join(BASE_DIR, "config.env"), override=True)

from Locust_report_v3       import create_pdf_report
from Create_IP_Pool_skript  import main as create_pool
from Remove_IP_Pool_skript  import main as remove_pool
from Network_monitor        import NetworkMonitor
from Reachability           import run as run_reachability_check

DATA_DIR   = os.path.join(BASE_DIR, "data")
REPORT_DIR = os.path.join(BASE_DIR, "report")

# ── Themes ─────────────────────────────────────────────────────────
THEMES = {
    "Locust Dark": {
        "BG_SIDEBAR":  "#121212",
        "BG_MAIN":     "#111111",
        "BG_CARD":     "#1a1a1a",
        "ACCENT":      "#2a5f3a",
        "ACCENT_HOVER":"#1e4a2c",
        "FG_TEXT":     "#ffffff",
        "FG_MUTED":    "#888888",
        "FG_LABEL":    "#cccccc",
        "FG_HEADER":   "#2a5f3a",
        "BG_INPUT":    "#242424",
        "BTN_DANGER":  "#922b21",
        "BTN_START":   "#2a5f3a",
        "BTN_REPORT":  "#7D3C98",
        "BTN_SETUP":   "#2a5f3a",
    },
    "Navy Blue": {
        "BG_SIDEBAR":   "#222831",
        "BG_MAIN":      "#1c2128",
        "BG_CARD":      "#222831",
        "ACCENT":       "#23395B",
        "ACCENT_HOVER": "#23395B",
        "FG_TEXT":      "#DBD4D3",
        "FG_MUTED":     "#8899a6",
        "FG_LABEL":     "#FFFFFF",
        "FG_HEADER":    "#FFFFFF",
        "BG_INPUT":     "#2d3340",
        "BTN_DANGER":   "#922b21",
        "BTN_START":    "#23395B",
        "BTN_REPORT":   "#23395B",
        "BTN_SETUP":    "#23395B",
    },
    "Discord Light": {
        "BG_SIDEBAR":   "#282b30",   # tmavý panel
        "BG_MAIN":      "#36393e",   # hlavný obsah
        "BG_CARD":      "#424549",   # karty/sekcie
        "ACCENT":       "#7289da",   # blurple
        "ACCENT_HOVER": "#5b73c7",   # tmavší blurple
        "FG_TEXT":      "#dcddde",   # hlavný text (Discord štandard)
        "FG_MUTED":     "#72767d",   # tlmený text
        "FG_LABEL":     "#b9bbbe",   # labely polí
        "FG_HEADER":    "#7289da",   # nadpisy sekcií
        "BG_INPUT":     "#1e2124",   # najtmavšie — inputy
        "BTN_DANGER":   "#ed4245",   # Discord červená
        "BTN_START":    "#7289da",   # Discord blurple
        "BTN_REPORT":   "#7289da",   # blurple
        "BTN_SETUP":    "#7289da",   # blurple
    },
    "Discord Darkest": {
        "BG_SIDEBAR":   "#121214",   # takmer čierna
        "BG_MAIN":      "#1a1a1e",   
        "BG_CARD":      "#242428",   
        "ACCENT":       "#5b73c7",   # blurple
        "ACCENT_HOVER": "#7289da",
        "FG_TEXT":      "#dcddde",
        "FG_MUTED":     "#72767d",
        "FG_LABEL":     "#b9bbbe",
        "FG_HEADER":    "#7289da",
        "BG_INPUT":     "#0d0e10",   # absolútne najtemnejšia
        "BTN_DANGER":   "#ed4245",
        "BTN_START":    "#5b73c7",
        "BTN_REPORT":   "#5b73c7",
        "BTN_SETUP":    "#5b73c7",
    },
    "Netflix": {
    "BG_SIDEBAR":   "#141414",   # Netflix čierna
    "BG_MAIN":      "#181818",   # hlavné pozadie
    "BG_CARD":      "#222222",   # karty
    "ACCENT":       "#800000",   # Netflix červená
    "ACCENT_HOVER": "#b20710",   # tmavšia červená
    "FG_TEXT":      "#ffffff",   # biely text
    "FG_MUTED":     "#808080",   # šedý text
    "FG_LABEL":     "#b3b3b3",   # labely
    "FG_HEADER":    "#ffffff",   # nadpisy červené
    "BG_INPUT":     "#0d0d0d",   # najtmavší input
    "BTN_DANGER":   "#A40031",   # červená = danger
    "BTN_START":    "#015041",   # Netflix zelená (playing indicator)
    "BTN_REPORT":   "#015041",   # červená
    "BTN_SETUP":    "#015041",   # červená
},
}

STAGE_PRESETS = {
    "Flat":      [{"duration": 300, "users": 50,  "spawn_rate": 5}],
    "Stress":    [{"duration": 60,  "users": 10,  "spawn_rate": 5},
                  {"duration": 120, "users": 50,  "spawn_rate": 10},
                  {"duration": 180, "users": 100, "spawn_rate": 20},
                  {"duration": 300, "users": 300, "spawn_rate": 50},
                  {"duration": 360, "users": 0,   "spawn_rate": 10}],
    "Spike":     [{"duration": 30,  "users": 10,  "spawn_rate": 2},
                  {"duration": 60,  "users": 500, "spawn_rate": 200},
                  {"duration": 90,  "users": 10,  "spawn_rate": 50}],
    "Endurance": [{"duration": 300,  "users": 10, "spawn_rate": 2},
                  {"duration": 7200, "users": 25, "spawn_rate": 1},
                  {"duration": 7500, "users": 0,  "spawn_rate": 5}],
    "Capacity":  [{"duration": 120, "users": 10,  "spawn_rate": 2},
                  {"duration": 240, "users": 25,  "spawn_rate": 2},
                  {"duration": 360, "users": 50,  "spawn_rate": 5},
                  {"duration": 480, "users": 100, "spawn_rate": 10},
                  {"duration": 600, "users": 150, "spawn_rate": 10},
                  {"duration": 720, "users": 200, "spawn_rate": 20}],
}


def apply_theme(name):
    global C_SIDEBAR, C_CONTENT, C_CARD, C_ACTIVE, C_HOVER
    global C_TEXT, C_MUTED, C_LABEL, C_HEADER, C_ENTRY
    global C_DANGER, C_SUCCESS, C_PURPLE, C_BLUE
    t = THEMES[name]
    C_SIDEBAR = t["BG_SIDEBAR"]
    C_CONTENT = t["BG_MAIN"]
    C_CARD    = t["BG_CARD"]
    C_ACTIVE  = t["ACCENT"]
    C_HOVER   = t["ACCENT_HOVER"]
    C_TEXT    = t["FG_TEXT"]
    C_MUTED   = t["FG_MUTED"]
    C_LABEL   = t["FG_LABEL"]
    C_HEADER  = t["FG_HEADER"]
    C_ENTRY   = t["BG_INPUT"]
    C_DANGER  = t["BTN_DANGER"]
    C_SUCCESS = t["BTN_START"]
    C_PURPLE  = t["BTN_REPORT"]
    C_BLUE    = t["BTN_SETUP"]


ZOOM_MIN  = 0.5
ZOOM_MAX  = 2.0
ZOOM_STEP = 0.1


# ============================================================
#  HELPERS
# ============================================================

def parse_ports(port_str):
    if not port_str or not port_str.strip():
        return None
    port_str = port_str.strip()
    if "-" in port_str and "," not in port_str:
        parts = port_str.split("-")
        return list(range(int(parts[0]), int(parts[1]) + 1))
    return [int(p.strip()) for p in port_str.split(",")]

def is_ipv6(ip):
    try:
        socket.inet_pton(socket.AF_INET6, ip)
        return True
    except (socket.error, OSError):
        return False

def ipv6_range_to_list(start_str, end_str):
    import ipaddress
    start = int(ipaddress.IPv6Address(start_str))
    end   = int(ipaddress.IPv6Address(end_str))
    return [str(ipaddress.IPv6Address(i)) for i in range(start, end + 1)]

def ipv6_prefix_to_list(prefix_str, max_count=256):
    import ipaddress
    net = ipaddress.IPv6Network(prefix_str, strict=False)
    return [str(ip) for ip in list(net.hosts())[:max_count]]

def darken(hex_color, amount=40):
    hex_color = hex_color.lstrip("#")
    r, g, b   = tuple(max(0, int(hex_color[i:i+2], 16) - amount) for i in (0, 2, 4))
    return f"#{r:02x}{g:02x}{b:02x}"

def bind_card(widget, cmd, hover_color, normal_color):
    def on_click(e): cmd()
    def on_enter(e): widget.configure(fg_color=hover_color)
    def on_leave(e): widget.configure(fg_color=normal_color)
    for w in [widget] + list(widget.winfo_children()):
        w.bind("<Button-1>", on_click)
        w.bind("<Enter>", on_enter)
        w.bind("<Leave>", on_leave)

def make_scroll_frame(parent, **kwargs):
    sf = ctk.CTkScrollableFrame(
        parent,
        fg_color="transparent",
        corner_radius=0,
        label_text="",
        label_fg_color="transparent",
        **kwargs
    )
    try:
        sf._label_frame.grid_remove()
    except Exception:
        pass
    return sf

def get_network_interfaces():
    interfaces = []
    try:
        with open("/proc/net/dev", "r") as f:
            for line in f.readlines()[2:]:
                iface = line.split(":")[0].strip()
                if iface and iface != "lo":
                    interfaces.append(iface)
    except Exception:
        pass
    return interfaces if interfaces else ["ens33", "eth0", "wlan0"]


# ============================================================
#  MAIN GUI
# ============================================================

class LocustGUI(ctk.CTk):

    NAV_ITEMS = [
        ("⚙",  "Config"),
        ("🌐", "HTTP/S"),
        ("📄", "Generate Report"),
        ("📋", "Reports"),
    ]

    LBL_W  = 160
    ENTR_W = 220

    def __init__(self, initial_theme="Locust Dark"):
        super().__init__()
        apply_theme(initial_theme)
        self._current_theme   = initial_theme
        self._network_monitor = None
        self._reach_stop_event = threading.Event()

        self.title("Locust Test GUI")
        self.geometry("1100x800")
        self.minsize(900, 600)
        self.configure(fg_color=C_CONTENT)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)

        self.locust_process  = None
        self.log_queue       = queue.Queue()
        self.locustfile_path = None
        self.entries         = {}
        self._labels         = {}
        self._active_page    = None
        self._nav_buttons    = {}
        self._pages          = {}
        self._zoom           = 1.0

        # stages — inicializácia pred _build_main
        self._stages      = []
        self._stage_rows  = []
        self._preset_btns = {}

        self._build_sidebar()
        self._build_log()
        self._build_main()
        self._load_env_to_gui()

        self._show_page("Config")
        self._poll_log_queue()

        self.bind_all("<Control-equal>",       self._zoom_in)
        self.bind_all("<Control-plus>",        self._zoom_in)
        self.bind_all("<Control-KP_Add>",      self._zoom_in)
        self.bind_all("<Control-minus>",       self._zoom_out)
        self.bind_all("<Control-KP_Subtract>", self._zoom_out)
        self.bind_all("<Control-0>",           self._zoom_reset)

        self._bind_scroll()

    # ================================================================
    # THEME
    # ================================================================

    def _change_theme(self, theme_name):
        self.write_log(f"🎨 Theme changed to: {theme_name}")
        self.after(200, lambda: self._restart_with_theme(theme_name))

    def _restart_with_theme(self, theme_name):
        self.destroy()
        app = LocustGUI(initial_theme=theme_name)
        app.mainloop()

    # ================================================================
    # ENV LOAD / SAVE
    # ================================================================

    def _load_env_to_gui(self):
        mapping = {
            "target":           os.getenv("TARGET_HOST"),
            "interface":        os.getenv("INTERFACE"),
            "test_type":        os.getenv("TEST_TYPE"),
            "ip_start":         os.getenv("IP_START"),
            "ip_end":           os.getenv("IP_END"),
            "ipv4prefix":       os.getenv("IPV4PREFIX", "32"),
            "ip6_start":        os.getenv("IP6_START"),
            "ip6_end":          os.getenv("IP6_END"),
            "ip6_prefix":       os.getenv("IP6_PREFIX"),
            "ipv6rangeprefix":  os.getenv("IPV6RPREFIX", "128"),
            "processes":        os.getenv("PROCESSES"),
            "stop_timeout":     os.getenv("STOP_TIMEOUT", "60"),
            "reach_interval":   os.getenv("REACH_INTERVAL"),
            "reach_timeout":    os.getenv("REACH_TIMEOUT"),
            "reach_src_ip":     os.getenv("REACH_SRC_IP", ""),
            "reach_interface":  os.getenv("REACH_INTERFACE", ""),
            "reach_threshold":  os.getenv("REACH_THRESHOLD"),
        }
        for key, value in mapping.items():
            if value and key in self.entries:
                widget = self.entries[key]
                if isinstance(widget, ctk.CTkComboBox):
                    widget.set(value)
                else:
                    widget.delete(0, "end")
                    widget.insert(0, value)

        self.ipv6_mode.set(os.getenv("IPV6_MODE", "range"))
        self._on_ipv6_mode_change()
        if os.getenv("IP_VERSION", "ipv4") == "ipv6":
            self.ip_tab.set("IPv6")

        # ── Stages — musí byť posledné ────────────────────────────
        stages_raw = os.getenv("STAGES", "")
        if stages_raw:
            try:
                self._stages = json.loads(stages_raw)
                self._render_stage_rows()
                for btn in self._preset_btns.values():
                    btn.configure(fg_color=C_ENTRY, text_color=C_TEXT)
            except Exception:
                self._load_preset("Stress")
        else:
            self._load_preset("Stress")

    def _save_env_from_gui(self):
        env_path = os.path.join(BASE_DIR, "config.env")
        mapping = {
            "TARGET_HOST":     self.get("target"),
            "INTERFACE":       self.get("interface"),
            "TEST_TYPE":       self.get("test_type"),
            "IP_VERSION":      self._active_ip_version(),
            "IP_START":        self.entries["ip_start"].get().strip(),
            "IP_END":          self.entries["ip_end"].get().strip(),
            "IPV4PREFIX":      self.entries["ipv4prefix"].get(),
            "IP6_START":       self.entries["ip6_start"].get().strip(),
            "IP6_END":         self.entries["ip6_end"].get().strip(),
            "IP6_PREFIX":      self.entries["ip6_prefix"].get().strip(),
            "IPV6_MODE":       self.ipv6_mode.get(),
            "IPV6RPREFIX":     self.entries["ipv6rangeprefix"].get(),
            "PROCESSES":       self.get("processes"),
            "STOP_TIMEOUT":    self.get("stop_timeout"),
            "REACH_INTERVAL":  self.get("reach_interval"),
            "REACH_TIMEOUT":   self.get("reach_timeout"),
            "REACH_SRC_IP":    self.get("reach_src_ip"),
            "REACH_INTERFACE": self.get("reach_interface"),
            "REACH_THRESHOLD": self.get("reach_threshold"),
            "STAGES":          json.dumps(self._get_stages()),
        }
        for key, val in mapping.items():
            set_key(env_path, key, val)
        self.write_log("✓ Config saved to config.env")

    # ================================================================
    # ZOOM
    # ================================================================

    def _zoom_in(self, event=None):
        if self._zoom < ZOOM_MAX:
            self._zoom = round(self._zoom + ZOOM_STEP, 1)
            self._apply_zoom()
        return "break"

    def _zoom_out(self, event=None):
        if self._zoom > ZOOM_MIN:
            self._zoom = round(self._zoom - ZOOM_STEP, 1)
            self._apply_zoom()
        return "break"

    def _zoom_reset(self, event=None):
        self._zoom = 1.0
        self._apply_zoom()
        return "break"

    def _apply_zoom(self):
        w = self.winfo_width()
        h = self.winfo_height()
        self.focus_set()
        ctk.set_widget_scaling(self._zoom)
        self.geometry(f"{w}x{h}")
        self.write_log(f"🔍 Zoom: {int(self._zoom * 100)}%")

    # ================================================================
    # SCROLL
    # ================================================================

    def _bind_scroll(self):
        self.bind_all("<MouseWheel>", self._on_mousewheel)
        self.bind_all("<Button-4>",   self._on_mousewheel)
        self.bind_all("<Button-5>",   self._on_mousewheel)

    def _on_mousewheel(self, event):
        if isinstance(event.widget, tk.Text):
            return
        widget = event.widget
        while widget:
            if isinstance(widget, ctk.CTkScrollableFrame):
                top, bottom = widget._parent_canvas.yview()
                if top == 0.0 and bottom == 1.0:
                    return "break"
                if event.num == 4:
                    widget._parent_canvas.yview_scroll(-1, "units")
                elif event.num == 5:
                    widget._parent_canvas.yview_scroll(1, "units")
                else:
                    units = int(-1 * (event.delta / abs(event.delta))) if event.delta != 0 else 0
                    widget._parent_canvas.yview_scroll(units, "units")
                return "break"
            try:
                widget = widget.master
            except AttributeError:
                break

    # ================================================================
    # SIDEBAR
    # ================================================================

    def _build_sidebar(self):
        sidebar = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color=C_SIDEBAR)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_rowconfigure(8, weight=1)
        sidebar.grid_propagate(False)

        ctk.CTkLabel(
            sidebar, text="🦗 Locust",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=C_HEADER
        ).grid(row=0, column=0, padx=20, pady=(24, 4), sticky="w")

        ctk.CTkLabel(
            sidebar, text="Load Test GUI",
            font=ctk.CTkFont(size=11),
            text_color=C_MUTED
        ).grid(row=1, column=0, padx=20, pady=(0, 24), sticky="w")

        ctk.CTkFrame(sidebar, height=1, fg_color="#2a3a5e"
                     ).grid(row=2, column=0, padx=12, pady=(0, 12), sticky="ew")

        for i, (icon, label) in enumerate(self.NAV_ITEMS):
            btn = ctk.CTkButton(
                sidebar,
                text=f"  {icon}  {label}",
                anchor="w",
                fg_color="transparent",
                hover_color=C_HOVER,
                text_color=C_TEXT,
                font=ctk.CTkFont(size=13),
                corner_radius=8,
                height=42,
                command=lambda l=label: self._show_page(l)
            )
            btn.grid(row=3+i, column=0, padx=10, pady=3, sticky="ew")
            self._nav_buttons[label] = btn

        ctk.CTkFrame(sidebar, height=1, fg_color="#2a3a5e"
                     ).grid(row=8, column=0, padx=12, pady=12, sticky="ew")

        ctk.CTkLabel(sidebar, text="THEME",
                     font=ctk.CTkFont(size=10, weight="bold"),
                     text_color=C_MUTED
                     ).grid(row=9, column=0, padx=20, pady=(4, 2), sticky="w")

        self._theme_combo = ctk.CTkComboBox(
            sidebar,
            values=list(THEMES.keys()),
            width=170,
            fg_color=darken(C_SIDEBAR),
            button_color=C_ACTIVE,
            button_hover_color=C_HOVER,
            dropdown_fg_color=C_SIDEBAR,
            dropdown_text_color=C_TEXT,
            command=self._change_theme
        )
        self._theme_combo.set(self._current_theme)
        self._theme_combo.grid(row=10, column=0, padx=(15, 0), pady=(0, 8), sticky="w")

        ctk.CTkLabel(
            sidebar, text="v0.1  •  2026",
            font=ctk.CTkFont(size=10),
            text_color=C_MUTED
        ).grid(row=11, column=0, padx=20, pady=(0, 16), sticky="w")

    # ================================================================
    # MAIN CONTENT AREA
    # ================================================================

    def _build_main(self):
        self.main = ctk.CTkFrame(self._paned, corner_radius=0, fg_color=C_CONTENT)
        self._paned.add(self.main,      minsize=300, stretch="always")
        self._paned.add(self._logframe, minsize=80,  stretch="never")

        self.main.grid_columnconfigure(0, weight=1)
        self.main.grid_rowconfigure(2, weight=1)

        self.page_title = ctk.CTkLabel(
            self.main, text="",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=C_TEXT, anchor="w"
        )
        self.page_title.grid(row=0, column=0, padx=24, pady=(18, 8), sticky="ew")

        ctk.CTkFrame(self.main, height=1, fg_color="#2a3a5e"
                     ).grid(row=1, column=0, padx=0, pady=0, sticky="ew")

        self.page_container = ctk.CTkFrame(self.main, fg_color="transparent", corner_radius=0)
        self.page_container.grid(row=2, column=0, sticky="nsew", padx=0, pady=0)
        self.page_container.grid_columnconfigure(0, weight=1)
        self.page_container.grid_rowconfigure(0, weight=1)

        self._pages["Config"]          = self._build_page_config(self.page_container)
        self._pages["HTTP"]            = self._build_page_http(self.page_container)
        self._pages["Generate Report"] = self._build_page_report(self.page_container)
        self._pages["Reports"]         = self._build_page_reports(self.page_container)
        self.after(100, self._set_sash_default)

    def _show_page(self, name):
        for label, btn in self._nav_buttons.items():
            if label == name:
                btn.configure(fg_color=C_ACTIVE, text_color="white",
                               font=ctk.CTkFont(size=13, weight="bold"))
            else:
                btn.configure(fg_color="transparent", text_color=C_TEXT,
                               font=ctk.CTkFont(size=13, weight="normal"))
        for label, frame in self._pages.items():
            if label == name:
                frame.grid()
            else:
                frame.grid_remove()
        icon = next(ic for ic, lb in self.NAV_ITEMS if lb == name)
        self.page_title.configure(text=f"{icon}  {name}")
        self._active_page = name

    def _set_sash_default(self):
        total = self._paned.winfo_height()
        self._paned.sash_place(0, 0, total - 200)

    # ================================================================
    # PAGE – CONFIG
    # ================================================================

    def _build_page_config(self, parent):
        outer = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        outer.grid(row=0, column=0, sticky="nsew")
        outer.grid_columnconfigure(0, weight=1)
        outer.grid_rowconfigure(0, weight=1)
        outer.grid_rowconfigure(1, weight=0)

        scroll = make_scroll_frame(outer)
        scroll.grid(row=0, column=0, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)

        row = 0

        row = self._card_header(scroll, "General", row)
        card = self._card(scroll, row); row += 1
        self._field_row(card, 0, "Target host",  "target",    "https://google.sk", help="Full URL or IP address of the server under test.\nExample: https://192.168.1.1 or http://myapp.local:8080")
        ifaces = get_network_interfaces()
        self._combo_row(card, 1, "Interface", "interface", ifaces,
                os.getenv("INTERFACE", ifaces[0] if ifaces else "ens33"),help="Network interface used to send outgoing requests.\nMust match the interface where the IP pool will be assigned.")
        self._field_row(card, 0, "Test type",    "test_type", "Load Test", col=2, help="Label describing the test scenario.\nAppears in the generated PDF report header.")
        self._field_row(card, 1, "Source ports", "src_ports", "",          col=2,
                        ph="e.g. 1024-65535", help="Source port range for outgoing connections.\nFormats: single (8080), range (1024-65535), list (8080,8081,8082).\nLeave empty to let the OS assign ports automatically.")
                        
                        # SSL checkbox
        self._ssl_verify_var = ctk.BooleanVar(value=os.getenv("SSL_VERIFY", "true").lower() != "false")
        ssl_cb = ctk.CTkCheckBox(
            card,
            text="Verify SSL certificate",
            variable=self._ssl_verify_var,
            font=ctk.CTkFont(size=13),
            text_color=C_TEXT,
            fg_color=C_ACTIVE,
            hover_color=C_HOVER,
            border_color=C_MUTED,
        )
        ssl_cb.grid(row=2, column=0, columnspan=2, padx=(16, 8), pady=(0, 12), sticky="w")
        CTkToolTip(ssl_cb, message="When disabled, HTTPS requests do not verify the server certificate.\nUseful for testing self-signed certificates", delay=0.3, x_offset=10, y_offset=-10)

        row = self._card_header(scroll, "IP Pool", row)
        card2 = self._card(scroll, row); row += 1

        self.ip_tab = ctk.CTkTabview(card2, height=110, fg_color=C_CARD,
                                     segmented_button_fg_color=darken(C_CARD),
                                     segmented_button_selected_color=C_ACTIVE)
        self.ip_tab.grid(row=0, column=0, columnspan=4, padx=12, pady=8, sticky="ew")
        self.ip_tab.add("IPv4")
        self.ip_tab.add("IPv6")

        # ── IPv4 tab ──────────────────────────────────────────────
        v4 = self.ip_tab.tab("IPv4")
        v4.grid_columnconfigure(0, minsize=self.LBL_W)
        v4.grid_columnconfigure(1, weight=1)
        for i, (lbl, key, default) in enumerate([
            ("IP range start", "ip_start", "192.168.10.10"),
            ("IP range end",   "ip_end",   "192.168.10.40"),
        ]):
            ctk.CTkLabel(v4, text=lbl, font=ctk.CTkFont(size=12),
                         text_color=C_LABEL, anchor="w", width=self.LBL_W
                         ).grid(row=i, column=0, padx=(16, 8), pady=6, sticky="w")
            e = ctk.CTkEntry(v4, fg_color=C_ENTRY)
            e.insert(0, default)
            e.grid(row=i, column=1, padx=(0, 16), pady=6, sticky="ew")
            self.entries[key] = e

        ctk.CTkLabel(v4, text="Prefix /", font=ctk.CTkFont(size=12),
                     text_color=C_LABEL, anchor="w", width=self.LBL_W
                     ).grid(row=2, column=0, padx=(16, 8), pady=6, sticky="w")
        cb_v4_prefix = ctk.CTkComboBox(
            v4, values=["32","31","30","29","28","27","26","25","24","16","8"],
            width=self.ENTR_W, fg_color=C_ENTRY,
            button_color=C_ACTIVE, button_hover_color=C_HOVER,
            dropdown_fg_color=C_CARD, dropdown_text_color=C_TEXT
        )
        cb_v4_prefix.set("32")
        cb_v4_prefix.grid(row=2, column=1, padx=(0, 16), pady=6, sticky="ew")
        self.entries["ipv4prefix"] = cb_v4_prefix

        # ── IPv6 tab ──────────────────────────────────────────────
        v6 = self.ip_tab.tab("IPv6")
        v6.grid_columnconfigure(1, weight=1)
        v6.grid_columnconfigure(3, weight=1)
        self.ipv6_mode = ctk.StringVar(value="range")
        mf = ctk.CTkFrame(v6, fg_color="transparent")
        mf.grid(row=0, column=0, columnspan=4, sticky="w", padx=8, pady=(4, 2))
        ctk.CTkLabel(mf, text="Mode:", font=ctk.CTkFont(size=11),
                     text_color=C_MUTED).pack(side="left", padx=(0, 8))
        for val, txt in [("range", "Range"), ("prefix", "Prefix")]:
            ctk.CTkRadioButton(mf, text=txt, variable=self.ipv6_mode, value=val,
                               command=self._on_ipv6_mode_change,
                               font=ctk.CTkFont(size=11),
                               fg_color=C_ACTIVE, hover_color=C_HOVER,
                               border_color=C_MUTED
                               ).pack(side="left", padx=4)

        self.ipv6_range_frame = ctk.CTkFrame(v6, fg_color="transparent")
        self.ipv6_range_frame.grid(row=1, column=0, columnspan=4, sticky="ew")
        self.ipv6_range_frame.grid_columnconfigure(0, minsize=self.LBL_W)
        self.ipv6_range_frame.grid_columnconfigure(1, weight=1)
        for i, (lbl, key, dflt) in enumerate([("IPv6 start", "ip6_start", "fd00::10"),
                                               ("IPv6 end",   "ip6_end",   "fd00::40")]):
            ctk.CTkLabel(self.ipv6_range_frame, text=lbl, font=ctk.CTkFont(size=11),
                         text_color=C_LABEL, anchor="w", width=self.LBL_W
                         ).grid(row=i, column=0, padx=(16, 8), pady=4, sticky="w")
            e = ctk.CTkEntry(self.ipv6_range_frame, fg_color=C_ENTRY)
            e.insert(0, dflt)
            e.grid(row=i, column=1, padx=(0, 16), pady=4, sticky="ew")
            self.entries[key] = e

        ctk.CTkLabel(self.ipv6_range_frame, text="Prefix /",
                     font=ctk.CTkFont(size=11), text_color=C_LABEL,
                     anchor="w", width=self.LBL_W
                     ).grid(row=2, column=0, padx=(16, 8), pady=4, sticky="w")
        cb_v6_prefix = ctk.CTkComboBox(
            self.ipv6_range_frame,
            values=["128","127","126","120","112","96","64"],
            width=self.ENTR_W, fg_color=C_ENTRY,
            button_color=C_ACTIVE, button_hover_color=C_HOVER,
            dropdown_fg_color=C_CARD, dropdown_text_color=C_TEXT
        )
        cb_v6_prefix.set("128")
        cb_v6_prefix.grid(row=2, column=1, padx=(0, 16), pady=4, sticky="ew")
        self.entries["ipv6rangeprefix"] = cb_v6_prefix

        self.ipv6_prefix_frame = ctk.CTkFrame(v6, fg_color="transparent")
        self.ipv6_prefix_frame.grid(row=1, column=0, columnspan=4, sticky="ew")
        self.ipv6_prefix_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(self.ipv6_prefix_frame, text="IPv6 prefix",
                     font=ctk.CTkFont(size=11), text_color=C_LABEL, anchor="w"
                     ).grid(row=0, column=0, padx=(16, 8), pady=4, sticky="w")
        e = ctk.CTkEntry(self.ipv6_prefix_frame, width=self.ENTR_W, fg_color=C_ENTRY)
        e.insert(0, "fd00::/64")
        e.grid(row=0, column=1, padx=(0, 12), pady=4, sticky="ew")
        self.entries["ip6_prefix"] = e
        self.ipv6_prefix_frame.grid_remove()

        # ── Reachability ──────────────────────────────────────────
        row = self._card_header(scroll, "Reachability", row)
        card3 = self._card(scroll, row); row += 1
        self._field_row(card3, 0, "Interval (s)",         "reach_interval",  "5", help="How often (in seconds) a reachability probe is sent to the target\nduring the test. Lower = more precise, higher = less overhead.")
        self._field_row(card3, 1, "Timeout (s)",           "reach_timeout",   "5",help="Maximum time to wait for a response to each probe.\nProbes exceeding this limit are counted as failures.")
        self._field_row(card3, 0, "Source IP",             "reach_src_ip",    "", col=2, ph="= IP range start", help="Source IP used for reachability probes.\nLeave empty to use the first IP from the pool.\nUseful when you want probes from a specific address.")
        self._combo_row(card3, 1, "Interface", "reach_interface", [""] + get_network_interfaces(), "", col=2, help="Network interface used for reachability probes.\nLeave empty to use the main interface defined above.")
        self._field_row(card3, 2, "Failure threshold (%)", "reach_threshold", "50", col=0, help="Percentage of failed probes above which the test\nis marked as FAILED in the PDF report.\nExample: 50 means more than half of probes must succeed.")

        # ── Network Monitor ───────────────────────────────────────
        row = self._card_header(scroll, "Network Monitor", row)
        card_mon = self._card(scroll, row); row += 1
        ifaces = get_network_interfaces()
        self._combo_row(
            card_mon, 0, "Interface", "monitor_interface", ifaces,
            os.getenv("INTERFACE", ifaces[0] if ifaces else "ens33",),help="Interface to monitor for network traffic statistics\n(bytes sent/received, packets) during the test.\nResults are saved to network_usage.csv and shown in the report."
        )

        # ── Actions — fixed bottom ────────────────────────────────
        bf = ctk.CTkFrame(outer, fg_color=C_CONTENT, height=48)
        bf.grid(row=1, column=0, sticky="ew", padx=0, pady=0)
        bf.grid_propagate(False)
        bf.grid_columnconfigure(0, weight=1)  # spacer vľavo

        ctk.CTkButton(bf, text="⚙ Setup IP Pool", width=150, height=32,
            fg_color=C_BLUE, hover_color=darken(C_BLUE, 25),
            font=ctk.CTkFont(size=12), corner_radius=6,
            command=self.setup_env
        ).grid(row=0, column=1, padx=4, pady=8)

        ctk.CTkButton(bf, text="🗑 Cleanup", width=150, height=32,
            fg_color=C_DANGER, hover_color=darken(C_DANGER, 25),
            font=ctk.CTkFont(size=12), corner_radius=6,
            command=self.cleanup
        ).grid(row=0, column=2, padx=(4, 16), pady=8)

        return outer

    # ================================================================
    # PAGE – HTTP
    # ================================================================

    def _build_page_http(self, parent):
        outer = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        outer.grid(row=0, column=0, sticky="nsew")
        outer.grid_columnconfigure(0, weight=1)
        outer.grid_rowconfigure(0, weight=1)
        outer.grid_rowconfigure(1, weight=0)

        scroll = make_scroll_frame(outer)
        scroll.grid(row=0, column=0, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)

        s_row = 0
        
        # ── Define Test ───────────────────────────────────────────
        s_row = self._card_header(scroll, "Define Test", s_row)
        card_stages = ctk.CTkFrame(scroll, fg_color=C_CARD, corner_radius=10)
        card_stages.grid(row=s_row, column=0, padx=16, pady=(0, 4), sticky="ew")
        card_stages.grid_columnconfigure(0, weight=1)
        s_row += 1

        preset_frame = ctk.CTkFrame(card_stages, fg_color="transparent")
        preset_frame.grid(row=0, column=0, padx=12, pady=(10, 4), sticky="w")
        for name in STAGE_PRESETS:
            btn = ctk.CTkButton(
                preset_frame, text=name, width=80, height=26,
                fg_color=C_ENTRY, hover_color=C_HOVER,
                font=ctk.CTkFont(size=11), corner_radius=6,
                command=lambda n=name: self._load_preset(n)
            )
            btn.pack(side="left", padx=(0, 6))
            self._preset_btns[name] = btn

        self._stages_frame = ctk.CTkFrame(card_stages, fg_color="transparent")
        self._stages_frame.grid(row=1, column=0, padx=12, pady=(2, 0), sticky="ew")
        self._stages_frame.grid_columnconfigure(0, minsize=180, weight=1)
        self._stages_frame.grid_columnconfigure(1, minsize=180, weight=1)
        self._stages_frame.grid_columnconfigure(2, minsize=180, weight=1)
        self._stages_frame.grid_columnconfigure(3, minsize=130, weight=0)
        self._stages_frame.grid_columnconfigure(4, minsize=55,  weight=0)
        self._stages_frame.grid_columnconfigure(5, minsize=55,  weight=0)
        self._stages_frame.grid_columnconfigure(6, minsize=30,  weight=0)
        self._hdr_min_lbl = None
        self._hdr_max_lbl = None
        for col, (txt, help_txt) in enumerate([
            ("Duration (s)", None),
            ("Users",        None),
            ("Spawn rate",   None),
            ("Wait mode",    "between – random wait between Min and Max\nconstant – fixed wait of Min seconds\nconstant_throughput – Min = target RPS per user"),
            ("Min",          "between: minimum wait (s)\nconstant: fixed wait (s)\nconstant_throughput: target RPS"),
            ("Max",          "between: maximum wait (s)\nIgnored in other modes"),
        ]):
            lbl = ctk.CTkLabel(
                self._stages_frame,
                text=f"{txt.upper()} ⓘ" if help_txt else txt.upper(),
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color=C_MUTED, anchor="w",
                cursor="question_arrow" if help_txt else "arrow"
            )
            lbl.grid(row=0, column=col, padx=(0,4), pady=4, sticky="w")
            if help_txt:
                CTkToolTip(lbl, message=help_txt, delay=0.3, x_offset=10, y_offset=-10)
            if txt == "Min":
                self._hdr_min_lbl = lbl
            elif txt == "Max":
                self._hdr_max_lbl = lbl

        ctk.CTkButton(
            card_stages, text="+ Add stage", height=28,
            fg_color="transparent", hover_color=C_HOVER,
            border_width=1, border_color=C_MUTED,
            font=ctk.CTkFont(size=11), corner_radius=6,
            command=self._add_stage_row
        ).grid(row=3, column=0, padx=12, pady=(6, 4), sticky="ew")

        self._stages_total_lbl = ctk.CTkLabel(
            card_stages, text="",
            font=ctk.CTkFont(size=11), text_color=C_MUTED, anchor="w"
        )
        self._stages_total_lbl.grid(row=4, column=0, padx=14, pady=(0, 10), sticky="w")
               # ── Locust Parameters ─────────────────────────────────────
        s_row = self._card_header(scroll, "Locust Parameters", s_row)
        card = self._card(scroll, s_row); s_row += 1
        self._field_row(card, 0, "Stop timeout (s)", "stop_timeout", "60", col=0, help="Time (seconds) Locust waits for running users to finish\ntheir current task after the test ends.\nIncrease for long-running requests.")
        self._field_row(card, 0, "Processes", "processes", "-1", col=2, help="Number of worker processes Locust spawns.\n-1 = one process per CPU core (recommended).\n1 = single process (useful for debugging).")


        # ── Locustfile ────────────────────────────────────────────
        s_row = self._card_header(scroll, "Locustfile", s_row)
        card_lf = self._card(scroll, s_row); s_row += 1

        ctk.CTkLabel(card_lf, text="File", font=ctk.CTkFont(size=15),
                     text_color=C_LABEL, anchor="w", width=self.LBL_W
                     ).grid(row=0, column=0, padx=(16, 8), pady=10, sticky="w")
        self._locustfile_label = ctk.CTkLabel(
            card_lf, text="default: Locustfile_http.py",
            font=ctk.CTkFont(size=11), text_color=C_MUTED, anchor="w"
        )
        self._locustfile_label.grid(row=0, column=1, padx=(0, 8), pady=10, sticky="ew")
        ctk.CTkButton(card_lf, text="Browse", width=80,
                      fg_color=C_ENTRY, hover_color=C_HOVER,
                      font=ctk.CTkFont(size=12), corner_radius=6,
                      command=self._browse_locustfile
                      ).grid(row=0, column=2, padx=(0, 8), pady=10)
        ctk.CTkButton(card_lf, text="✖", width=36,
                      fg_color=darken(C_DANGER, 10), hover_color=C_DANGER,
                      font=ctk.CTkFont(size=12), corner_radius=6,
                      command=self._clear_locustfile
                      ).grid(row=0, column=3, padx=(0, 16), pady=10)

        # ── Actions — fixed bottom ────────────────────────────────
        bf = ctk.CTkFrame(outer, fg_color=C_CONTENT, height=48)
        bf.grid(row=1, column=0, sticky="ew", padx=0, pady=0)
        bf.grid_propagate(False)
        bf.grid_columnconfigure(0, weight=1)

        self.runbtn = ctk.CTkButton(bf, text="▶ Start Test", width=150, height=32,
            fg_color=C_SUCCESS, hover_color=darken(C_SUCCESS, 25),
            font=ctk.CTkFont(size=12), corner_radius=6,
            command=self.run_test
        )
        self.runbtn.grid(row=0, column=1, padx=4, pady=8)

        self.stopbtn = ctk.CTkButton(bf, text="■ Stop", width=150, height=32,
            fg_color="#3a3a3a", hover_color=C_DANGER,
            font=ctk.CTkFont(size=12), corner_radius=6,
            state="disabled", command=self.stop_locust
        )
        self.stopbtn.grid(row=0, column=2, padx=(4, 16), pady=8)

        return outer

    # ================================================================
    # STAGE HELPERS
    # ================================================================

    def _load_preset(self, name):
        for n, btn in self._preset_btns.items():
            btn.configure(
                fg_color=C_ACTIVE if n == name else C_ENTRY,
                text_color="white" if n == name else C_TEXT
            )
        self._stages = [dict(s) for s in STAGE_PRESETS[name]]
        self._render_stage_rows()

    def _add_stage_row(self):
        last = self._stages[-1] if self._stages else {"duration": 0, "users": 0, "spawn_rate": 2}
        self._stages.append({
            "duration":   last["duration"] + 60,
            "users":      last["users"] + 10,
            "spawn_rate": last["spawn_rate"],
        })
        for btn in self._preset_btns.values():
            btn.configure(fg_color=C_ENTRY, text_color=C_TEXT)
        self._render_stage_rows()

    def _del_stage_row(self, idx):
        if len(self._stages) > 1:
            self._stages.pop(idx)
            self._render_stage_rows()

    def _render_stage_rows(self):
        for w in self._stages_frame.winfo_children():
            if int(w.grid_info().get("row", 0)) >= 1:
                w.destroy()
        self._stage_rows = []

        for i, stage in enumerate(self._stages):
            row_entries = {}

            # Duration, Users, Spawn rate
            for col, key in enumerate(["duration", "users", "spawn_rate"]):
                e = ctk.CTkEntry(
                    self._stages_frame, fg_color=C_ENTRY,
                    font=ctk.CTkFont(size=12, family="Courier New")
                )
                e.insert(0, str(stage[key]))
                e.grid(row=i+1, column=col, padx=(0, 4), pady=3, sticky="ew")
                e.bind("<FocusOut>", lambda event: self._update_stage_totals())
                row_entries[key] = e

            # Wait mode combobox
            cb = ctk.CTkComboBox(
                self._stages_frame,
                values=["between", "constant", "constant_throughput"],
                width=120, fg_color=C_ENTRY,
                button_color=C_ACTIVE, button_hover_color=C_HOVER,
                dropdown_fg_color=C_CARD, dropdown_text_color=C_TEXT,
                font=ctk.CTkFont(size=11)
            )
            cb.set(stage.get("wait_mode", "between"))
            cb.grid(row=i+1, column=3, padx=(0, 4), pady=3, sticky="ew")
            row_entries["wait_mode"] = cb

            # Min
            e_min = ctk.CTkEntry(
                self._stages_frame, width=50, fg_color=C_ENTRY,
                font=ctk.CTkFont(size=12, family="Courier New")
            )
            e_min.insert(0, str(stage.get("wait_min", "1")))
            e_min.grid(row=i+1, column=4, padx=(0, 4), pady=3, sticky="ew")
            row_entries["wait_min"] = e_min

            # Max
            e_max = ctk.CTkEntry(
                self._stages_frame, width=50, fg_color=C_ENTRY,
                font=ctk.CTkFont(size=12, family="Courier New")
            )
            e_max.insert(0, str(stage.get("wait_max", "3")))
            e_max.grid(row=i+1, column=5, padx=(0, 4), pady=3, sticky="ew")
            row_entries["wait_max"] = e_max

            # Skry Max a roztiahni Min ak mode nie je "between"; aktualizuj aj header labely
            def _on_wait_mode_change(mode, _row=i+1, _emin=e_min, _emax=e_max):
                if mode == "between":
                    _emin.grid(row=_row, column=4, columnspan=1,
                               padx=(0, 4), pady=3, sticky="ew")
                    _emax.grid(row=_row, column=5,
                               padx=(0, 4), pady=3, sticky="ew")
                    if self._hdr_min_lbl:
                        self._hdr_min_lbl.grid(row=0, column=4, columnspan=1,
                                               padx=(0, 4), pady=4, sticky="w")
                        self._hdr_min_lbl.configure(text="MIN ⓘ")
                    if self._hdr_max_lbl:
                        self._hdr_max_lbl.grid(row=0, column=5,
                                               padx=(0, 4), pady=4, sticky="w")
                else:
                    _emax.grid_remove()
                    _emin.grid(row=_row, column=4, columnspan=2,
                               padx=(0, 4), pady=3, sticky="ew")
                    if self._hdr_min_lbl:
                        self._hdr_min_lbl.grid(row=0, column=4, columnspan=2,
                                               padx=(0, 4), pady=4, sticky="w")
                        self._hdr_min_lbl.configure(text="MIN ⓘ")
                    if self._hdr_max_lbl:
                        self._hdr_max_lbl.grid_remove()

            _on_wait_mode_change(stage.get("wait_mode", "between"))
            cb.configure(command=_on_wait_mode_change)

            # Delete button
            ctk.CTkButton(
                self._stages_frame, text="✕", width=28, height=28,
                fg_color="transparent", hover_color=C_DANGER,
                font=ctk.CTkFont(size=11), corner_radius=4,
                command=lambda idx=i: self._del_stage_row(idx)
            ).grid(row=i+1, column=6, padx=(2, 0), pady=3)

            self._stage_rows.append(row_entries)
        self._update_stage_totals()

    def _get_stages(self):
        stages = []
        for i, row in enumerate(self._stage_rows):
            try:
                wait_mode    = row["wait_mode"].get()
                wait_max_raw = row["wait_max"].get().strip()
                wait_min     = float(row["wait_min"].get().strip() or 1)
                wait_max     = float(wait_max_raw) if wait_max_raw else wait_min

                stages.append({
                    "duration":   int(row["duration"].get().strip()   or 0),
                    "users":      int(row["users"].get().strip()      or 0),
                    "spawn_rate": int(row["spawn_rate"].get().strip() or 1),
                    "wait_mode":  wait_mode,
                    "wait_min":   wait_min,
                    "wait_max":   wait_max,
                })
            except (ValueError, KeyError) as e:
                print(f"[WARN] Stage row {i+1} skipped: {e}")
        return stages
    def _update_stage_totals(self):
        try:
            stages    = self._get_stages()
            total_dur = stages[-1]["duration"] if stages else 0
            max_users = max(s["users"] for s in stages) if stages else 0
            m, s      = divmod(total_dur, 60)
            dur_str   = f"{m}m {s}s" if m > 0 else f"{s}s"
            self._stages_total_lbl.configure(
                text=f"Total: {dur_str}  •  Max users: {max_users}  •  Stages: {len(stages)}"
            )
        except Exception:
            pass

    def _save_stages(self):
        stages = self._get_stages()
        with open(os.path.join(BASE_DIR, "stages.json"), "w") as f:
            json.dump(stages, f)
        set_key(os.path.join(BASE_DIR, "config.env"), "STAGES", json.dumps(stages))
        self.write_log(f"✓ Stages saved ({len(stages)} stages)")
        return stages

    # ================================================================
    # PAGE – REPORT
    # ================================================================

    def _build_page_report(self, parent):
        outer = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        outer.grid(row=0, column=0, sticky="nsew")
        outer.grid_columnconfigure(0, weight=1)
        outer.grid_rowconfigure(0, weight=1)
        outer.grid_rowconfigure(1, weight=0)
        outer.grid_rowconfigure(2, weight=0)

        scroll = make_scroll_frame(outer)
        scroll.grid(row=0, column=0, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)

        t_row = 0

        t_row = self._card_header(scroll, "Comment", t_row)
        self.comment_text = ctk.CTkTextbox(
            scroll, height=140, corner_radius=8,
            font=ctk.CTkFont(size=12, family="Courier New"),
            fg_color=C_CARD
        )
        self.comment_text.grid(row=t_row, column=0, padx=16, pady=(4, 12), sticky="ew")
        self.comment_text.insert("0.0", "Write a comment for the report...")
        t_row += 1

        t_row = self._card_header(scroll, "Output", t_row)
        card_out = ctk.CTkFrame(scroll, fg_color=C_CARD, corner_radius=10)
        card_out.grid(row=t_row, column=0, padx=16, pady=(0, 4), sticky="ew")
        card_out.grid_columnconfigure(1, weight=1)
        t_row += 1

        ctk.CTkLabel(card_out, text="Report name", font=ctk.CTkFont(size=15),
                     text_color=C_LABEL, anchor="w", width=self.LBL_W
                     ).grid(row=0, column=0, padx=(16, 8), pady=10, sticky="w")
        self._report_name_entry = ctk.CTkEntry(card_out, fg_color=C_ENTRY,
                                               placeholder_text="Locust_Report")
        self._report_name_entry.insert(0, "Locust_Report")
        self._report_name_entry.grid(row=0, column=1, columnspan=2, padx=(0, 16), pady=10, sticky="ew")

        ctk.CTkLabel(card_out, text="Save to", font=ctk.CTkFont(size=15),
                     text_color=C_LABEL, anchor="w", width=self.LBL_W
                     ).grid(row=1, column=0, padx=(16, 8), pady=10, sticky="w")
        self._report_dir_entry = ctk.CTkEntry(card_out, fg_color=C_ENTRY,
                                              placeholder_text=REPORT_DIR)
        self._report_dir_entry.insert(0, REPORT_DIR)
        self._report_dir_entry.grid(row=1, column=1, padx=(0, 8), pady=10, sticky="ew")
        ctk.CTkButton(card_out, text="Browse", width=80,
                      fg_color=C_ENTRY, hover_color=C_HOVER,
                      font=ctk.CTkFont(size=12), corner_radius=6,
                      command=self._browse_save_dir
                      ).grid(row=1, column=2, padx=(0, 16), pady=10)

        t_row = self._card_header(scroll, "PDF Signing", t_row)
        card_sign = ctk.CTkFrame(scroll, fg_color=C_CARD, corner_radius=10)
        card_sign.grid(row=t_row, column=0, padx=16, pady=(0, 4), sticky="ew")
        card_sign.grid_columnconfigure(1, weight=1)
        t_row += 1

        self._sign_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(card_sign, text="Sign PDF", variable=self._sign_var,
                        font=ctk.CTkFont(size=12), text_color=C_TEXT,
                        command=self._on_sign_toggle
                        ).grid(row=0, column=0, columnspan=3, padx=16, pady=(12, 8), sticky="w")

        self._cert_sign_frame = ctk.CTkFrame(card_sign, fg_color="transparent")
        self._cert_sign_frame.grid(row=1, column=0, columnspan=3, sticky="ew")
        self._cert_sign_frame.grid_columnconfigure(1, weight=1)
        self._cert_sign_frame.grid_remove()

        ctk.CTkLabel(self._cert_sign_frame, text="Certificate", font=ctk.CTkFont(size=15),
                     text_color=C_LABEL, anchor="w", width=self.LBL_W
                     ).grid(row=0, column=0, padx=(16, 8), pady=8, sticky="w")
        self._cert_path_entry = ctk.CTkEntry(self._cert_sign_frame, fg_color=C_ENTRY,
                                             placeholder_text="Path to cert.p12")
        default_cert = os.path.join(REPORT_DIR, "cert.p12")
        if os.path.exists(default_cert):
            self._cert_path_entry.insert(0, default_cert)
        self._cert_path_entry.grid(row=0, column=1, padx=(0, 8), pady=8, sticky="ew")
        ctk.CTkButton(self._cert_sign_frame, text="Browse", width=80,
                      fg_color=C_ENTRY, hover_color=C_HOVER,
                      font=ctk.CTkFont(size=12), corner_radius=6,
                      command=self._browse_cert
                      ).grid(row=0, column=2, padx=(0, 16), pady=8)

        ctk.CTkLabel(self._cert_sign_frame, text="Password", font=ctk.CTkFont(size=15),
                     text_color=C_LABEL, anchor="w", width=self.LBL_W
                     ).grid(row=1, column=0, padx=(16, 8), pady=(0, 12), sticky="w")
        self.cert_pass = ctk.CTkEntry(self._cert_sign_frame, show="•",
                                      placeholder_text="Password for cert.p12",
                                      fg_color=C_ENTRY)
        self.cert_pass.grid(row=1, column=1, columnspan=2, padx=(0, 16), pady=(0, 12), sticky="ew")

        # ── Buttons row ───────────────────────────────────────────
        # separator
        ctk.CTkFrame(outer, height=1, fg_color=darken(C_CONTENT, 15)).grid(
            row=1, column=0, sticky="ew"
        )

        bf = ctk.CTkFrame(outer, fg_color=C_CONTENT, height=48)
        bf.grid(row=2, column=0, sticky="ew", padx=0, pady=0)
        bf.grid_propagate(False)
        bf.grid_columnconfigure(0, weight=1)

        ctk.CTkButton(bf, text="📄 Generate Report", width=150, height=32,
            fg_color=C_PURPLE, hover_color=darken(C_PURPLE, 25),
            font=ctk.CTkFont(size=12), corner_radius=6,
            command=self._generate_report
        ).grid(row=0, column=1, padx=4, pady=8)

        ctk.CTkButton(bf, text="🗑 Delete Data", width=110, height=32,
            fg_color=C_DANGER, hover_color=darken(C_DANGER, 25),
            font=ctk.CTkFont(size=12), corner_radius=6,
            command=self._delete_data
        ).grid(row=0, column=2, padx=(4, 16), pady=8)

        return outer

    def _on_sign_toggle(self):
        if self._sign_var.get():
            self._cert_sign_frame.grid()
        else:
            self._cert_sign_frame.grid_remove()

    def _browse_save_dir(self):
        path = fd.askdirectory(title="Select output folder",
                               initialdir=self._report_dir_entry.get().strip() or REPORT_DIR)
        if path:
            self._report_dir_entry.delete(0, "end")
            self._report_dir_entry.insert(0, path)

    def _browse_cert(self):
        path = fd.askopenfilename(title="Select certificate",
                                  filetypes=[("PKCS#12", "*.p12 *.pfx"), ("All files", "*.*")],
                                  initialdir=REPORT_DIR)
        if path:
            self._cert_path_entry.delete(0, "end")
            self._cert_path_entry.insert(0, path)

    def _browse_locustfile(self):
        path = fd.askopenfilename(
            title="Select Locustfile",
            initialdir=os.path.join(BASE_DIR, "locust_tests"),
            filetypes=[("Python files", "*.py"), ("All files", "*.*")]
        )
        if path:
            self.locustfile_path = path
            self._locustfile_label.configure(text=os.path.basename(path), text_color=C_TEXT)
            self.write_log(f"✓ Locustfile: {os.path.basename(path)}")

    def _clear_locustfile(self):
        self.locustfile_path = None
        self._locustfile_label.configure(text="default: Locustfile_http.py", text_color=C_MUTED)
        self.write_log("↩ Locustfile reset to default")

    def _delete_data(self):
        deleted = []
        errors  = []
        for f in glob.glob(os.path.join(DATA_DIR, "*.csv")):
            try:
                os.remove(f)
                deleted.append(os.path.basename(f))
            except Exception as e:
                errors.append(f"{os.path.basename(f)}: {e}")
        for fname in ["test_config.csv"]:
            fpath = os.path.join(BASE_DIR, fname)
            if os.path.exists(fpath):
                try:
                    os.remove(fpath)
                    deleted.append(fname)
                except Exception as e:
                    errors.append(f"{fname}: {e}")
        if deleted:
            self.write_log(f"🗑 Deleted: {', '.join(deleted)}")
        if errors:
            self.write_log(f"⚠ Errors: {', '.join(errors)}")
        if not deleted and not errors:
            self.write_log("ℹ No data files found to delete")

    # ================================================================
    # LOG
    # ================================================================

    def _build_log(self):
        self._paned = tk.PanedWindow(
            self, orient=tk.VERTICAL,
            bg="#2a2a2a", sashwidth=6,
            sashrelief="raised", sashpad=2
        )
        self._paned.grid(row=0, column=1, sticky="nsew")
        self.grid_rowconfigure(0, weight=1)

        self._logframe = tk.Frame(self._paned, bg="#0d1117")
        self._logframe.grid_columnconfigure(0, weight=1)
        self._logframe.grid_rowconfigure(1, weight=1)

        hdr = tk.Frame(self._logframe, bg="#0d1117")
        hdr.grid(row=0, column=0, padx=16, pady=(6, 2), sticky="ew")
        hdr.grid_columnconfigure(0, weight=1)

        tk.Label(hdr, text="Output Log",
                 font=("Courier New", 10, "bold"),
                 bg="#0d1117", fg=C_MUTED
                 ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(hdr, text="Clear", command=self.clear_log,
                      fg_color="#333", hover_color="#555",
                      font=ctk.CTkFont(size=11),
                      corner_radius=6, height=24, width=70
                      ).grid(row=0, column=1, sticky="e")

        self.log = ctk.CTkTextbox(
            self._logframe, corner_radius=0,
            font=ctk.CTkFont(size=11, family="Courier New"),
            fg_color="#0d1117", text_color="#c9d1d9",
            state="disabled"
        )
        self.log.grid(row=1, column=0, sticky="nsew")

        self.statusbar = ctk.CTkLabel(
            self._logframe, text="Ready",
            font=ctk.CTkFont(size=10),
            text_color=C_MUTED, anchor="w",
            fg_color=C_SIDEBAR, corner_radius=0, height=22
        )
        self.statusbar.grid(row=2, column=0, sticky="ew")

    # ================================================================
    # PAGE – REPORTS
    # ================================================================

    def _build_page_reports(self, parent):
        outer = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        outer.grid(row=0, column=0, sticky="nsew")
        outer.grid_columnconfigure(0, weight=1)
        outer.grid_rowconfigure(2, weight=0)

        toolbar = ctk.CTkFrame(outer, fg_color=C_CARD, corner_radius=0, height=44)
        toolbar.grid(row=0, column=0, sticky="ew", padx=0, pady=(0, 1))
        toolbar.grid_propagate(False)
        toolbar.grid_columnconfigure(0, weight=1)

        ctk.CTkButton(
            toolbar, text="⟳  Refresh", width=110, height=30,
            fg_color=C_ENTRY, hover_color=C_HOVER,
            font=ctk.CTkFont(size=12), corner_radius=6,
            command=self._refresh_reports
        ).grid(row=0, column=0, padx=12, pady=7, sticky="w")

        self._reports_dir_label = ctk.CTkLabel(
            toolbar, text=REPORT_DIR,
            font=ctk.CTkFont(size=10), text_color=C_MUTED, anchor="e"
        )
        self._reports_dir_label.grid(row=0, column=1, padx=12, sticky="e")

        hdr = ctk.CTkFrame(outer, fg_color=darken(C_CARD, 15), corner_radius=0, height=32)
        hdr.grid(row=1, column=0, sticky="ew", padx=(8, 0))
        hdr.grid_propagate(False)
        hdr.grid_columnconfigure(0, weight=1)
        hdr.grid_columnconfigure(1, minsize=220, weight=0)
        hdr.grid_columnconfigure(2, minsize=160, weight=0)
        hdr.grid_columnconfigure(3, minsize=110, weight=0)

        for col, txt in enumerate(["Report name", "Created", "Signed", ""]):
            ctk.CTkLabel(
                hdr, text=txt.upper(),
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color=C_MUTED, anchor="w"
            ).grid(row=0, column=col, padx=(4 if col == 0 else 8, 8), pady=6, sticky="w")

        self._reports_scroll = ctk.CTkScrollableFrame(
            outer, fg_color="transparent", corner_radius=0
        )
        self._reports_scroll.grid(row=2, column=0, sticky="nsew", padx=0, pady=0)
        self._reports_scroll.grid_columnconfigure(0, weight=1)

        self._refresh_reports()
        return outer

    def _is_pdf_signed(self, path):
        try:
            with open(path, "rb") as f:
                content = f.read()
            return b"/ByteRange" in content and b"/Contents" in content
        except Exception:
            return False

    def _scan_reports(self):
        reports = []
        if not os.path.isdir(REPORT_DIR):
            return reports
        for fname in sorted(os.listdir(REPORT_DIR), key=lambda f: os.path.getmtime(os.path.join(REPORT_DIR, f)), reverse=True):
            if not fname.lower().endswith(".pdf"):
                continue
            fpath = os.path.join(REPORT_DIR, fname)
            try:
                ctime    = os.path.getmtime(fpath)
                date_str = time.strftime("%d-%m-%y  %H:%M", time.localtime(ctime))
                signed   = self._is_pdf_signed(fpath)
                reports.append((fname, date_str, signed, fpath))
            except Exception:
                pass
        return reports

    def _refresh_reports(self):
        for w in self._reports_scroll.winfo_children():
            w.destroy()
        reports = self._scan_reports()
        if not reports:
            ctk.CTkLabel(
                self._reports_scroll,
                text="No PDF reports found in  " + REPORT_DIR,
                font=ctk.CTkFont(size=12), text_color=C_MUTED
            ).grid(row=0, column=0, pady=40)
            return
        for i, (fname, date_str, signed, fpath) in enumerate(reports):
            bg = C_CARD if i % 2 == 0 else darken(C_CARD, 8)
            row_frame = ctk.CTkFrame(self._reports_scroll, fg_color=bg, corner_radius=6, height=40)
            row_frame.grid(row=i, column=0, sticky="ew", padx=0, pady=2)
            row_frame.grid_propagate(False)
            row_frame.grid_columnconfigure(0, weight=1)
            row_frame.grid_columnconfigure(1, minsize=220, weight=0)
            row_frame.grid_columnconfigure(2, minsize=160, weight=0)
            row_frame.grid_columnconfigure(3, minsize=110, weight=0)

            ctk.CTkLabel(row_frame, text=fname,
                         font=ctk.CTkFont(size=16), text_color=C_TEXT, anchor="w"
                         ).grid(row=0, column=0, padx=(4, 8), sticky="w")
            ctk.CTkLabel(row_frame, text=date_str,
                         font=ctk.CTkFont(size=16, family="Courier New"),
                         text_color=C_LABEL, anchor="w"
                         ).grid(row=0, column=1, padx=8, sticky="w")

            sign_text  = "✅ Signed" if signed else "❌ No"
            sign_color = "#00cc00"  if signed else "#ff1a1a"
            ctk.CTkLabel(row_frame, text=sign_text,
                         font=ctk.CTkFont(size=16), text_color=sign_color, anchor="w"
                         ).grid(row=0, column=2, padx=8, sticky="w")

            btn_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
            btn_frame.grid(row=0, column=3, padx=(4, 8), sticky="e")
            ctk.CTkButton(btn_frame, text="Open", width=60, height=26,
                          fg_color=C_ACTIVE, hover_color=darken(C_ACTIVE, 20),
                          font=ctk.CTkFont(size=11), corner_radius=5,
                          command=lambda p=fpath: self._open_report(p)
                          ).grid(row=0, column=0, padx=(0, 4))
            ctk.CTkButton(btn_frame, text="🗑", width=34, height=26,
                          fg_color=darken(C_DANGER, 10), hover_color=C_DANGER,
                          font=ctk.CTkFont(size=11), corner_radius=5,
                          command=lambda p=fpath, n=fname: self._delete_report(p, n)
                          ).grid(row=0, column=1)

    def _open_report(self, path):
        try:
            if sys.platform.startswith("linux"):
                subprocess.Popen(["xdg-open", path])
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                os.startfile(path)
        except Exception as e:
            self.write_log(f"✗ Cannot open report: {e}")

    def _delete_report(self, path, name):
        try:
            os.remove(path)
            self.write_log(f"🗑 Deleted: {name}")
            self._refresh_reports()
        except Exception as e:
            self.write_log(f"✗ Cannot delete {name}: {e}")

    # ================================================================
    # CARD / FIELD HELPERS
    # ================================================================

    def _card_header(self, parent, text, row):
        ctk.CTkLabel(
            parent, text=text.upper(),
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=C_HEADER, anchor="w"
        ).grid(row=row, column=0, padx=20, pady=(16, 4), sticky="w")
        return row + 1

    def _card(self, parent, row):
        card = ctk.CTkFrame(parent, fg_color=C_CARD, corner_radius=10)
        card.grid(row=row, column=0, padx=16, pady=(0, 4), sticky="ew")
        card.grid_columnconfigure(0, minsize=self.LBL_W)
        card.grid_columnconfigure(1, minsize=self.ENTR_W, weight=1)
        card.grid_columnconfigure(2, minsize=self.LBL_W)
        card.grid_columnconfigure(3, minsize=self.ENTR_W, weight=1)
        return card

    def _field_row(self, card, row, label, key, default, col=0, ph=None, help: str = None):
        lbl = ctk.CTkLabel(
            card,
            text=f"{label} ⓘ" ,
            font=ctk.CTkFont(size=15),
            text_color=C_TEXT ,  # ⓘ zvýrazní celý label
            anchor="w",
            width=self.LBL_W,
            cursor="question_arrow" if help else "arrow",
        )
        lbl.grid(row=row, column=col, padx=(16, 8), pady=10, sticky="w")

        if help:
            CTkToolTip(lbl, message=help, delay=0.3, x_offset=10, y_offset=-10)

        e = ctk.CTkEntry(card, width=self.ENTR_W,
                         placeholder_text=ph or default or "",
                         fg_color=C_ENTRY)
        if default:
            e.insert(0, default)
        e.grid(row=row, column=col + 1, padx=(0, 16), pady=10, sticky="ew")
        self.entries[key] = e
        self._labels[key] = lbl

    def _combo_row(self, card, row, label, key, values, default, col=0, help: str = None):
        lbl = ctk.CTkLabel(
            card,
            text=f"{label} ⓘ",
            font=ctk.CTkFont(size=15),
            text_color=C_TEXT,
            anchor="w",
            width=self.LBL_W,
            cursor="question_arrow" if help else "arrow",
        )
        lbl.grid(row=row, column=col, padx=(16, 8), pady=10, sticky="w")

        if help:
            CTkToolTip(lbl, message=help, delay=0.3, x_offset=10, y_offset=-10)

        cb = ctk.CTkComboBox(
            card, width=self.ENTR_W, values=values,
            fg_color=C_ENTRY,
            button_color=C_ACTIVE,
            button_hover_color=C_HOVER,
            dropdown_fg_color=C_CARD,
            dropdown_hover_color=darken(C_CARD, 15),
            dropdown_text_color=C_TEXT,
        )
        cb.set(default if default in values else (values[0] if values else default))
        cb.grid(row=row, column=col + 1, padx=(0, 16), pady=10, sticky="ew")
        self.entries[key] = cb
        self._labels[key] = lbl

    # ================================================================
    # IP VERSION HELPERS
    # ================================================================

    def _on_ipv6_mode_change(self):
        if self.ipv6_mode.get() == "range":
            self.ipv6_prefix_frame.grid_remove()
            self.ipv6_range_frame.grid()
        else:
            self.ipv6_range_frame.grid_remove()
            self.ipv6_prefix_frame.grid()

    def _active_ip_version(self):
        return "ipv6" if self.ip_tab.get() == "IPv6" else "ipv4"

    def _get_ip_start(self):
        if self._active_ip_version() == "ipv6":
            if self.ipv6_mode.get() == "prefix":
                import ipaddress
                net = ipaddress.IPv6Network(self.entries["ip6_prefix"].get().strip(), strict=False)
                return str(next(net.hosts()))
            return self.entries["ip6_start"].get().strip()
        return self.entries["ip_start"].get().strip()

    def _get_ip_end(self):
        if self._active_ip_version() == "ipv6":
            if self.ipv6_mode.get() == "prefix":
                import ipaddress
                net   = ipaddress.IPv6Network(self.entries["ip6_prefix"].get().strip(), strict=False)
                hosts = list(net.hosts())
                return str(hosts[min(255, len(hosts)-1)])
            return self.entries["ip6_end"].get().strip()
        return self.entries["ip_end"].get().strip()

    def _get_ip_list(self):
        if self._active_ip_version() == "ipv6":
            if self.ipv6_mode.get() == "prefix":
                return ipv6_prefix_to_list(self.entries["ip6_prefix"].get().strip())
            return ipv6_range_to_list(self._get_ip_start(), self._get_ip_end())
        return None

    def _get_target_clean(self):
        return urlparse(self.get("target")).hostname or self.get("target")

    def _get_source_range(self):
        start = self._get_ip_start()
        end   = self._get_ip_end()
        return f"{start} - {end}"  

    # ================================================================
    # GENERIC HELPERS
    # ================================================================

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
                self.statusbar.configure(text=f"●  {msg[:100]}")
        except queue.Empty:
            pass
        finally:
            self.after(100, self._poll_log_queue)

    def clear_log(self):
        self.log.configure(state="normal")
        self.log.delete("0.0", "end")
        self.log.configure(state="disabled")
        self.statusbar.configure(text="●  Log cleared")

    def get(self, key):
        return self.entries[key].get().strip()

    def get_comment(self):
        text = self.comment_text.get("0.0", "end").strip()
        if text == "Write a comment for the report...":
            return ""
        return text

    def _save_port_pool(self):
        port_str  = self.get("src_ports")
        port_file = os.path.join(BASE_DIR, "port_pool.txt")
        if port_str:
            ports = parse_ports(port_str)
            if ports:
                with open(port_file, "w") as f:
                    f.write(port_str)
                self.write_log(f"✓ Port pool saved ({len(ports)} ports)")
            else:
                self.write_log("⚠ Invalid port format")
        else:
            if os.path.exists(port_file):
                os.remove(port_file)
            try:
                with open("/proc/sys/net/ipv4/ip_local_port_range") as f:
                    lo, hi = f.read().split()
                self.write_log(f"ℹ Source ports: OS ephemeral range {lo}–{hi}")
            except Exception:
                self.write_log("ℹ Source ports: OS assigned automatically")

    def _save_test_config(self, script_dir):
        config_file  = os.path.join(script_dir, "test_config.csv")
        target_clean = self._get_target_clean()
        ip_ver       = self._active_ip_version()
        clean        = target_clean.split(":")[0].lstrip("[").split("]")[0]
        try:
            socket.inet_pton(socket.AF_INET6, clean)
            resolved_ip = clean
        except OSError:
            try:
                socket.inet_pton(socket.AF_INET, clean)
                resolved_ip = clean
            except OSError:
                try:
                    af = socket.AF_INET6 if ip_ver == "ipv6" else socket.AF_INET
                    resolved_ip = socket.getaddrinfo(clean, None, af)[0][4][0]
                except Exception:
                    try:
                        resolved_ip = socket.gethostbyname(clean)
                    except Exception:
                        resolved_ip = clean

        src_ip      = self.get("reach_src_ip")    or self._get_ip_start()
        reach_iface = self.get("reach_interface") or self.get("interface")
        # Get Ip pool 
        pool_file  = os.path.join(BASE_DIR, "ip_pool.txt")
        pool_count = 0
        pool_ips   = ""
        if os.path.exists(pool_file):
            with open(pool_file) as f:
                lines = [l.strip() for l in f if l.strip() and not l.startswith("#")]
            pool_count = len(lines)
            pool_ips   = f"{lines[0]} - {lines[-1]}" if lines else ""

        with open(config_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "target", "target_clean", "target_ip", "ip_start", "ip_end",
                "source_range", "ip_pool_count", "ip_pool_range", "src_ports", "ip_version", "interface",
                "processes", "stop_timeout",
                "reach_interval", "reach_timeout", "reach_src_ip", "reach_interface",
                "reach_threshold", "test_type",
            ])
            writer.writeheader()
            writer.writerow({
                "target":           self.get("target"),
                "target_clean":     target_clean,
                "target_ip":        resolved_ip,
                "ip_start":         self._get_ip_start(),
                "ip_end":           self._get_ip_end(),
                "source_range":     self._get_source_range(),
                "ip_pool_count":    pool_count,
                "ip_pool_range":    pool_ips,
                "src_ports":        self.get("src_ports"),
                "ip_version":       ip_ver,
                "interface":        self.get("interface"),
                "reach_interval":   self.get("reach_interval") or "5",
                "reach_timeout":    self.get("reach_timeout") or "5",
                "reach_src_ip":     src_ip,
                "reach_interface":  reach_iface,
                "reach_threshold":  self.get("reach_threshold") or "50",
                "processes":        self.get("processes"),
                "stop_timeout":     self.get("stop_timeout") or "60",
                "test_type":        self.get("test_type"),
            })
        self.write_log(f"✓ Config saved → {target_clean} ({resolved_ip}) [{ip_ver.upper()}]")

    def _load_test_config(self, script_dir):
        config_file = os.path.join(script_dir, "test_config.csv")
        if os.path.exists(config_file):
            try:
                cfg             = pd.read_csv(config_file).iloc[0]
                target_clean    = str(cfg.get("target_clean",    self._get_target_clean()))
                target_ip       = str(cfg.get("target_ip",       target_clean))
                source_range    = str(cfg.get("source_range",    self._get_source_range()))
                ip_pool_count = str(cfg.get("ip_pool_count", ""))
                ip_pool_range = str(cfg.get("ip_pool_range", ""))
                interface       = str(cfg.get("interface",       self.get("interface")))
                reach_src_ip    = str(cfg.get("reach_src_ip", self.get("reach_src_ip")))
                reach_threshold = float(cfg.get("reach_threshold", 50))
                test_type_cfg   = str(cfg.get("test_type",       self.get("test_type")))
                processes       = str(cfg.get("processes",       self.get("processes")))
                stop_timeout    = str(cfg.get("stop_timeout",    self.get("stop_timeout") or "60"))
                self.write_log(f"✓ Params: {target_clean} | {source_range} | threshold={reach_threshold}%")
                return target_clean, target_ip, source_range, interface, reach_threshold, test_type_cfg, processes, stop_timeout, reach_src_ip, ip_pool_count, ip_pool_range
            except Exception as e:
                self.write_log(f"⚠ Error reading config: {e}")
        return (
            self._get_target_clean(),
            self._get_target_clean(),
            self._get_source_range(),
            self.get("interface"),
            float(self.get("reach_threshold") or 50),
            self.get("test_type"),
            self.get("processes"),
            self.get("stop_timeout") or "60",
            self.get("reach_src_ip") or self._get_ip_start(),
        )

    # ================================================================
    # SETUP
    # ================================================================

    def setup_env(self):
        threading.Thread(target=self._setup_thread, daemon=True).start()

    def _setup_thread(self):
        try:
            self.write_log("=" * 60)
            self.write_log("▶ SETUP – Adding IPs to interface...")
            ip_ver     = self._active_ip_version()
            prefix_len = (self.entries["ipv4prefix"].get()
                          if ip_ver == "ipv4"
                          else self.entries["ipv6rangeprefix"].get())
            create_pool(
                ip_start    = self._get_ip_start(),
                ip_end      = self._get_ip_end(),
                interface   = self.get("interface"),
                output_file = os.path.join(BASE_DIR, "ip_pool.txt"),
                ip_version  = ip_ver,
                ip_list     = self._get_ip_list(),
                prefix_len  = prefix_len,
            )
            self.write_log(f"✓ IP pool created [{ip_ver.upper()}]")

            self.write_log("✓ SETUP COMPLETE")
            self.write_log("=" * 60)
        except Exception as e:
            self.write_log(f"✗ Setup error: {e}")

    # ================================================================
    # RUN TEST
    # ================================================================

    def run_test(self):
        self._set_stop_enabled(True)
        threading.Thread(target=self._run_test_thread, daemon=True).start()

    def _set_stop_enabled(self, enabled):
        self._stop_enabled = enabled
        if enabled:
            self.runbtn.configure(
                fg_color="#B7950B",
                hover_color="#B7950B",
                text="⏳ Running...",
                text_color="white",
                state="normal",
                command=lambda: None
            )
            self.stopbtn.configure(
                fg_color=C_DANGER,
                hover_color=darken(C_DANGER, 25),
                text_color="white",
                state="normal",          # ← normal, klikateľný
                command=self.stop_locust # ← správny command
            )
        else:
            self.runbtn.configure(
                fg_color=C_SUCCESS,
                hover_color=darken(C_SUCCESS, 25),
                text="▶ Start Test",
                text_color="white",
                state="normal",
                command=self.run_test
            )
            self.stopbtn.configure(
                fg_color="#3a3a3a",
                hover_color="#3a3a3a",   # ← hover = rovnaká, nech nevyzerá klikateľne
                text_color="#aaaaaa",
                state="normal",
                command=lambda: None     # ← prázdny command keď test nebežím
            )

    def _run_test_thread(self):
        try:
            stages = self._save_stages()

            if not stages:
                self.write_log("✗ No valid stages — check Duration/Users/Spawn rate fields")
                return

            run_time = stages[-1]["duration"]
            interval = int(self.get("reach_interval") or 5)

            self._save_port_pool()
            self._save_env_from_gui()
            self._save_test_config(BASE_DIR)
            self.write_log("=" * 60)

            interface = self.get("monitor_interface") or self.get("interface")
            self._network_monitor = NetworkMonitor(
                interface   = interface,
                interval    = 1,
                output_file = os.path.join(DATA_DIR, "network_usage.csv")
            )
            self._network_monitor.start()
            self.write_log(f"📡 Network monitor started on {interface}")

            self.write_log("▶ Starting Reachability monitoring...")
            reach_thread = threading.Thread(
                target=self._run_reachability, args=(run_time, interval), daemon=True
            )
            reach_thread.start()

            self.write_log("▶ Starting Locust test...")
            self.write_log("-" * 60)
            cmd = ["locust", "-f",self.locustfile_path or os.path.join(BASE_DIR, "locust_tests", 
                "Locustfile_http.py"),
                "--headless",
                "-H",          self.get("target"),
                "--stop-timeout", self.get("stop_timeout") or "60",
                "--processes", self.get("processes"),
                "--csv",       os.path.join(DATA_DIR, "report"),
            ]
            self.write_log(f"CMD: {' '.join(cmd)}")
            self.write_log("-" * 60)

            self.locust_process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1, cwd=BASE_DIR
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
                self.write_log(f"✗ Locust error (code {self.locust_process.returncode})")
            self.write_log("=" * 60)

        except Exception as e:
            self.write_log(f"✗ Test error: {e}")
        finally:
            if self._network_monitor:
                self._network_monitor.stop()
                self._network_monitor = None
                self.write_log("📡 Network monitor stopped")
            self._set_stop_enabled(False)

    def stop_locust(self):
        if not self._stop_enabled:
            return
        if self.locust_process and self.locust_process.poll() is None:
            self.locust_process.terminate()
            self.write_log("⛔ Locust test stopped by user")
            self._reach_stop_event.set()
        self._set_stop_enabled(False)

    def _run_reachability(self, duration, interval):
        self._reach_stop_event.clear()
        run_reachability_check(
            source_ip  = self.get("reach_src_ip") or self._get_ip_start(),
            url        = self.get("target"),
            interval   = interval,
            duration   = duration,
            timeout    = float(self.get("reach_timeout") or 5),
            csv_file   = os.path.join(DATA_DIR, "reachability.csv"),
            stop_event = self._reach_stop_event,
        )

    # ================================================================
    # REPORT
    # ================================================================

    def _generate_report(self):
        threading.Thread(target=self._generate_report_thread, daemon=True).start()

    def _generate_report_thread(self):
        try:
            (target_clean, target_ip, source_range, interface,
             reach_threshold, test_type_cfg, processes, stop_timeout,
             reach_src_ip, ip_pool_count, ip_pool_range) = self._load_test_config(BASE_DIR)

            report_name = self._report_name_entry.get().strip() or "Locust_Report"
            if not report_name.endswith(".pdf"):
                report_name += ".pdf"
            save_dir = self._report_dir_entry.get().strip() or REPORT_DIR
            os.makedirs(save_dir, exist_ok=True)
            pdf_path = os.path.join(save_dir, report_name)
            sign     = self._sign_var.get()
            p12_path = self._cert_path_entry.get().strip() if sign else ""
            p12_pass = self.cert_pass.get().strip().encode() if sign else b""

            self.write_log("=" * 60)
            self.write_log("▶ Generating PDF report...")
            create_pdf_report(
                stats_file      = os.path.join(DATA_DIR, "report_stats.csv"),
                history_file    = os.path.join(DATA_DIR, "report_stats_history.csv"),
                output_file     = pdf_path,
                meta_file       = os.path.join(DATA_DIR, "report_metadata.csv"),
                network_file    = os.path.join(DATA_DIR, "network_usage.csv"),
                comment         = self.get_comment(),
                target_ip       = target_ip,
                source_ip       = source_range,
                ip_pool_count = ip_pool_count,
                ip_pool_range = ip_pool_range,
                interface       = interface,
                reach_threshold = reach_threshold / 100,
                test_type       = test_type_cfg,
                src_ports       = self.get("src_ports") or None,
                reach_src_ip    = self.get("reach_src_ip") or self._get_ip_start(),
                sign            = sign,
                p12_path        = p12_path,
                p12_pass        = p12_pass,
            )
            self.write_log(f"✓ {report_name} generated → {save_dir}")
            self.write_log("=" * 60)
            if sys.platform.startswith("linux"):
                subprocess.Popen(["xdg-open", pdf_path])
            elif sys.platform == "darwin":
                subprocess.Popen(["open", pdf_path])
            else:
                os.startfile(pdf_path)
        except Exception as e:
            self.write_log(f"✗ Report error: {e}")

    # ================================================================
    # CLEANUP
    # ================================================================

    def cleanup(self):
        threading.Thread(target=self._cleanup_thread, daemon=True).start()

    def _cleanup_thread(self):
        try:
            self.write_log("=" * 60)
            self.write_log("▶ Removing IP pool from interface...")
            ip_ver     = self._active_ip_version()
            prefix_len = (self.entries["ipv4prefix"].get()
                          if ip_ver == "ipv4"
                          else self.entries["ipv6rangeprefix"].get())
            remove_pool(
                ip_start   = self._get_ip_start(),
                ip_end     = self._get_ip_end(),
                interface  = self.get("interface"),
                pool_file  = os.path.join(BASE_DIR, "ip_pool.txt"),
                ip_version = ip_ver,
                ip_list    = self._get_ip_list(),
                prefix_len = prefix_len,
            )
            self.write_log("✓ Cleanup complete")
            self.write_log("=" * 60)
        except Exception as e:
            self.write_log(f"✗ Cleanup error: {e}")


if __name__ == "__main__":
    app = LocustGUI()
    app.mainloop()
