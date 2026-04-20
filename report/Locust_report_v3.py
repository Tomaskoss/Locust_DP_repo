#!/usr/bin/env python3
import matplotlib
matplotlib.use('Agg')

import os
import sys
import pandas as pd
import json
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak
)
from reportlab.platypus.flowables import Flowable
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from datetime import datetime

# === PATHS ===
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR   = os.path.join(BASE_DIR, "data")
REPORT_DIR = os.path.dirname(os.path.abspath(__file__))

# === CONFIGURATION ===
STATS_FILE    = os.path.join(DATA_DIR, "report_stats.csv")
HISTORY_FILE  = os.path.join(DATA_DIR, "report_stats_history.csv")
NETWORK_FILE  = os.path.join(DATA_DIR, "network_usage.csv")
META_FILE     = os.path.join(DATA_DIR, "report_metadata.csv")
PDF_FILE      = os.path.join(REPORT_DIR, "Locust_Report.pdf")
FAILURES_FILE = os.path.join(DATA_DIR, "report_failures.csv")
REACH_FILE    = os.path.join(DATA_DIR, "reachability.csv")   # <-- NOVÉ

# Biele stránky — text musí byť tmavý
C_TEXT       = colors.HexColor("#1a1a1a")
C_TEXT_MUTED = colors.HexColor("#555555")

# Akcenty
C_PRIMARY      = colors.HexColor("#2a5f3a")
C_PRIMARY_DARK = colors.HexColor("#1e4a2c")
C_ACCENT       = colors.HexColor("#2a5f3a")
C_DANGER       = colors.HexColor("#922b21")
C_SURFACE      = colors.HexColor("#f5f5f5")
C_SURFACE2     = colors.HexColor("#ebebeb")
C_ROW_ALT      = colors.HexColor("#f0f5f1")
C_BORDER       = colors.HexColor("#cccccc")
C_WHITE        = colors.white

PAGE_W, PAGE_H = A4
MARGIN         = 18 * mm


# ================================================================
# CUSTOM FLOWABLES
# ================================================================

class ColorBand(Flowable):
    def __init__(self, text, bg=None, height=28, font_size=13):
        super().__init__()
        self.text      = text
        self.bg        = bg or C_PRIMARY
        self.height    = height
        self.font_size = font_size
        self.width     = PAGE_W - 2 * MARGIN

    def draw(self):
        self.canv.setFillColor(self.bg)
        self.canv.roundRect(0, 0, self.width, self.height, 6, fill=1, stroke=0)
        self.canv.setFillColor(C_WHITE)
        self.canv.setFont("Helvetica-Bold", self.font_size)
        self.canv.drawString(12, 8, self.text)

    def wrap(self, *args):
        return self.width, self.height


class HeroHeader(Flowable):
    def __init__(self, title, subtitle, logo_path=None):
        super().__init__()
        self.title     = title
        self.subtitle  = subtitle
        self.logo_path = logo_path
        self.width     = PAGE_W - 2 * MARGIN
        self.height    = 90

    def draw(self):
        w, h = self.width, self.height
        self.canv.setFillColor(C_PRIMARY_DARK)
        self.canv.roundRect(0, 0, w, h, 10, fill=1, stroke=0)
        self.canv.setFillColor(C_PRIMARY)
        self.canv.roundRect(w * 0.70, 0, w * 0.30, h, 10, fill=1, stroke=0)
        self.canv.rect(w * 0.70, 0, 20, h, fill=1, stroke=0)

        if self.logo_path and os.path.exists(self.logo_path):
            self.canv.drawImage(
                self.logo_path,
                w - 130, 15, width=110, height=60,
                mask='auto', preserveAspectRatio=True
            )

        self.canv.setFillColor(C_WHITE)
        self.canv.setFont("Helvetica-Bold", 22)
        self.canv.drawString(16, h - 34, self.title)
        self.canv.setFont("Helvetica", 11)
        self.canv.setFillColor(colors.HexColor("#BDD7FF"))
        self.canv.drawString(16, h - 54, self.subtitle)

    def wrap(self, *args):
        return self.width, self.height


