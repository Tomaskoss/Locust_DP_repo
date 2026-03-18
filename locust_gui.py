#!/usr/bin/env python3
import tkinter as tk
import tkinter.filedialog as fd
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
from dotenv import load_dotenv, set_key

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "network"))
sys.path.insert(0, os.path.join(BASE_DIR, "report"))

load_dotenv(dotenv_path=os.path.join(BASE_DIR, "config.env"), override=True)

from Create_topology        import create_topology_diagram
from Locust_report_v3       import create_pdf_report
from Create_IP_Pool_skript  import main as create_pool
from Remove_IP_Pool_skript  import main as remove_pool
from Network_monitor        import NetworkMonitor

DATA_DIR   = os.path.join(BASE_DIR, "data")
REPORT_DIR = os.path.join(BASE_DIR, "report")

# ── Themes ─────────────────────────────────────────────────────────
THEMES = {
    "Dark Blue": {
        "SIDEBAR":  "#1a1a2e",
        "CONTENT":  "#16213e",
        "CARD":     "#1f2b47",
        "ACTIVE":   "#85b832",
        "HOVER":    "#1558A8",
        "TEXT":     "#e0e0e0",
        "MUTED":    "#7a8899",
        "LABEL":    "#c5cfe0",
        "HEADER":   "#85b832",
        "ENTRY":    "#263550",
        "DANGER":   "#922b21",
        "SUCCESS":  "#85b832",
        "PURPLE":   "#7D3C98",
        "BLUE":     "#2a5f3a",
    },
    "Dark Green": {
        "SIDEBAR":  "#0d1f0d",
        "CONTENT":  "#111a11",
        "CARD":     "#1a2e1a",
        "ACTIVE":   "#4caf50",
        "HOVER":    "#388e3c",
        "TEXT":     "#e0e0e0",
        "MUTED":    "#6a8f6a",
        "LABEL":    "#b8d4b8",
        "HEADER":   "#4caf50",
        "ENTRY":    "#1e351e",
        "DANGER":   "#C0392B",
        "SUCCESS":  "#2e7d32",
        "PURPLE":   "#7D3C98",
        "BLUE":     "#1565c0",
    },
    "Dark Red": {
        "SIDEBAR":  "#1a0a0a",
        "CONTENT":  "#1a1010",
        "CARD":     "#2b1515",
        "ACTIVE":   "#e53935",
        "HOVER":    "#b71c1c",
        "TEXT":     "#e0e0e0",
        "MUTED":    "#8f6060",
        "LABEL":    "#d4b8b8",
        "HEADER":   "#e53935",
        "ENTRY":    "#3a1a1a",
        "DANGER":   "#C0392B",
        "SUCCESS":  "#1E8449",
        "PURPLE":   "#7D3C98",
        "BLUE":     "#2471A3",
    },
    "Locust Dark": {
    "SIDEBAR":  "#0a0a0a",
    "CONTENT":  "#111111",
    "CARD":     "#1a1a1a",
    "ACTIVE":   "#2a5f3a",   
    "HOVER":    "#1e4a2c",   
    "TEXT":     "#ffffff",
    "MUTED":    "#888888",
    "LABEL":    "#cccccc",
    "HEADER":   "#2a5f3a",   
    "ENTRY":    "#242424",
    "DANGER":   "#922b21",
    "SUCCESS":  "#2a5f3a",   
    "PURPLE":   "#7D3C98",
    "BLUE":     "#2a5f3a",
    },
}

def apply_theme(name):
    global C_SIDEBAR, C_CONTENT, C_CARD, C_ACTIVE, C_HOVER
    global C_TEXT, C_MUTED, C_LABEL, C_HEADER, C_ENTRY
    global C_DANGER, C_SUCCESS, C_PURPLE, C_BLUE
    t = THEMES[name]
    C_SIDEBAR = t["SIDEBAR"]; C_CONTENT = t["CONTENT"]
    C_CARD    = t["CARD"];    C_ACTIVE  = t["ACTIVE"]
    C_HOVER   = t["HOVER"];   C_TEXT    = t["TEXT"]
    C_MUTED   = t["MUTED"];   C_LABEL   = t["LABEL"]
    C_HEADER  = t["HEADER"];  C_ENTRY   = t["ENTRY"]
    C_DANGER  = t["DANGER"];  C_SUCCESS = t["SUCCESS"]
    C_PURPLE  = t["PURPLE"];  C_BLUE    = t["BLUE"]

apply_theme("Locust Dark")

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