def _page_template(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(C_TEXT_MUTED)
    canvas.setStrokeColor(C_BORDER)
    canvas.setLineWidth(0.5)
    canvas.line(MARGIN, 18 * mm, PAGE_W - MARGIN, 18 * mm)
    canvas.drawString(MARGIN, 13 * mm, "Locust Load Test Report")
    canvas.drawRightString(
        PAGE_W - MARGIN, 13 * mm,
        f"Strana {doc.page}  •  {datetime.now().strftime('%d.%m.%Y')}"
    )
    canvas.restoreState()


# ================================================================
# HELPER FUNCTIONS
# ================================================================

def generate_topology_diagram(target_ip=None, source_ip=None,
                                interface=None, output_file=None,
                                reach_src_ip=None):
    if output_file is None:
        output_file = os.path.join(REPORT_DIR, "topology_diagram.png")
    try:
        sys.path.insert(0, os.path.join(BASE_DIR, "network"))
        from Create_topology import create_topology_diagram
        create_topology_diagram(
            target_ip    = target_ip    or "Unknown",
            source_ip    = source_ip    or "Unknown",
            interface    = interface    or "ens33",
            output_file  = output_file,
            reach_src_ip = reach_src_ip
        )
        print("✓ Topology diagram generated")
        return True
    except Exception as e:
        print(f"✗ Error generating topology: {e}")
        return False


def _get_os_port_range():
    try:
        with open("/proc/sys/net/ipv4/ip_local_port_range") as f:
            lo, hi = f.read().split()
        return f"OS ephemeral ({lo}–{hi})"
    except Exception:
        return "OS assigned (random)"


def load_test_times(meta_path):
    if os.path.exists(meta_path):
        try:
            df             = pd.read_csv(meta_path)
            start_time_raw = str(df.iloc[0].get("start_time",  "Unknown"))
            end_time_raw   = str(df.iloc[0].get("end_time",    "Unknown"))
            test_type      = str(df.iloc[0].get("test_type",   "Unknown"))
            target_host    = str(df.iloc[0].get("target_host", "Unknown"))
            target_ip      = str(df.iloc[0].get("target_ip",   "Unknown"))
            used_ips       = str(df.iloc[0].get("used_ips",    "Unknown"))
            try:
                start_time = datetime.fromisoformat(start_time_raw).strftime("%H:%M:%S")
                end_time   = datetime.fromisoformat(end_time_raw).strftime("%H:%M:%S")
            except Exception:
                start_time = start_time_raw
                end_time   = end_time_raw
            return start_time, end_time, test_type, target_host, target_ip, used_ips
        except Exception as e:
            print(f"Failed to load {meta_path}: {e}")
    return "Unknown", "Unknown", "Unknown", "Unknown", "Unknown", "Unknown"


def compute_duration(start_str, end_str):
    try:
        fmt      = "%H:%M:%S"
        start_dt = datetime.strptime(start_str, fmt)
        end_dt   = datetime.strptime(end_str,   fmt)
        delta    = end_dt - start_dt
        if delta.total_seconds() < 0:
            delta = (datetime.combine(datetime.today(), end_dt.time()) -
                     datetime.combine(datetime.today(), start_dt.time()))
        total = delta.total_seconds()
        m, s  = divmod(total, 60)
        h, m  = divmod(int(m), 60)
        if h > 0:
            return f"{h}h {m}m"
        elif m > 0:
            return f"{m}m {int(s)}s"
        else:
            return f"{s:.1f}s"
    except Exception:
        return "Unknown"


def add_stages_table(story, S, base_dir):
    stages_path = os.path.join(base_dir, "stages.json")
    if not os.path.exists(stages_path):
        return
    try:
        with open(stages_path) as f:
            stages = json.load(f)
        if not stages:
            return

        S_head = ParagraphStyle("sh", fontSize=9, textColor=colors.white,
                                 fontName="Helvetica-Bold", alignment=TA_CENTER)
        S_cell = ParagraphStyle("sc", fontSize=9, textColor=C_TEXT,
                                 alignment=TA_CENTER, leading=12)

        rows = [[
            Paragraph("Stage",           S_head),
            Paragraph("Duration (s)",    S_head),
            Paragraph("Users",           S_head),
            Paragraph("Spawn Rate",      S_head),
            Paragraph("Cumulative Time", S_head),
        ]]

        for i, stage in enumerate(stages, 1):
            duration   = int(stage.get("duration",   0))
            users      = int(stage.get("users",      0))
            spawn_rate = int(stage.get("spawn_rate", 0))
            m, s = divmod(duration, 60)
            h, m = divmod(m, 60)
            if h > 0:
                cum_str = f"{h}h {m}m {s}s"
            elif m > 0:
                cum_str = f"{m}m {s}s"
            else:
                cum_str = f"{s}s"

            rows.append([
                Paragraph(str(i),          S_cell),
                Paragraph(str(duration),   S_cell),
                Paragraph(str(users),      S_cell),
                Paragraph(str(spawn_rate), S_cell),
                Paragraph(cum_str,         S_cell),
            ])

        col_w = (PAGE_W - 2 * MARGIN) / 5
        t = Table(rows, colWidths=[col_w] * 5)
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0), C_PRIMARY_DARK),
            ("ROWBACKGROUNDS",(0, 1), (-1,-1), [C_WHITE, C_ROW_ALT]),
            ("GRID",          (0, 0), (-1,-1), 0.4, C_BORDER),
            ("LEFTPADDING",   (0, 0), (-1,-1), 6),
            ("RIGHTPADDING",  (0, 0), (-1,-1), 6),
            ("TOPPADDING",    (0, 0), (-1,-1), 5),
            ("BOTTOMPADDING", (0, 0), (-1,-1), 5),
            ("VALIGN",        (0, 0), (-1,-1), "MIDDLE"),
        ]))

        story.append(ColorBand("  Test Stages"))
        story.append(Spacer(1, 8))
        story.append(t)
        story.append(Spacer(1, 14))

    except Exception as e:
        print(f"Warning: Could not load stages: {e}")


# ================================================================
# TABLE HELPERS
# ================================================================

def make_info_table(rows, col_widths=None):
    col_widths = col_widths or [160, None]
    t = Table(rows, colWidths=col_widths, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("FONTNAME",       (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME",       (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE",       (0, 0), (-1, -1), 10),
        ("TEXTCOLOR",      (0, 0), (0, -1), C_PRIMARY_DARK),
        ("TEXTCOLOR",      (1, 0), (1, -1), C_TEXT),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [C_WHITE, C_ROW_ALT]),
        ("GRID",           (0, 0), (-1, -1), 0.4, C_BORDER),
        ("LEFTPADDING",    (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",   (0, 0), (-1, -1), 10),
        ("TOPPADDING",     (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 6),
    ]))
    return t


def make_metric_cards(metrics):
    n     = len(metrics)
    width = (PAGE_W - 2 * MARGIN - (n - 1) * 4) / n

    cells = []
    for label, value, bg in metrics:
        inner = Table(
            [
                [Paragraph(f"<b>{value}</b>",
                           ParagraphStyle("cv", fontSize=16, textColor=C_WHITE,
                                          alignment=TA_CENTER,
                                          fontName="Helvetica-Bold"))],
                [Paragraph(label,
                           ParagraphStyle("cl", fontSize=8,
                                          textColor=colors.HexColor("#BDD7FF"),
                                          alignment=TA_CENTER))]
            ],
            colWidths=[width]
        )
        inner.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), bg),
            ("TOPPADDING",    (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ]))
        cells.append(inner)

    grid = Table([cells], colWidths=[width] * n, hAlign="LEFT")
    grid.setStyle(TableStyle([
        ("LEFTPADDING",  (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING",   (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 0),
    ]))
    return grid


# ================================================================
# MATPLOTLIB STYLE
# ================================================================

def _apply_chart_style(ax, title):
    ax.set_facecolor("#F8F9FA")
    ax.get_figure().set_facecolor("white")
    ax.set_title(title, fontsize=11, fontweight="bold", color="#202124", pad=10)
    ax.tick_params(colors="#5F6368", labelsize=8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#DADCE0")
    ax.spines["bottom"].set_color("#DADCE0")
    ax.grid(True, linestyle="--", linewidth=0.5, color="#E0E0E0", alpha=0.8)
    ax.set_xlabel(ax.get_xlabel(), fontsize=9, color="#5F6368")
    ax.set_ylabel(ax.get_ylabel(), fontsize=9, color="#5F6368")


def save_chart(path, dpi=180):
    plt.tight_layout()
    plt.savefig(path, dpi=dpi, bbox_inches="tight", facecolor="white")
    plt.close()


# ================================================================
# CHART FUNCTIONS
# ================================================================

def add_time_series_charts(history_df, story):
    if 'Timestamp' not in history_df.columns:
        return

    history_df['Timestamp'] = pd.to_datetime(history_df['Timestamp'], unit='s')

    p1 = os.path.join(REPORT_DIR, "chart_rps_failures.png")
    fig, ax = plt.subplots(figsize=(7, 3))
    ax.fill_between(history_df['Timestamp'], history_df['Requests/s'],
                    alpha=0.15, color="#1A73E8")
    ax.plot(history_df['Timestamp'], history_df['Requests/s'],
            label='Requests/s', color="#1A73E8", linewidth=1.8)
    ax.plot(history_df['Timestamp'], history_df['Failures/s'],
            label='Failures/s', color="#EA4335", linewidth=1.8, linestyle="--")
    ax.set_ylabel("Requests/s")
    ax.legend(fontsize=8, framealpha=0.8)
    _apply_chart_style(ax, "Requests per Second Over Time")
    save_chart(p1)
    story.append(Image(p1, width=440, height=190))
    story.append(Spacer(1, 10))

    p2 = os.path.join(REPORT_DIR, "chart_response_times.png")
    fig, ax = plt.subplots(figsize=(7, 3))
    ax.fill_between(
        history_df['Timestamp'],
        history_df['Total Min Response Time'] / 1000,
        history_df['Total Max Response Time'] / 1000,
        alpha=0.08, color="#1A73E8"
    )
    ax.plot(history_df['Timestamp'], history_df['Total Min Response Time']    / 1000,
            label='Min',    linestyle='--', color="#34A853", linewidth=1.5)
    ax.plot(history_df['Timestamp'], history_df['Total Median Response Time'] / 1000,
            label='Median', linestyle='-',  color="#1A73E8", linewidth=2)
    ax.plot(history_df['Timestamp'], history_df['Total Max Response Time']    / 1000,
            label='Max',    linestyle='-.', color="#EA4335", linewidth=1.5)
    ax.set_ylabel("Response Time (s)")
    ax.legend(fontsize=8, framealpha=0.8)
    _apply_chart_style(ax, "Response Times Over Time")
    save_chart(p2)
    story.append(Image(p2, width=440, height=190))
    story.append(Spacer(1, 10))

    if 'User Count' in history_df.columns:
        p3 = os.path.join(REPORT_DIR, "chart_users.png")
        fig, ax = plt.subplots(figsize=(7, 3))
        ax.fill_between(history_df['Timestamp'], history_df['User Count'],
                        alpha=0.15, color="#7B2FBE")
        ax.plot(history_df['Timestamp'], history_df['User Count'],
                color="#7B2FBE", linewidth=1.8, label="Users")
        ax.set_ylabel("Number of Users")
        ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
        ax.legend(fontsize=8)
        _apply_chart_style(ax, "Number of Users Over Time")
        save_chart(p3)
        story.append(Image(p3, width=440, height=190))
        story.append(Spacer(1, 10))


# ================================================================
# REACHABILITY FUNCTIONS  <-- NOVÉ
# ================================================================

def load_reachability_data(reach_file):
    """
    Načíta reachability.csv a vráti (reachable_count, unreachable_count, df).
    Sonda je reachable ak status_code je 200-299.
    Vracia (None, None, None) ak súbor neexistuje alebo je prázdny.
    """
    if not os.path.exists(reach_file):
        print(f"Reachability file not found: {reach_file}")
        return None, None, None
    try:
        df = pd.read_csv(reach_file)
        if df.empty:
            return None, None, None
        df["reachable"] = (df["status_code"] >= 200) & (df["status_code"] < 500)
        reachable_count   = int(df["reachable"].sum())
        unreachable_count = int((~df["reachable"]).sum())
        print(f"✓ Reachability data loaded: {reachable_count} reachable, {unreachable_count} unreachable")
        return reachable_count, unreachable_count, df
    except Exception as e:
        print(f"Error loading reachability data: {e}")
        return None, None, None

def add_reachability_delay_chart(df, story, reach_timeout_s=None):
    try:
        df = df.copy()
        df["timestamp"] = pd.to_datetime(df["unix_timestamp"], unit="s")
        df["delay_ms"]  = df["elapsed_time_s"] * 1000.0

        # ── PÄŤ kategórií — timeout a 5xx sú odlíšené farbou ─────────
        def classify(code):
            if 200 <= code < 300:
                return "reachable"
            elif code == 429:
                return "rate_limited"
            elif code == 0:
                # status 0 = request vôbec nedorazil / exception (connection refused, timeout)
                return "timeout"
            elif 500 <= code < 600:
                return "error_5xx"
            else:
                # 4xx okrem 429, alebo iné neočakávané kódy
                return "error_other"

        df["category"] = df["status_code"].apply(classify)
        df["reachable"] = df["category"] == "reachable"

        # ── Farby ─────────────────────────────────────────────────────
        # Zelená   = OK
        # Žltá     = rate-limited
        # Oranžová = timeout (sieťová nedostupnosť, žiadna odpoveď)
        # Červená  = HTTP 5xx (server odpovedal, ale s chybou)
        # Šedá     = iný HTTP kód (4xx okrem 429)
        COLORS = {
            "reachable":    "#34A853",
            "rate_limited": "#F9AB00",
            "timeout":      "#FF6D00",
            "error_5xx":    "#EA4335",
            "error_other":  "#9E9E9E",
        }
        LABELS = {
            "reachable":    "Reachable (2xx)",
            "rate_limited": "Rate-limited (429)",
            "timeout":      "Timeout / No response (status=0)",
            "error_5xx":    "Server error (5xx)",
            "error_other":  "Other error (4xx etc.)",
        }

        # Kategórie zoradené od najhoršej — určujú farbu segmentu čiary
        SEVERITY = ["error_5xx", "timeout", "rate_limited", "error_other", "reachable"]

        def worse_category(cat_a, cat_b):
            ia = SEVERITY.index(cat_a) if cat_a in SEVERITY else len(SEVERITY)
            ib = SEVERITY.index(cat_b) if cat_b in SEVERITY else len(SEVERITY)
            return cat_a if ia <= ib else cat_b

        t_start = df["timestamp"].iloc[0]
        t_end   = df["timestamp"].iloc[-1]

        p_delay = os.path.join(REPORT_DIR, "chart_reach_delay.png")
        fig, ax = plt.subplots(figsize=(7.5, 3.5))

        # ── Tieňovanie pozadia pre problémové intervaly ──────────────
        shade_color = {
            "rate_limited": "#F9AB00",
            "timeout":      "#FF6D00",
            "error_5xx":    "#EA4335",
            "error_other":  "#9E9E9E",
        }
        for cat, color in shade_color.items():
            in_block, block_start = False, None
            for _, row in df.iterrows():
                if row["category"] == cat and not in_block:
                    block_start, in_block = row["timestamp"], True
                elif row["category"] != cat and in_block:
                    ax.axvspan(block_start, row["timestamp"],
                               color=color, alpha=0.10, zorder=1)
                    in_block = False
            if in_block and block_start is not None:
                ax.axvspan(block_start, t_end, color=color, alpha=0.10, zorder=1)

        # ── Segmentovaná čiara — farba = horšia zo dvoch kategórií ──
        for i in range(len(df) - 1):
            row_a = df.iloc[i]
            row_b = df.iloc[i + 1]
            seg_cat   = worse_category(row_a["category"], row_b["category"])
            seg_color = COLORS[seg_cat]

            ax.plot(
                [row_a["timestamp"], row_b["timestamp"]],
                [row_a["delay_ms"],  row_b["delay_ms"]],
                color=seg_color, linewidth=1.8, zorder=2
            )

        # ── Body — každá kategória zvlášť ────────────────────────────
        marker_cfg = {
            "reachable":    dict(s=18, marker="o", linewidths=1.2),
            "rate_limited": dict(s=28, marker="^", linewidths=1.5),
            "timeout":      dict(s=32, marker="D", linewidths=1.5),
            "error_5xx":    dict(s=32, marker="x", linewidths=2.0),
            "error_other":  dict(s=22, marker="s", linewidths=1.2),
        }
        for cat, cfg in marker_cfg.items():
            mask = df["category"] == cat
            if mask.any():
                ax.scatter(
                    df.loc[mask, "timestamp"],
                    df.loc[mask, "delay_ms"],
                    color=COLORS[cat],
                    zorder=4,
                    label=LABELS[cat],
                    **cfg
                )

        # ── Threshold čiara ──────────────────────────────────────────
        if reach_timeout_s is not None:
            threshold_ms = reach_timeout_s * 1000.0
            ax.axhline(
                y=threshold_ms,
                color="#EA4335",
                linestyle="--",
                linewidth=1.5,
                alpha=0.75,
                zorder=3,
                label=f"Timeout threshold ({reach_timeout_s} s = {threshold_ms:.0f} ms)"
            )
            ax.text(
                t_end,
                threshold_ms,
                f"  {threshold_ms:.0f} ms",
                va="center",
                ha="left",
                fontsize=7,
                color="#EA4335",
                transform=ax.transData
            )

        # ── Os X ─────────────────────────────────────────────────────
        import matplotlib.dates as mdates

        total_seconds = (t_end - t_start).total_seconds()
        if total_seconds <= 300:
            locator   = mdates.SecondLocator(interval=max(1, int(total_seconds / 8)))
            formatter = mdates.DateFormatter("%H:%M:%S")
        elif total_seconds <= 3600:
            locator   = mdates.MinuteLocator(interval=max(1, int(total_seconds / 60 / 8)))
            formatter = mdates.DateFormatter("%H:%M:%S")
        elif total_seconds <= 86400:
            locator   = mdates.MinuteLocator(interval=max(5, int(total_seconds / 60 / 8)))
            formatter = mdates.DateFormatter("%d.%m %H:%M")
        else:
            locator   = mdates.HourLocator(interval=max(1, int(total_seconds / 3600 / 8)))
            formatter = mdates.DateFormatter("%d.%m %H:%M")

        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_major_formatter(formatter)
        ax.set_xlim(t_start, t_end)

        from matplotlib.dates import date2num
        existing = list(ax.get_xticks())
        ax.set_xticks(sorted(set(existing + [date2num(t_start), date2num(t_end)])))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=25, ha="right", fontsize=7)

        ax.set_ylabel("Response Delay (ms)")
        ax.set_xlabel("")
        ax.legend(fontsize=7.5, framealpha=0.85, loc="upper left")
        _apply_chart_style(ax, "Reachability — Response Delay Over Time")

        # ── Os Y ─────────────────────────────────────────────────────
        y_min = max(0, df["delay_ms"].min() * 0.8)
        y_max = df["delay_ms"].max() * 1.20
        if reach_timeout_s:
            y_max = max(y_max, reach_timeout_s * 1000 * 1.05)
        ax.set_ylim(bottom=y_min, top=y_max)

        save_chart(p_delay, dpi=200)
        story.append(Image(p_delay, width=470, height=220))
        story.append(Spacer(1, 6))

        # ── Tabuľka pod grafom — timeout a 5xx zvlášť ────────────────
        reach_ok      = df[df["category"] == "reachable"]
        reach_rl      = df[df["category"] == "rate_limited"]
        reach_timeout = df[df["category"] == "timeout"]
        reach_5xx     = df[df["category"] == "error_5xx"]
        reach_other   = df[df["category"] == "error_other"]
        total_probes  = len(df)

        avg_delay_ok = (
            f"{reach_ok['elapsed_time_s'].mean() * 1000:.1f} ms"
            if len(reach_ok) > 0 else "—"
        )

        S_hd = ParagraphStyle(
            "dh",
            fontSize=8,
            textColor=C_WHITE,
            fontName="Helvetica-Bold",
            alignment=TA_CENTER
        )
        S_cd = ParagraphStyle(
            "dc",
            fontSize=9,
            textColor=C_TEXT,
            fontName="Helvetica-Bold",
            alignment=TA_CENTER,
            leading=13
        )

        cw = (PAGE_W - 2 * MARGIN) / 7
        compact_table = Table(
            [
                [
                    Paragraph("Total probes",         S_hd),
                    Paragraph("Reachable",            S_hd),
                    Paragraph("Rate-limited (429)",   S_hd),
                    Paragraph("Timeout",              S_hd),
                    Paragraph("Server error (5xx)",   S_hd),
                    Paragraph("Other error",          S_hd),
                    Paragraph("Avg delay (reachable)",S_hd),
                ],
                [
                    Paragraph(str(total_probes),       S_cd),
                    Paragraph(str(len(reach_ok)),      S_cd),
                    Paragraph(str(len(reach_rl)),      S_cd),
                    Paragraph(str(len(reach_timeout)), S_cd),
                    Paragraph(str(len(reach_5xx)),     S_cd),
                    Paragraph(str(len(reach_other)),   S_cd),
                    Paragraph(avg_delay_ok,            S_cd),
                ],
            ],
            colWidths=[cw] * 7
        )
        compact_table.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0), C_PRIMARY_DARK),
            ("BACKGROUND",    (0, 1), (-1, 1), C_WHITE),
            ("BACKGROUND",    (2, 1), (2, 1),
             colors.HexColor("#FFF8E1") if len(reach_rl) > 0 else C_WHITE),
            ("BACKGROUND",    (3, 1), (3, 1),
             colors.HexColor("#FFF3E0") if len(reach_timeout) > 0 else C_WHITE),
            ("BACKGROUND",    (4, 1), (4, 1),
             colors.HexColor("#FDECEA") if len(reach_5xx) > 0 else C_WHITE),
            ("BACKGROUND",    (5, 1), (5, 1),
             colors.HexColor("#F5F5F5") if len(reach_other) > 0 else C_WHITE),
            ("GRID",          (0, 0), (-1, -1), 0.4, C_BORDER),
            ("TOPPADDING",    (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING",   (0, 0), (-1, -1), 4),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
            ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(compact_table)
        story.append(Spacer(1, 12))

    except Exception as e:
        print(f"Error creating delay chart: {e}")
        import traceback
        traceback.print_exc()
def add_network_traffic_charts(network_file, history_file, story,
                               failure_threshold=0.5):
    if not os.path.exists(network_file):
        print(f"Network file '{network_file}' not found, charts skipped")
        return
    try:
        network_df = pd.read_csv(network_file, on_bad_lines='skip')
        network_df = network_df[network_df['timestamp'] > 1_000_000_000].copy()
        network_df['timestamp'] = pd.to_datetime(network_df['timestamp'], unit='s')

        unreachable_ts = []
        if os.path.exists(history_file):
            try:
                hdf = pd.read_csv(history_file)
                hdf['Timestamp'] = pd.to_datetime(hdf['Timestamp'], unit='s')
                if 'Failures/s' in hdf.columns and 'Requests/s' in hdf.columns:
                    for _, row in hdf.iterrows():
                        if (row['Requests/s'] > 0 and
                                (row['Failures/s'] / row['Requests/s']) > failure_threshold):
                            unreachable_ts.append(row['Timestamp'])
            except Exception as e:
                print(f"Warning: {e}")

        p4    = os.path.join(REPORT_DIR, "chart_network_total.png")
        rx_mb = (network_df['rx_total'] - network_df['rx_total'].iloc[0]) / (1024 * 1024)
        tx_mb = (network_df['tx_total'] - network_df['tx_total'].iloc[0]) / (1024 * 1024)
        rx_mb = rx_mb.clip(lower=0)
        tx_mb = tx_mb.clip(lower=0)

        fig, ax1 = plt.subplots(figsize=(7, 3))
        ax1.fill_between(network_df['timestamp'], rx_mb, alpha=0.12, color="#1A73E8")
        ax1.plot(network_df['timestamp'], rx_mb,
                 color="#1A73E8", linewidth=1.8, label="RX MB")
        ax1.set_ylabel("Received MB", color="#1A73E8", fontsize=9)
        ax2 = ax1.twinx()
        ax2.fill_between(network_df['timestamp'], tx_mb, alpha=0.08, color="#7B2FBE")
        ax2.plot(network_df['timestamp'], tx_mb,
                 color="#7B2FBE", linewidth=1.8, label="TX MB")
        ax2.set_ylabel("Transmitted MB", color="#7B2FBE", fontsize=9)
        for ts in unreachable_ts:
            ax1.axvline(x=ts, color="#EA4335", alpha=0.25, linewidth=1)
        lines1, l1 = ax1.get_legend_handles_labels()
        lines2, l2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, l1 + l2, fontsize=8, loc="upper left")
        _apply_chart_style(ax1, "Total Network Traffic (Cumulative)")
        save_chart(p4)
        story.append(Image(p4, width=440, height=190))
        story.append(Spacer(1, 10))

        p5 = os.path.join(REPORT_DIR, "chart_network_speed.png")
        fig, ax = plt.subplots(figsize=(7, 3))
        ax.fill_between(network_df['timestamp'], network_df['rx_kbps'],
                        alpha=0.12, color="#1A73E8")
        ax.plot(network_df['timestamp'], network_df['rx_kbps'],
                color="#1A73E8", linewidth=1.8, label="RX kB/s")
        ax.fill_between(network_df['timestamp'], network_df['tx_kbps'],
                        alpha=0.08, color="#7B2FBE")
        ax.plot(network_df['timestamp'], network_df['tx_kbps'],
                color="#7B2FBE", linewidth=1.8, label="TX kB/s")
        for ts in unreachable_ts:
            ax.axvline(x=ts, color="#EA4335", alpha=0.25, linewidth=1)
        ax.set_ylabel("Speed (kB/s)")
        ax.legend(fontsize=8)
        _apply_chart_style(ax, "Network Transfer Speed")
        save_chart(p5)
        story.append(Image(p5, width=440, height=190))
        story.append(Spacer(1, 12))

        rx_kb = ((network_df["rx_total"] - network_df["rx_total"].iloc[0]) / 1024).clip(lower=0)
        tx_kb = ((network_df["tx_total"] - network_df["tx_total"].iloc[0]) / 1024).clip(lower=0)
        rx_kb = rx_kb.iloc[1:]
        tx_kb = tx_kb.iloc[1:]
        rx_kb = rx_kb[rx_kb > 0]
        tx_kb = tx_kb[tx_kb > 0]

        TRANSFER_THRESHOLD_rxs = 1.0
        TRANSFER_THRESHOLD_txs = 1.0

        rxs_nz = network_df[network_df['rx_kbps'] > TRANSFER_THRESHOLD_rxs]['rx_kbps']
        txs_nz = network_df[network_df['tx_kbps'] > TRANSFER_THRESHOLD_txs]['tx_kbps']

        def _stat(s):
            return (
                s.min()  if len(s) > 0 else 0,
                s.max()  if len(s) > 0 else 0,
                s.mean() if len(s) > 0 else 0,
            )

        rx_total_min, rx_total_max, rx_total_avg = _stat(rx_kb)
        tx_total_min, tx_total_max, tx_total_avg = _stat(tx_kb)
        rx_spd_min,   rx_spd_max,   rx_spd_avg   = _stat(rxs_nz)
        tx_spd_min,   tx_spd_max,   tx_spd_avg   = _stat(txs_nz)

        col_w = (PAGE_W - 2 * MARGIN - 4 * 8) / 4

        def net_table(title, data_rows, header_color):
            rows = [[
                Paragraph(f"<b>{title}</b>",
                          ParagraphStyle("nh", fontSize=9, textColor=C_WHITE,
                                         fontName="Helvetica-Bold")),
                Paragraph("<b>Hodnota</b>",
                          ParagraphStyle("nv", fontSize=9, textColor=C_WHITE,
                                         fontName="Helvetica-Bold"))
            ]] + [
                [Paragraph(r, ParagraphStyle("nr",  fontSize=9, textColor=C_TEXT)),
                 Paragraph(v, ParagraphStyle("nv2", fontSize=9, textColor=C_TEXT,
                                             alignment=TA_RIGHT))]
                for r, v in data_rows
            ]
            cw1 = col_w * 0.58
            cw2 = col_w * 0.42
            t   = Table(rows, colWidths=[cw1, cw2])
            t.setStyle(TableStyle([
                ("BACKGROUND",    (0, 0), (-1, 0), header_color),
                ("ROWBACKGROUNDS",(0, 1), (-1, -1), [C_WHITE, C_ROW_ALT]),
                ("GRID",          (0, 0), (-1, -1), 0.4, C_BORDER),
                ("TOPPADDING",    (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING",   (0, 0), (-1, -1), 6),
                ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
                ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
            ]))
            return t

        t1 = net_table("RX Total [kB]",
                       [("Min",     f"{rx_total_min:.2f}"),
                        ("Max",     f"{rx_total_max:.2f}"),
                        ("Average", f"{rx_total_avg:.2f}")],
                       C_PRIMARY)
        t2 = net_table("RX [kB/s]",
                       [("Min",     f"{rx_spd_min:.2f}"),
                        ("Max",     f"{rx_spd_max:.2f}"),
                        ("Average", f"{rx_spd_avg:.2f}")],
                       colors.HexColor("#1558A8"))
        t3 = net_table("TX Total [kB]",
                       [("Min",     f"{tx_total_min:.2f}"),
                        ("Max",     f"{tx_total_max:.2f}"),
                        ("Average", f"{tx_total_avg:.2f}")],
                       colors.HexColor("#7B2FBE"))
        t4 = net_table("TX [kB/s]",
                       [("Min",     f"{tx_spd_min:.2f}"),
                        ("Max",     f"{tx_spd_max:.2f}"),
                        ("Average", f"{tx_spd_avg:.2f}")],
                       colors.HexColor("#5E1A9C"))

        grid = Table(
            [[t1, t2, t3, t4]],
            colWidths=[col_w + 8] * 4,
            hAlign="LEFT"
        )
        grid.setStyle(TableStyle([
            ("LEFTPADDING",  (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(ColorBand("  Network Traffic Statistics",
                               bg=colors.HexColor("#1558A8"), height=24, font_size=11))
        story.append(Spacer(1, 8))
        story.append(grid)
        story.append(Spacer(1, 12))

    except Exception as e:
        print(f"Error creating network charts: {e}")
        story.append(Paragraph(f"Error: {e}",
                               ParagraphStyle("err", fontSize=9, textColor=C_DANGER)))
        story.append(Spacer(1, 12))


# ================================================================
# SIGNING
# ================================================================

def sign_report(input_path, output_path,
                p12_path="cert.p12", p12_pass=b"yourpassword"):
    """Digitálne podpíše PDF report pomocou .p12 certifikátu (pyHanko)."""
    try:
        from pyhanko.sign import signers
        from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
    except ImportError:
        print("⚠ pyhanko nie je nainštalovaný. Signing preskočený.")
        return

    if not os.path.exists(p12_path):
        print(f"⚠ Certifikát '{p12_path}' neexistuje. Signing preskočený.")
        return

    signer = signers.SimpleSigner.load_pkcs12(
        pfx_file   = p12_path,
        passphrase = p12_pass
    )
    with open(input_path, "rb") as inf:
        w = IncrementalPdfFileWriter(inf)
        with open(output_path, "wb") as out:
            signers.sign_pdf(
                w,
                signers.PdfSignatureMetadata(field_name="Signature1"),
                signer = signer,
                output = out
            )
    print(f"✓ Signed PDF: {output_path}")


# ================================================================
# PDF GENERATION
# ================================================================

def create_pdf_report(stats_file, history_file, output_file,
                      meta_file=None, network_file=None,
                      reach_file=None,                         # <-- NOVÉ
                      reach_timeout=None,                      # <-- NOVÉ timeout threshold v sekundách
                      comment=None,
                      target_ip=None, source_ip=None, interface=None,
                      reach_threshold=0.5, test_type=None,
                      src_ports=None, reach_src_ip=None,
                      ip_pool_count=None, ip_pool_range=None,
                      sign=False, p12_path=None, p12_pass=b"yourpassword"):

    if meta_file    is None: meta_file    = META_FILE
    if network_file is None: network_file = NETWORK_FILE
    if reach_file   is None: reach_file   = REACH_FILE        # <-- NOVÉ
    if reach_timeout is None:
        try:
            import os as _os
            _rt = _os.getenv("REACH_TIMEOUT")
            reach_timeout = float(_rt) if _rt else None
        except Exception:
            reach_timeout = None

    if not os.path.exists(stats_file):
        print(f"CSV file '{stats_file}' not found.")
        return

    stats_df   = pd.read_csv(stats_file)
    agg = stats_df[stats_df["Name"] == "Aggregated"]
    if agg.empty:
        print("Stats CSV has no valid rows.")
        return

    data_row     = agg.iloc[0] if not agg.empty else statsdf.iloc[-1]
    req_count    = int(data_row["Request Count"])
    fail_count   = int(data_row["Failure Count"])
    success      = req_count - fail_count
    failure_rate = round((fail_count / req_count) * 100, 2) if req_count > 0 else 0
    avg_resp     = round(data_row["Average Response Time"] / 1000, 3)
    median_resp  = round(data_row["Median Response Time"]  / 1000, 3)
    min_resp     = round(data_row["Min Response Time"]     / 1000, 3)
    max_resp     = round(data_row["Max Response Time"]     / 1000, 3)
    rps          = round(data_row["Requests/s"], 2)
    fails_s      = round(data_row["Failures/s"], 2)
    avg_size     = round(data_row["Average Content Size"], 2)

    # Načítaj reachability dáta zo sond  <-- NOVÉ
    reach_reachable, reach_unreachable, reach_df = load_reachability_data(reach_file)

    start_time, end_time, test_type_meta, target_host, target_ip_meta, used_ips = \
        load_test_times(meta_file)

    display_test_type  = test_type if (test_type and test_type.strip()) else test_type_meta
    duration           = compute_duration(start_time, end_time)
    resolved_target_ip = target_ip or target_ip_meta
    if source_ip:
        used_ips = source_ip
    elif used_ips in ("Unknown", "", "nan", None):
        used_ips = "Unknown"

    ip_version = "IPv6" if (source_ip and ":" in source_ip) else "IPv4"

    topology_output = os.path.join(REPORT_DIR, "topology_diagram.png")
    generate_topology_diagram(
        target_ip    = target_ip,
        source_ip    = source_ip,
        interface    = interface,
        output_file  = topology_output,
        reach_src_ip = reach_src_ip
    )

    pdf = SimpleDocTemplate(
        output_file, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN,  bottomMargin=28 * mm
    )

    S = {
        "body":    ParagraphStyle("body",    fontSize=10, textColor=C_TEXT,        leading=15),
        "muted":   ParagraphStyle("muted",   fontSize=9,  textColor=C_TEXT_MUTED,  leading=13),
        "label":   ParagraphStyle("label",   fontSize=10, textColor=C_PRIMARY_DARK,
                                  fontName="Helvetica-Bold"),
        "value":   ParagraphStyle("value",   fontSize=10, textColor=C_TEXT),
        "comment": ParagraphStyle("comment", fontSize=10, textColor=C_TEXT,
                                  leading=15, leftIndent=8, rightIndent=8,
                                  spaceBefore=4, spaceAfter=4,
                                  borderColor=C_PRIMARY, borderWidth=0.8,
                                  borderPadding=10, borderRadius=6,
                                  backColor=C_SURFACE2),
    }

    story     = []
    logo_path = os.path.join(BASE_DIR, "vut_logo.png")

    # ── HERO HEADER ───────────────────────────────────────────────
    story.append(HeroHeader(
        title     = "Locust Load Test Report",
        subtitle  = f"{target_host}  •  {ip_version}  •  {datetime.now().strftime('%d. %m. %Y  %H:%M')}",
        logo_path = logo_path if os.path.exists(logo_path) else None
    ))
    story.append(Spacer(1, 14))

    # ── METRIC CARDS ──────────────────────────────────────────────
    story.append(make_metric_cards([
        ("Requests",     str(req_count),     C_PRIMARY_DARK),
        ("Requests/s",   str(rps),           C_PRIMARY_DARK),
        ("Avg Response", f"{avg_resp} s",    C_PRIMARY),
        ("Duration",     duration,           C_PRIMARY),
        ("Failures",     str(fail_count),    C_DANGER),
        ("Failure Rate", f"{failure_rate}%", C_DANGER),
    ]))
    story.append(Spacer(1, 16))

    # ── TEST INFORMATION ──────────────────────────────────────────
    story.append(ColorBand("  Test Information"))
    story.append(Spacer(1, 8))
    story.append(make_info_table([
        [Paragraph("Test Type",         S["label"]), Paragraph(display_test_type,              S["value"])],
        [Paragraph("Target Host",       S["label"]), Paragraph(str(target_host),               S["value"])],
        [Paragraph("Target IP",         S["label"]), Paragraph(str(resolved_target_ip),        S["value"])],
        [Paragraph("IP Version",        S["label"]), Paragraph(ip_version,                     S["value"])],
        [Paragraph("Start Time",        S["label"]), Paragraph(str(start_time),                S["value"])],
        [Paragraph("End Time",          S["label"]), Paragraph(str(end_time),                  S["value"])],
        [Paragraph("Duration",          S["label"]), Paragraph(duration,                       S["value"])],
        [Paragraph("Used IP range",     S["label"]), Paragraph(str(used_ips),                  S["value"])],
        [Paragraph("IP Pool range",     S["label"]), Paragraph(str(ip_pool_range) if ip_pool_range else str(used_ips), S["value"])],
        [Paragraph("IP Pool count",     S["label"]), Paragraph(str(ip_pool_count) if ip_pool_count else "Unknown", S["value"])],
        [Paragraph("Source ports",      S["label"]), Paragraph(str(src_ports) if src_ports else _get_os_port_range(), S["value"])],
        [Paragraph("Failure threshold", S["label"]), Paragraph(f"{int(reach_threshold*100)}%", S["value"])],
        [Paragraph("Report generated",  S["label"]),
         Paragraph(datetime.now().strftime('%d-%m-%Y  %H:%M:%S'),                            S["value"])],
    ], col_widths=[160, None]))
    story.append(Spacer(1, 14))

    # ── Comment ─────────────────────────────────────────────────
    if comment and comment.strip():
        story.append(ColorBand("  Comment", bg=colors.HexColor("#5F6368")))
        story.append(Spacer(1, 8))
        story.append(Paragraph(comment.replace("\n", "<br/>"), S["comment"]))
        story.append(Spacer(1, 14))

    story.append(PageBreak())

    # ── PERFORMANCE OVERVIEW ──────────────────────────────────────
    story.append(ColorBand("  Performance Overview"))
    story.append(Spacer(1, 8))

    threshold_pct = round(reach_threshold * 100, 1)
    is_stable     = failure_rate <= threshold_pct
    stable_text   = "Stable and reachable" if is_stable else "Unstable / unreachable"
    stable_color  = C_ACCENT if is_stable else C_DANGER

    story.append(make_info_table([
        [Paragraph("Request Count",         S["label"]), Paragraph(str(req_count),      S["value"])],
        [Paragraph("Success Count",         S["label"]), Paragraph(str(success),        S["value"])],
        [Paragraph("Failure Count",         S["label"]), Paragraph(str(fail_count),     S["value"])],
        [Paragraph("Failure Rate",          S["label"]), Paragraph(f"{failure_rate}%",  S["value"])],
        [Paragraph("Failure threshold",     S["label"]), Paragraph(f"{threshold_pct}%", S["value"])],
        [Paragraph("Stable & Reachable",    S["label"]),
         Paragraph(stable_text, ParagraphStyle(
             "stable", fontSize=10, fontName="Helvetica-Bold", textColor=stable_color
         ))],
        [Paragraph("Median Response Time",  S["label"]), Paragraph(f"{median_resp} s",  S["value"])],
        [Paragraph("Average Response Time", S["label"]), Paragraph(f"{avg_resp} s",     S["value"])],
        [Paragraph("Min Response Time",     S["label"]), Paragraph(f"{min_resp} s",     S["value"])],
        [Paragraph("Max Response Time",     S["label"]), Paragraph(f"{max_resp} s",     S["value"])],
        [Paragraph("Requests/s",            S["label"]), Paragraph(str(rps),            S["value"])],
        [Paragraph("Failures/s",            S["label"]), Paragraph(str(fails_s),        S["value"])],
        [Paragraph("Avg Content Size",      S["label"]), Paragraph(f"{avg_size} B",     S["value"])],
    ], col_widths=[200, None]))
    story.append(Spacer(1, 14))
    story.append(PageBreak())
    add_stages_table(story, S, BASE_DIR)
    story.append(PageBreak())

    # ── Failures OVERVIEW ──────────────────────────────────────
    if os.path.exists(FAILURES_FILE):
        fdf = pd.read_csv(FAILURES_FILE)
        if not fdf.empty:
            story.append(ColorBand("Failure Details", bg=C_DANGER))
            story.append(Spacer(1, 8))

            S_cell = ParagraphStyle("fcell", fontSize=8, textColor=C_TEXT, leading=11,
                         wordWrap="CJK")
            S_head = ParagraphStyle("fhead", fontSize=8, textColor=colors.white,
                         fontName="Helvetica-Bold", leading=11)

            rows = [[
                Paragraph("Method",      S_head),
                Paragraph("Endpoint",    S_head),
                Paragraph("Occurrences", S_head),
                Paragraph("Error",       S_head),
            ]]
            for _, row in fdf.iterrows():
                error_text = str(row.get("Error", "")).replace("<", "&lt;").replace(">", "&gt;")
                rows.append([
                    Paragraph(str(row.get("Method", "")),      S_cell),
                    Paragraph(str(row.get("Name",   "")),      S_cell),
                    Paragraph(str(row.get("Occurrences", "")), S_cell),
                    Paragraph(error_text,                      S_cell),
                ])

            t = Table(rows, colWidths=[45, 100, 55, 250])
            t.setStyle(TableStyle([
                ("BACKGROUND",    (0, 0), (-1, 0), C_DANGER),
                ("ROWBACKGROUNDS",(0, 1), (-1,-1), [C_WHITE, C_ROW_ALT]),
                ("GRID",          (0, 0), (-1,-1), 0.4, C_BORDER),
                ("LEFTPADDING",   (0, 0), (-1,-1), 6),
                ("RIGHTPADDING",  (0, 0), (-1,-1), 6),
                ("TOPPADDING",    (0, 0), (-1,-1), 4),
                ("BOTTOMPADDING", (0, 0), (-1,-1), 4),
                ("VALIGN",        (0, 0), (-1,-1), "TOP"),
            ]))
            story.append(t)
            story.append(Spacer(1, 14))
            story.append(PageBreak())

    # ── TOPOLOGY ─────────────────────────────────────────────────
    if os.path.exists(topology_output):
        story.append(ColorBand("  Network Topology"))
        story.append(Spacer(1, 10))
        story.append(Image(topology_output, width=490, height=430))
        story.append(Spacer(1, 6))
        story.append(Paragraph(
            "Network topology showing the test configuration with attack generation, "
            "monitoring (tester), and reachability verification components.",
            S["muted"]
        ))
        story.append(Spacer(1, 16))
        story.append(PageBreak())

    # ── REACHABILITY  (pie chart + timeline)  <-- UPRAVENÉ ────────
    p_pie = os.path.join(REPORT_DIR, "chart_pie.png")
    story.append(ColorBand("  Reachability"))
    story.append(Spacer(1, 10))

    # Použi reachability.csv ak dostupné, inak fallback na Locust stats
    if reach_reachable is not None:
        pie_reachable   = reach_reachable
        pie_unreachable = reach_unreachable
        pie_total       = reach_reachable + reach_unreachable
        pie_source_note = (
            f"Based on {pie_total} reachability probes "
            f"({pie_reachable} reachable, {pie_unreachable} unreachable) — source: reachability.csv"
        )
    else:
        pie_reachable   = success
        pie_unreachable = fail_count
        pie_total       = req_count
        pie_source_note = (
            "reachability.csv not found — fallback to Locust request statistics "
            f"({pie_reachable} success, {pie_unreachable} failures)"
        )

    sizes  = [pie_reachable, pie_unreachable] if pie_total > 0 else [1, 0]
    labels = ["Reachable", "Unreachable"]
    cmap   = ["#34A853", "#EA4335"]

    fig, ax = plt.subplots(figsize=(5, 3.5))
    wedges, _, autotexts = ax.pie(
        sizes, colors=cmap, startangle=90,
        autopct='%1.1f%%', pctdistance=0.75,
        wedgeprops={"edgecolor": "white", "linewidth": 2}
    )
    for i, a in enumerate(autotexts):
        a.set_fontsize(9)
        a.set_text(f"{labels[i]}\n{a.get_text()}")
        a.set_color("white")
        a.set_fontweight("bold")
    ax.set_title("Reachable vs Unreachable", fontsize=11,
                 fontweight="bold", color="#202124")
    fig.patch.set_facecolor("white")
    save_chart(p_pie, dpi=220)
    story.append(Image(p_pie, width=380, height=300))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        pie_source_note,
        ParagraphStyle("src_note", fontSize=8, textColor=C_TEXT_MUTED, alignment=TA_CENTER)
    ))
    story.append(Spacer(1, 10))

    # Timeline a delay graf sond (len ak máme reachability.csv)
    if reach_df is not None:
        add_reachability_delay_chart(reach_df, story, reach_timeout_s=reach_timeout)

    story.append(PageBreak())

    # ── TIME SERIES CHARTS ────────────────────────────────────────
    if os.path.exists(history_file):
        history_df = pd.read_csv(history_file)
        story.append(ColorBand("  Time Series Charts"))
        story.append(Spacer(1, 10))
        add_time_series_charts(history_df, story)

    # ── NETWORK TRAFFIC ───────────────────────────────────────────
    story.append(PageBreak())
    story.append(ColorBand("  Network Traffic Analysis",
                            bg=colors.HexColor("#1558A8")))
    story.append(Spacer(1, 10))
    add_network_traffic_charts(
        network_file, history_file, story,
        failure_threshold=reach_threshold
    )

    # ── BUILD ─────────────────────────────────────────────────────
    pdf.build(story, onFirstPage=_page_template, onLaterPages=_page_template)

    for f in ["chart_pie.png", "chart_rps_failures.png", "chart_response_times.png",
              "chart_users.png", "chart_network_total.png", "chart_network_speed.png",
              "chart_reach_timeline.png", "chart_reach_delay.png", "topology_diagram.png"]:
        full_path = os.path.join(REPORT_DIR, f)
        if os.path.exists(full_path):
            os.remove(full_path)

    print(f"✓ PDF report generated: {output_file}")

    if sign:
        signed_output = output_file.replace(".pdf", "_signed.pdf")
        resolved_p12 = (
            p12_path if (p12_path and os.path.isabs(p12_path))
            else os.path.join(REPORT_DIR, p12_path or "cert.p12")
        )
        try:
            sign_report(output_file, signed_output, resolved_p12, p12_pass)
            if os.path.exists(signed_output):
                os.replace(signed_output, output_file)
                print(f"✓ Signed PDF replaced original: {output_file}")
        except Exception as e:
            print(f"⚠ Signing failed: {e}")


# === MAIN ===
if __name__ == "__main__":
    create_pdf_report(
        stats_file   = STATS_FILE,
        history_file = HISTORY_FILE,
        output_file  = PDF_FILE,
    )