# ============================================================
#  network bar
# ============================================================
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
        ("🌐", "HTTP"),
        ("📄", "Generate Report"),
        ("📋", "Reports"),
    ]

    LBL_W  = 160
    ENTR_W = 220

    def __init__(self, initial_theme="Locust Dark"):
        super().__init__()
        apply_theme(initial_theme)
        self._current_theme = initial_theme
        self._network_monitor = None

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
        self._active_page    = None
        self._nav_buttons    = {}
        self._pages          = {}
        self._zoom           = 1.0

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
            "test_type":       os.getenv("TEST_TYPE"),
            "ip_start":        os.getenv("IP_START"),
            "ip_end":          os.getenv("IP_END"),
            "ip6_start":       os.getenv("IP6_START"),
            "ip6_end":         os.getenv("IP6_END"),
            "ip6_prefix":      os.getenv("IP6_PREFIX"),
            "users":           os.getenv("USERS"),
            "run_time":        os.getenv("RUN_TIME"),
            "spawn_rate":      os.getenv("SPAWN_RATE"),
            "processes":       os.getenv("PROCESSES"),
            "reach_interval":  os.getenv("REACH_INTERVAL"),
            "reach_timeout":   os.getenv("REACH_TIMEOUT"),
            "reach_src_ip":    os.getenv("REACH_SRC_IP", ""),
            "reach_interface": os.getenv("REACH_INTERFACE", ""),
            "reach_threshold": os.getenv("REACH_THRESHOLD"),
        }
        for key, value in mapping.items():
            if value and key in self.entries:
                widget = self.entries[key]
                if isinstance(widget, ctk.CTkComboBox):
                    widget.set(value)
                else:
                    widget.delete(0, "end")
                    widget.insert(0, value)

    def _save_env_from_gui(self):
        env_path = os.path.join(BASE_DIR, "config.env")
        mapping = {
            "TARGET_HOST":     self.get("target"),
            "INTERFACE":       self.get("interface"),
            "TEST_TYPE":       self.get("test_type"),
            "IP_VERSION":      self._active_ip_version(),
            "IP_START":        self._get_ip_start(),
            "IP_END":          self._get_ip_end(),
            "IP6_START":       self.entries["ip6_start"].get().strip(),
            "IP6_END":         self.entries["ip6_end"].get().strip(),
            "IP6_PREFIX":      self.entries["ip6_prefix"].get().strip(),
            "IPV6_MODE":       self.ipv6_mode.get(),
            "USERS":           self.get("users"),
            "RUN_TIME":        self.get("run_time"),
            "SPAWN_RATE":      self.get("spawn_rate"),
            "PROCESSES":       self.get("processes"),
            "REACH_INTERVAL":  self.get("reach_interval"),
            "REACH_TIMEOUT":   self.get("reach_timeout"),
            "REACH_SRC_IP":    self.get("reach_src_ip"),
            "REACH_INTERFACE": self.get("reach_interface"),
            "REACH_THRESHOLD": self.get("reach_threshold"),
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
    # SCROLL KOLECKO
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
        self._theme_combo.grid(row=10, column=0, padx=15, pady=(0, 8))

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
        self._paned.add(self.main,        minsize=300, stretch="always")
        self._paned.add(self._logframe,   minsize=80,  stretch="never")

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

        self._pages["Config"] = self._build_page_config(self.page_container)
        self._pages["HTTP"]   = self._build_page_http(self.page_container)
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
        log_height = 200  # ← nastav podľa želanej výšky logu
        self._paned.sash_place(0, 0, total - log_height)
        


    # ================================================================
    # PAGE – CONFIG
    # ================================================================

    def _build_page_config(self, parent):
        scroll = make_scroll_frame(parent)
        scroll.grid(row=0, column=0, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)

        row = 0

        row = self._card_header(scroll, "General", row)
        card = self._card(scroll, row); row += 1
        self._field_row(card, 0, "Target host",  "target",     "https://google.sk")
        ifaces = get_network_interfaces()
        self._combo_row(card, 1, "Interface", "interface", ifaces,
                os.getenv("INTERFACE", ifaces[0] if ifaces else "ens33"))
        self._field_row(card, 0, "Test type",    "test_type",  "Load Test",  col=2)
        self._field_row(card, 1, "Source ports", "src_ports",  "",           col=2,
                        ph="e.g. 1024-65535")

        row = self._card_header(scroll, "IP Pool", row)
        card2 = self._card(scroll, row); row += 1

        self.ip_tab = ctk.CTkTabview(card2, height=110, fg_color=C_CARD,
                                     segmented_button_fg_color=darken(C_CARD),
                                     segmented_button_selected_color=C_ACTIVE)
        self.ip_tab.grid(row=0, column=0, columnspan=4, padx=12, pady=8, sticky="ew")
        self.ip_tab.add("IPv4")
        self.ip_tab.add("IPv6")

        v4 = self.ip_tab.tab("IPv4")
        v4.grid_columnconfigure(0, minsize=self.LBL_W)
        v4.grid_columnconfigure(1, weight=1)
        for i, (lbl, key, default) in enumerate([
            ("IP range start", "ip_start", "192.168.10.10"),
            ("IP range end",   "ip_end",   "192.168.10.40"),
        ]):
            ctk.CTkLabel(v4, text=lbl, font=ctk.CTkFont(size=12),
                         text_color=C_LABEL, anchor="w", width=self.LBL_W
                         ).grid(row=i, column=0, padx=(16,8), pady=6, sticky="w")
            e = ctk.CTkEntry(v4, fg_color=C_ENTRY)
            e.insert(0, default)
            e.grid(row=i, column=1, padx=(0,16), pady=6, sticky="ew")
            self.entries[key] = e

        v6 = self.ip_tab.tab("IPv6")
        v6.grid_columnconfigure(1, weight=1)
        v6.grid_columnconfigure(3, weight=1)
        self.ipv6_mode = ctk.StringVar(value="range")
        mf = ctk.CTkFrame(v6, fg_color="transparent")
        mf.grid(row=0, column=0, columnspan=4, sticky="w", padx=8, pady=(4,2))
        ctk.CTkLabel(mf, text="Mode:", font=ctk.CTkFont(size=11),
                     text_color=C_MUTED).pack(side="left", padx=(0,8))
        for val, txt in [("range","Range"),("prefix","Prefix")]:
            ctk.CTkRadioButton(mf, text=txt, variable=self.ipv6_mode, value=val,
                       command=self._on_ipv6_mode_change,
                       font=ctk.CTkFont(size=11),
                       fg_color=C_ACTIVE,
                       hover_color=C_HOVER,
                       border_color=C_MUTED
                       ).pack(side="left", padx=4)

        self.ipv6_range_frame = ctk.CTkFrame(v6, fg_color="transparent")
        self.ipv6_range_frame.grid(row=1, column=0, columnspan=4, sticky="ew")
        self.ipv6_range_frame.grid_columnconfigure(0, minsize=self.LBL_W)
        self.ipv6_range_frame.grid_columnconfigure(1, weight=1)
        for i, (lbl, key, dflt) in enumerate([("IPv6 start","ip6_start","fd00::10"),
                                               ("IPv6 end","ip6_end","fd00::40")]):
            ctk.CTkLabel(self.ipv6_range_frame, text=lbl, font=ctk.CTkFont(size=11),
                         text_color=C_LABEL, anchor="w", width=self.LBL_W
                         ).grid(row=i, column=0, padx=(16,8), pady=4, sticky="w")
            e = ctk.CTkEntry(self.ipv6_range_frame, fg_color=C_ENTRY)
            e.insert(0, dflt)
            e.grid(row=i, column=1, padx=(0,16), pady=4, sticky="ew")
            self.entries[key] = e

        self.ipv6_prefix_frame = ctk.CTkFrame(v6, fg_color="transparent")
        self.ipv6_prefix_frame.grid(row=1, column=0, columnspan=4, sticky="ew")
        self.ipv6_prefix_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(self.ipv6_prefix_frame, text="IPv6 prefix", font=ctk.CTkFont(size=11),
                     text_color=C_LABEL, anchor="w").grid(row=0, column=0, padx=(16,8), pady=4, sticky="w")
        e = ctk.CTkEntry(self.ipv6_prefix_frame, width=self.ENTR_W, fg_color=C_ENTRY)
        e.insert(0, "fd00::/64")
        e.grid(row=0, column=1, padx=(0,12), pady=4, sticky="ew")
        self.entries["ip6_prefix"] = e
        self.ipv6_prefix_frame.grid_remove()

        row = self._card_header(scroll, "Reachability", row)
        card3 = self._card(scroll, row); row += 1
        self._field_row(card3, 0, "Interval (s)",         "reach_interval", "5")
        self._field_row(card3, 1, "Timeout (s)",           "reach_timeout",  "5")
        self._field_row(card3, 0, "Source IP",             "reach_src_ip",    "",  col=2, ph="= IP range start")
        self._combo_row(card3, 1, "Interface", "reach_interface",[""] + get_network_interfaces(), "",  col=2)
        self._field_row(card3, 2, "Failure threshold (%)", "reach_threshold", "50", col=0)
        
        
        row = self._card_header(scroll, "Network Monitor", row)
        card_mon = self._card(scroll, row); row += 1

        ifaces = get_network_interfaces()
        self._combo_row(
            card_mon, 0,
            "Interface",
            "monitor_interface",
            ifaces,
            os.getenv("INTERFACE", ifaces[0] if ifaces else "ens33")
            )

        row = self._card_header(scroll, "Actions", row)
        bf = ctk.CTkFrame(scroll, fg_color="transparent")
        bf.grid(row=row, column=0, padx=16, pady=(4,16), sticky="ew")
        bf.grid_columnconfigure((0,1), weight=1)
        row += 1
        
        

        for col, (icon, label, sub, cmd, color) in enumerate([
            ("⚙", "Setup", "IP Pool + Topology",  self.setup_env, C_BLUE),
            ("🗑", "Cleanup", "Remove IP Pool",    self.cleanup,   C_DANGER),
        ]):
            card_btn = ctk.CTkFrame(bf, fg_color=color, corner_radius=10, cursor="hand2")
            card_btn.grid(row=0, column=col, padx=(0 if col==0 else 8, 8 if col==0 else 0),
                          pady=4, sticky="ew")
            card_btn.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(card_btn, text=icon, font=ctk.CTkFont(size=26),
                         fg_color="transparent", text_color="white", cursor="hand2"
                         ).grid(row=0, column=0, rowspan=2, padx=(14,8), pady=12, sticky="w")
            ctk.CTkLabel(card_btn, text=label,
                         font=ctk.CTkFont(size=13, weight="bold"),
                         fg_color="transparent", text_color="white", anchor="w", cursor="hand2"
                         ).grid(row=0, column=1, padx=(0,12), pady=(10,0), sticky="w")
            ctk.CTkLabel(card_btn, text=sub,
                         font=ctk.CTkFont(size=10),
                         fg_color="transparent", text_color="#b0b8c8", anchor="w", cursor="hand2"
                         ).grid(row=1, column=1, padx=(0,12), pady=(0,10), sticky="w")

            self.after(50, lambda cb=card_btn, c=cmd, cl=color: bind_card(cb, c, darken(cl, 25), cl))

        return scroll

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
        s_row = self._card_header(scroll, "Locust Parameters", s_row)
        card = self._card(scroll, s_row); s_row += 1
        self._field_row(card, 0, "Users",        "users",      "1")
        self._field_row(card, 1, "Run time (s)", "run_time",   "20")
        self._field_row(card, 0, "Spawn rate",   "spawn_rate", "1",  col=2)
        self._field_row(card, 1, "Processes",    "processes",  "-1", col=2)

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

        bottom = ctk.CTkFrame(outer, fg_color="transparent")
        bottom.grid(row=1, column=0, sticky="ew")
        bottom.grid_columnconfigure(0, weight=1)

        self._card_header(bottom, "Actions", 0)
        bf = ctk.CTkFrame(bottom, fg_color="transparent")
        bf.grid(row=1, column=0, padx=16, pady=(4,16), sticky="ew")
        bf.grid_columnconfigure((0, 1), weight=1)

        run_card = ctk.CTkFrame(bf, fg_color=C_SUCCESS, corner_radius=10, cursor="hand2")
        run_card.grid(row=0, column=0, padx=(0,8), pady=4, sticky="ew")
        run_card.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(run_card, text="▶", font=ctk.CTkFont(size=28),
                     fg_color="transparent", text_color="white", cursor="hand2"
                     ).grid(row=0, column=0, rowspan=2, padx=(14,8), pady=12)
        ctk.CTkLabel(run_card, text="Start Test",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     fg_color="transparent", text_color="white", anchor="w", cursor="hand2"
                     ).grid(row=0, column=1, padx=(0,12), pady=(10,0), sticky="w")
        ctk.CTkLabel(run_card, text="Locust + Reachability",
                     font=ctk.CTkFont(size=10),
                     fg_color="transparent", text_color="#b0b8c8", anchor="w", cursor="hand2"
                     ).grid(row=1, column=1, padx=(0,12), pady=(0,10), sticky="w")
        self._run_card = run_card
        self.after(50, lambda: bind_card(run_card, self.run_test, darken(C_SUCCESS, 25), C_SUCCESS))

        stop_card = ctk.CTkFrame(bf, fg_color="#3a3a3a", corner_radius=10, cursor="arrow")
        stop_card.grid(row=0, column=1, padx=(8,0), pady=4, sticky="ew")
        stop_card.grid_columnconfigure(1, weight=1)
        self._stop_icon_lbl = ctk.CTkLabel(stop_card, text="⛔", font=ctk.CTkFont(size=24),
                     fg_color="transparent", text_color="#aaaaaa")
        self._stop_icon_lbl.grid(row=0, column=0, rowspan=2, padx=(14,8), pady=12)
        self._stop_title_lbl = ctk.CTkLabel(stop_card, text="Stop Test",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     fg_color="transparent", text_color="#aaaaaa", anchor="w")
        self._stop_title_lbl.grid(row=0, column=1, padx=(0,12), pady=(10,0), sticky="w")
        self._stop_sub_lbl = ctk.CTkLabel(stop_card, text="Terminate Locust process",
                     font=ctk.CTkFont(size=10),
                     fg_color="transparent", text_color="#666666", anchor="w")
        self._stop_sub_lbl.grid(row=1, column=1, padx=(0,12), pady=(0,10), sticky="w")
        self._stop_card = stop_card
        self._stop_enabled = False

        return outer

    # ================================================================
    # PAGE – REPORT
    # ================================================================

    def _build_page_report(self, parent):
        outer = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        outer.grid(row=0, column=0, sticky="nsew")
        outer.grid_columnconfigure(0, weight=1)
        outer.grid_rowconfigure(0, weight=1)
        outer.grid_rowconfigure(1, weight=0)

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
        self.comment_text.grid(row=t_row, column=0, padx=16, pady=(4,12), sticky="ew")
        self.comment_text.insert("0.0", "Write a comment for the report...")
        t_row += 1

        t_row = self._card_header(scroll, "Output", t_row)
        card_out = ctk.CTkFrame(scroll, fg_color=C_CARD, corner_radius=10)
        card_out.grid(row=t_row, column=0, padx=16, pady=(0,4), sticky="ew")
        card_out.grid_columnconfigure(1, weight=1)
        t_row += 1

        ctk.CTkLabel(card_out, text="Report name", font=ctk.CTkFont(size=15),
                     text_color=C_LABEL, anchor="w", width=self.LBL_W
                     ).grid(row=0, column=0, padx=(16,8), pady=10, sticky="w")
        self._report_name_entry = ctk.CTkEntry(card_out, fg_color=C_ENTRY,
                                               placeholder_text="Locust_Report")
        self._report_name_entry.insert(0, "Locust_Report")
        self._report_name_entry.grid(row=0, column=1, columnspan=2, padx=(0,16), pady=10, sticky="ew")

        ctk.CTkLabel(card_out, text="Save to", font=ctk.CTkFont(size=15),
                     text_color=C_LABEL, anchor="w", width=self.LBL_W
                     ).grid(row=1, column=0, padx=(16,8), pady=10, sticky="w")
        self._report_dir_entry = ctk.CTkEntry(card_out, fg_color=C_ENTRY,
                                              placeholder_text=REPORT_DIR)
        self._report_dir_entry.insert(0, REPORT_DIR)
        self._report_dir_entry.grid(row=1, column=1, padx=(0,8), pady=10, sticky="ew")
        ctk.CTkButton(card_out, text="Browse", width=80,
                      fg_color=C_ENTRY, hover_color=C_HOVER,
                      font=ctk.CTkFont(size=12), corner_radius=6,
                      command=self._browse_save_dir
                      ).grid(row=1, column=2, padx=(0,16), pady=10)

        t_row = self._card_header(scroll, "PDF Signing", t_row)
        card_sign = ctk.CTkFrame(scroll, fg_color=C_CARD, corner_radius=10)
        card_sign.grid(row=t_row, column=0, padx=16, pady=(0,4), sticky="ew")
        card_sign.grid_columnconfigure(1, weight=1)
        t_row += 1

        self._sign_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(card_sign, text="Sign PDF", variable=self._sign_var,
                        font=ctk.CTkFont(size=12), text_color=C_TEXT,
                        command=self._on_sign_toggle
                        ).grid(row=0, column=0, columnspan=3, padx=16, pady=(12,8), sticky="w")

        self._cert_sign_frame = ctk.CTkFrame(card_sign, fg_color="transparent")
        self._cert_sign_frame.grid(row=1, column=0, columnspan=3, sticky="ew")
        self._cert_sign_frame.grid_columnconfigure(1, weight=1)
        self._cert_sign_frame.grid_remove()

        ctk.CTkLabel(self._cert_sign_frame, text="Certificate", font=ctk.CTkFont(size=15),
                     text_color=C_LABEL, anchor="w", width=self.LBL_W
                     ).grid(row=0, column=0, padx=(16,8), pady=8, sticky="w")
        self._cert_path_entry = ctk.CTkEntry(self._cert_sign_frame, fg_color=C_ENTRY,
                                             placeholder_text="Path to cert.p12")
        default_cert = os.path.join(REPORT_DIR, "cert.p12")
        if os.path.exists(default_cert):
            self._cert_path_entry.insert(0, default_cert)
        self._cert_path_entry.grid(row=0, column=1, padx=(0,8), pady=8, sticky="ew")
        ctk.CTkButton(self._cert_sign_frame, text="Browse", width=80,
                      fg_color=C_ENTRY, hover_color=C_HOVER,
                      font=ctk.CTkFont(size=12), corner_radius=6,
                      command=self._browse_cert
                      ).grid(row=0, column=2, padx=(0,16), pady=8)

        ctk.CTkLabel(self._cert_sign_frame, text="Password", font=ctk.CTkFont(size=15),
                     text_color=C_LABEL, anchor="w", width=self.LBL_W
                     ).grid(row=1, column=0, padx=(16,8), pady=(0,12), sticky="w")
        self.cert_pass = ctk.CTkEntry(self._cert_sign_frame, show="•",
                                      placeholder_text="Password for cert.p12",
                                      fg_color=C_ENTRY)
        self.cert_pass.grid(row=1, column=1, columnspan=2, padx=(0,16), pady=(0,12), sticky="ew")

        gen_card = ctk.CTkFrame(outer, fg_color=C_PURPLE, corner_radius=10, cursor="hand2")
        gen_card.grid(row=1, column=0, padx=16, pady=(12,16), sticky="ew")
        gen_card.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(gen_card, text="📄", font=ctk.CTkFont(size=26),
                     fg_color="transparent", text_color="white", cursor="hand2"
                     ).grid(row=0, column=0, rowspan=2, padx=(14,8), pady=12, sticky="w")
        ctk.CTkLabel(gen_card, text="Generate Report",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     fg_color="transparent", text_color="white", anchor="w", cursor="hand2"
                     ).grid(row=0, column=1, padx=(0,12), pady=(10,0), sticky="w")
        ctk.CTkLabel(gen_card, text="Export results to PDF",
                     font=ctk.CTkFont(size=10),
                     fg_color="transparent", text_color="#b0b8c8", anchor="w", cursor="hand2"
                     ).grid(row=1, column=1, padx=(0,12), pady=(0,10), sticky="w")
        self.after(50, lambda: bind_card(gen_card, self.generate_report, darken(C_PURPLE, 25), C_PURPLE))

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
            self._locustfile_label.configure(
                text=os.path.basename(path),
                text_color=C_TEXT
            )
            self.write_log(f"✓ Locustfile: {os.path.basename(path)}")

    def _clear_locustfile(self):
        self.locustfile_path = None
        self._locustfile_label.configure(
            text="default: Locustfile_http.py",
            text_color=C_MUTED
        )
        self.write_log("↩ Locustfile reset to default")

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

        # logframe vytvoríme teraz, do panedwindow pridáme neskôr v _build_main
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
        outer.grid_rowconfigure(2, weight=1)

        # ── Toolbar ────────────────────────────────────────────
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

        # ── Hlavička tabuľky ───────────────────────────────────
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
            ).grid(row=0, column=col,
                   padx=(4 if col == 0 else 8, 8), pady=6, sticky="w")

        # ── Scroll area pre riadky ─────────────────────────────
        self._reports_scroll = ctk.CTkScrollableFrame(
            outer, fg_color="transparent", corner_radius=0
        )
        self._reports_scroll.grid(row=2, column=0, sticky="nsew", padx=0, pady=0)
        self._reports_scroll.grid_columnconfigure(0, weight=1)

        self._refresh_reports()
        return outer

    # ── Helpery pre Reports ────────────────────────────────────────────

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
        for fname in sorted(os.listdir(REPORT_DIR), reverse=True):
            if not fname.lower().endswith(".pdf"):
                continue
            fpath = os.path.join(REPORT_DIR, fname)
            try:
                ctime = os.path.getmtime(fpath)
                date_str = time.strftime("%d-%m-%y  %H:%M", time.localtime(ctime))
                signed = self._is_pdf_signed(fpath)
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
                font=ctk.CTkFont(size=12),
                text_color=C_MUTED
            ).grid(row=0, column=0, pady=40)
            return

        for i, (fname, date_str, signed, fpath) in enumerate(reports):
            bg = C_CARD if i % 2 == 0 else darken(C_CARD, 8)
            row_frame = ctk.CTkFrame(
                self._reports_scroll, fg_color=bg, corner_radius=6, height=40
            )
            row_frame.grid(row=i, column=0, sticky="ew", padx=0, pady=2)            
            row_frame.grid_propagate(False)
            row_frame.grid_columnconfigure(0, weight=1)
            row_frame.grid_columnconfigure(1, minsize=220, weight=0)
            row_frame.grid_columnconfigure(2, minsize=160, weight=0)
            row_frame.grid_columnconfigure(3, minsize=110, weight=0)

            # Názov
            ctk.CTkLabel(
                row_frame, text=fname,
                font=ctk.CTkFont(size=16), text_color=C_TEXT, anchor="w"
            ).grid(row=0, column=0, padx=(4, 8), sticky="w")

            # Dátum
            ctk.CTkLabel(
                row_frame, text=date_str,
                font=ctk.CTkFont(size=16, family="Courier New"),
                text_color=C_LABEL, anchor="w"
            ).grid(row=0, column=1, padx=8, sticky="w")

            # Podpis
            sign_text  = "✅ Signed" if signed else "❌ No"
            sign_color = C_SUCCESS  if signed else C_MUTED
            ctk.CTkLabel(
                row_frame, text=sign_text,
                font=ctk.CTkFont(size=16), text_color=sign_color, anchor="w"
            ).grid(row=0, column=2, padx=8, sticky="w")

            # Tlačidlá
            btn_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
            btn_frame.grid(row=0, column=3, padx=(4, 8), sticky="e")

            ctk.CTkButton(
                btn_frame, text="Open", width=60, height=26,
                fg_color=C_ACTIVE, hover_color=darken(C_ACTIVE, 20),
                font=ctk.CTkFont(size=11), corner_radius=5,
                command=lambda p=fpath: self._open_report(p)
            ).grid(row=0, column=0, padx=(0, 4))

            ctk.CTkButton(
                btn_frame, text="🗑", width=34, height=26,
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

    def _field_row(self, card, row, label, key, default, col=0, ph=None):
        ctk.CTkLabel(card, text=label, font=ctk.CTkFont(size=15),
                     text_color=C_LABEL, anchor="w", width=self.LBL_W
                     ).grid(row=row, column=col, padx=(16, 8), pady=10, sticky="w")
        e = ctk.CTkEntry(card, width=self.ENTR_W,
                         placeholder_text=ph or default or "",
                         fg_color=C_ENTRY)
        if default:
            e.insert(0, default)
        e.grid(row=row, column=col+1, padx=(0, 16), pady=10, sticky="ew")
        self.entries[key] = e

    def _combo_row(self, card, row, label, key, values, default, col=0):
        ctk.CTkLabel(card, text=label, font=ctk.CTkFont(size=15),
                     text_color=C_LABEL, anchor="w", width=self.LBL_W
                     ).grid(row=row, column=col, padx=(16, 8), pady=10, sticky="w")
        cb = ctk.CTkComboBox(card, width=self.ENTR_W, values=values,
                             fg_color=C_ENTRY,
                             button_color=C_ACTIVE,
                             button_hover_color=C_HOVER,
                             dropdown_fg_color=C_CARD,
                             dropdown_hover_color=darken(C_CARD, 15),
                             dropdown_text_color=C_TEXT)
        cb.set(default if default in values else (values[0] if values else default))
        cb.grid(row=row, column=col+1, padx=(0, 16), pady=10, sticky="ew")
        self.entries[key] = cb

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
        return (self.get("target").replace("https://","").replace("http://","").split("/")[0])

    def _get_source_range(self):
        start = self._get_ip_start()
        end   = self._get_ip_end()
        if self._active_ip_version() == "ipv6":
            return f"{start} - {end}"
        return f"{start}-{end.split('.')[-1]}"

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

        with open(config_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "target","target_clean","target_ip","ip_start","ip_end","source_range",
                "src_ports","ip_version","interface","users","run_time",
                "reach_timeout","reach_src_ip","reach_interface","reach_threshold","test_type",
            ])
            writer.writeheader()
            writer.writerow({
                "target": self.get("target"), "target_clean": target_clean,
                "target_ip": resolved_ip, "ip_start": self._get_ip_start(),
                "ip_end": self._get_ip_end(), "source_range": self._get_source_range(),
                "src_ports": self.get("src_ports"), "ip_version": ip_ver,
                "interface": self.get("interface"), "users": self.get("users"),
                "run_time": self.get("run_time"),
                "reach_timeout": self.get("reach_timeout") or "5",
                "reach_src_ip": src_ip, "reach_interface": reach_iface,
                "reach_threshold": self.get("reach_threshold") or "50",
                "test_type": self.get("test_type"),
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
                interface       = str(cfg.get("interface",       self.get("interface")))
                reach_threshold = float(cfg.get("reach_threshold", 50))
                test_type_cfg   = str(cfg.get("test_type",       self.get("test_type")))
                self.write_log(f"✓ Params: {target_clean} | {source_range} | threshold={reach_threshold}%")
                return target_clean, target_ip, source_range, interface, reach_threshold, test_type_cfg
            except Exception as e:
                self.write_log(f"⚠ Error reading config: {e}")
        return (self._get_target_clean(), self._get_target_clean(), self._get_source_range(),
                self.get("interface"), float(self.get("reach_threshold") or 50), self.get("test_type"))

    # ================================================================
    # SETUP
    # ================================================================

    def setup_env(self):
        threading.Thread(target=self._setup_thread, daemon=True).start()

    def _setup_thread(self):
        try:
            self.write_log("=" * 60)
            self.write_log("▶ SETUP – Adding IPs to interface...")
            ip_ver = self._active_ip_version()
            create_pool(ip_start=self._get_ip_start(), ip_end=self._get_ip_end(),
                        interface=self.get("interface"),
                        output_file=os.path.join(BASE_DIR, "ip_pool.txt"),
                        ip_version=ip_ver, ip_list=self._get_ip_list())
            self.write_log(f"✓ IP pool created [{ip_ver.upper()}]")
            self.write_log("▶ Generating topology diagram...")
            create_topology_diagram(target_ip=self._get_target_clean(),
                                    source_ip=self._get_source_range(),
                                    interface=self.get("interface"),
                                    output_file=os.path.join(REPORT_DIR, "topology_diagram.png"))
            self.write_log("✓ Topology diagram generated")
            self.write_log("✓ SETUP COMPLETE")
            self.write_log("=" * 60)
        except Exception as e:
            self.write_log(f"✗ Setup error: {e}")

    # ================================================================
    # RUN TEST
    # ================================================================

    def run_test(self):
        self._run_card.configure(fg_color=darken(C_SUCCESS, 30), cursor="arrow")
        self._set_stop_enabled(True)
        threading.Thread(target=self._run_test_thread, daemon=True).start()

    def _set_stop_enabled(self, enabled):
        self._stop_enabled = enabled
        if enabled:
            self._stop_card.configure(fg_color=C_DANGER, cursor="hand2")
            self._stop_icon_lbl.configure(text_color="white", cursor="hand2")
            self._stop_title_lbl.configure(text_color="white", cursor="hand2")
            self._stop_sub_lbl.configure(text_color="#b0b8c8", cursor="hand2")
            bind_card(self._stop_card, self.stop_locust, darken(C_DANGER, 25), C_DANGER)
        else:
            self._stop_card.configure(fg_color="#3a3a3a", cursor="arrow")
            self._stop_icon_lbl.configure(text_color="#aaaaaa", cursor="arrow")
            self._stop_title_lbl.configure(text_color="#aaaaaa", cursor="arrow")
            self._stop_sub_lbl.configure(text_color="#666666", cursor="arrow")
            for w in [self._stop_card] + list(self._stop_card.winfo_children()):
                w.unbind("<Button-1>")
                w.unbind("<Enter>")
                w.unbind("<Leave>")

    def _run_test_thread(self):
        try:
            run_time = int(self.get("run_time"))
            interval = int(self.get("reach_interval") or 5)
            self._save_port_pool()
            self._save_env_from_gui()
            self._save_test_config(BASE_DIR)
            self.write_log("=" * 60)
            
                # ── Network Monitor ────────────────────────────────
            self._network_monitor = NetworkMonitor(
                interface=self.get("interface"),
                interval=1,
                output_file=os.path.join(DATA_DIR, "network_usage.csv")
            )
            self._network_monitor.start()
            self.write_log(f"📡 Network monitor started on {self.get('interface')}")
            # ──────────────────────────────────────────────────
            
            
            self.write_log("▶ Starting Reachability monitoring...")
            reach_thread = threading.Thread(target=self._run_reachability,
                                            args=(run_time, interval), daemon=True)
            reach_thread.start()
            self.write_log("▶ Starting Locust test...")
            self.write_log("-" * 60)
            cmd = ["locust", "-f", self.locustfile_path or os.path.join(BASE_DIR, "locust_tests", "Locustfile_http.py"),
                   "--headless", "-u", self.get("users"), "-r", self.get("spawn_rate"),
                   "--run-time", f"{run_time}s", "-H", self.get("target"),
                   "--processes", self.get("processes"), "--csv", os.path.join(DATA_DIR, "report")]
            self.write_log(f"CMD: {' '.join(cmd)}")
            self.write_log("-" * 60)
            self.locust_process = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                                    stderr=subprocess.STDOUT,
                                                    text=True, bufsize=1, cwd=BASE_DIR)
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
 # ── Network Monitor stop ───────────────────────
            if  self._network_monitor:
                self._network_monitor.stop()
                self._network_monitor = None
                self.write_log("📡 Network monitor stopped")
            self._run_card.configure(fg_color=C_SUCCESS, cursor="hand2")
            self._set_stop_enabled(False)

    def stop_locust(self):
        if not self._stop_enabled:
            return
        if self.locust_process and self.locust_process.poll() is None:
            self.locust_process.terminate()
            self.write_log("⛔ Locust test stopped by user")
        self._run_card.configure(fg_color=C_SUCCESS, cursor="hand2")
        self._set_stop_enabled(False)

    def _run_reachability(self, duration, interval):
        src_ip = self.get("reach_src_ip") or self._get_ip_start()
        use_v6 = is_ipv6(src_ip)

        class SourceIPAdapter(HTTPAdapter):
            def __init__(self, source_ip, source_port=0, **kwargs):
                self.source_ip = source_ip; self.source_port = source_port
                super().__init__(**kwargs)
            def init_poolmanager(self, *args, **kwargs):
                kwargs["source_address"] = (self.source_ip, self.source_port)
                super().init_poolmanager(*args, **kwargs)
            def send(self, request, **kwargs):
                old = urllib3_conn.create_connection
                sip, sport, v6 = self.source_ip, self.source_port, use_v6
                def patched(address, timeout=None, source_address=None, socket_options=None):
                    host, port = address
                    af = socket.AF_INET6 if v6 else socket.AF_INET
                    af, st, proto, _, sa = socket.getaddrinfo(host, port, af, socket.SOCK_STREAM)[0]
                    s = socket.socket(af, st, proto)
                    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    if socket_options:
                        for opt in socket_options: s.setsockopt(*opt)
                    s.bind((sip, sport, 0, 0) if v6 else (sip, sport))
                    s.settimeout(timeout); s.connect(sa); return s
                urllib3_conn.create_connection = patched
                try:
                    result = super().send(request, **kwargs)
                finally:
                    urllib3_conn.create_connection = old
                return result

        timeout_val = float(self.get("reach_timeout") or 5)
        port_pool   = parse_ports(self.get("src_ports"))
        src_port    = random.choice(port_pool) if port_pool else 0
        self.write_log(f"[Reachability] src={src_ip}:{src_port or 'random'} | interval={interval}s")
        session = requests.Session()
        adapter = SourceIPAdapter(src_ip, source_port=src_port)
        session.mount("http://", adapter); session.mount("https://", adapter)
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(os.path.join(DATA_DIR, "reachability.csv"), "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["timestamp","status_code","elapsed_time_s"])
            start = time.time()
            while time.time() - start < duration:
                ts = time.strftime("%Y-%m-%d %H:%M:%S")
                try:
                    r = session.get(self.get("target"), timeout=timeout_val)
                    writer.writerow([ts, r.status_code, r.elapsed.total_seconds()])
                    self.write_log(f"[Reachability] {ts} → {r.status_code} ({r.elapsed.total_seconds():.3f}s)")
                except Exception as ex:
                    writer.writerow([ts, "FAIL", -1])
                    self.write_log(f"[Reachability] {ts} → FAIL ({ex})")
                f.flush()
                time.sleep(interval)
        self.write_log("✓ Reachability complete → data/reachability.csv")

    # ================================================================
    # REPORT
    # ================================================================

    def generate_report(self):
        threading.Thread(target=self._generate_report_thread, daemon=True).start()

    def _generate_report_thread(self):
        try:
            target_clean, target_ip, source_range, interface, reach_threshold, test_type_cfg = \
                self._load_test_config(BASE_DIR)
            report_name = self._report_name_entry.get().strip() or "Locust_Report"
            if not report_name.endswith(".pdf"):
                report_name += ".pdf"
            save_dir    = self._report_dir_entry.get().strip() or REPORT_DIR
            os.makedirs(save_dir, exist_ok=True)
            pdf_path    = os.path.join(save_dir, report_name)
            sign        = self._sign_var.get()
            p12_path    = self._cert_path_entry.get().strip() if sign else ""
            p12_pass    = self.cert_pass.get().strip().encode() if sign else b""
            self.write_log("=" * 60)
            self.write_log("▶ Generating PDF report...")
            create_pdf_report(
                stats_file=os.path.join(DATA_DIR, "report_stats.csv"),
                history_file=os.path.join(DATA_DIR, "report_stats_history.csv"),
                output_file=pdf_path,
                meta_file=os.path.join(DATA_DIR, "report_metadata.csv"),
                network_file=os.path.join(DATA_DIR, "network_usage.csv"),
                comment=self.get_comment(), target_ip=target_ip,
                source_ip=source_range, interface=interface,
                reach_threshold=reach_threshold / 100, test_type=test_type_cfg,
                src_ports=self.get("src_ports") or None,
                sign=sign, p12_path=p12_path, p12_pass=p12_pass,
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
            remove_pool(ip_start=self._get_ip_start(), ip_end=self._get_ip_end(),
                        interface=self.get("interface"),
                        pool_file=os.path.join(BASE_DIR, "ip_pool.txt"),
                        ip_version=self._active_ip_version(), ip_list=self._get_ip_list())
            self.write_log("✓ Cleanup complete")
            self.write_log("=" * 60)
        except Exception as e:
            self.write_log(f"✗ Cleanup error: {e}")


if __name__ == "__main__":
    app = LocustGUI()
    app.mainloop()

