#!/usr/bin/env python3
import os
import sys  # ADD THIS - needed for sys.executable
import subprocess  # ADD THIS - needed for subprocess.run()
import pandas as pd
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image,PageBreak
from datetime import datetime


# === CONFIGURATION ===
STATS_FILE = "report_stats.csv"
HISTORY_FILE = "report_stats_history.csv"
NETWORK_FILE = "network_usage.csv"
PDF_FILE = "Locust_Report.pdf"
META_FILE = "report_metadata.csv"
TOPOLOGY_SCRIPT = "create_topology.py"
topology_file = "topology_diagram.png"
# === HELPER FUNCTIONS ===

def generate_topology_diagram():
    """
    Call external create_topology.py script to generate topology diagram
    Returns: True if successful, False otherwise
    """
    print("Generating network topology diagram...")
    
    # Check if create_topology.py exists
    if not os.path.exists(TOPOLOGY_SCRIPT):
        print(f"Warning: {TOPOLOGY_SCRIPT} not found, skipping topology generation")
        return False
    
    try:
        # Call the topology generator script
        result = subprocess.run(
            [sys.executable, TOPOLOGY_SCRIPT],  # Uses same Python interpreter
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("✓ Topology diagram generated successfully")
            if result.stdout:
                print(result.stdout.strip())
            return True
        else:
            print(f"✗ Failed to generate topology diagram")
            if result.stderr:
                print(f"Error: {result.stderr.strip()}")
            return False
            
    except subprocess.TimeoutExpired:
        print("✗ Topology generation timed out")
        return False
    except Exception as e:
        print(f"✗ Error calling topology generator: {e}")
        return False


def load_test_times(meta_path):
    if os.path.exists(meta_path):
        try:
            df = pd.read_csv(meta_path)
            start_time_raw = str(df.iloc[0].get("start_time", "Unknown"))
            end_time_raw = str(df.iloc[0].get("end_time", "Unknown"))
            test_type = str(df.iloc[0].get("test_type", "Unknown"))
            target_host = str(df.iloc[0].get("target_host", "Unknown"))
            target_ip = str(df.iloc[0].get("target_ip", "Unknown"))
            used_ips = str(df.iloc[0].get("used_ips", "Unknown"))
            try:
                start_time = datetime.fromisoformat(start_time_raw).strftime("%H:%M:%S")
                end_time = datetime.fromisoformat(end_time_raw).strftime("%H:%M:%S")
            except Exception:
                start_time = start_time_raw
                end_time = end_time_raw
            return start_time, end_time, test_type, target_host, target_ip, used_ips
        except Exception as e:
            print(f"Failed to load {meta_path}: {e}")
    return "Unknown", "Unknown", "Unknown", "Unknown", "Unknown", "Unknown"

def compute_duration(start_str, end_str):
    try:
        start_dt = datetime.strptime(start_str, "%H:%M:%S")
        end_dt = datetime.strptime(end_str, "%H:%M:%S")
        delta = end_dt - start_dt
        if delta.total_seconds() < 0:
            delta = (datetime.combine(datetime.today(), end_dt.time()) -
                     datetime.combine(datetime.today(), start_dt.time()))
        total_seconds = delta.total_seconds()
        minutes, seconds = divmod(total_seconds, 60)
        if minutes >= 1:
            return f"{int(minutes)} min {seconds:.3f} s"
        else:
            return f"{seconds:.3f} s"
    except Exception:
        return "Unknown"


# === CHART FUNCTIONS ===
def add_time_series_charts(history_df, story, styles):
    if 'Timestamp' not in history_df.columns:
        print("CSV missing 'Timestamp' column, charts skipped")
        return

    history_df['Timestamp'] = pd.to_datetime(history_df['Timestamp'], unit='s')

    # --- Total Requests per Second ---
    plt.figure(figsize=(6, 3))
    plt.plot(history_df['Timestamp'], history_df['Requests/s'], label='Requests/s', color='green')
    plt.plot(history_df['Timestamp'], history_df['Failures/s'], label='Failures/s', color='red')
    plt.xlabel('Time')
    plt.ylabel('Requests/s')
    plt.title('Requests per Second Over Time')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    chart_path = "chart_rps_failures.png"
    plt.savefig(chart_path, dpi=200)
    plt.close()
    story.append(Image(chart_path, width=400, height=250))
    story.append(Spacer(1, 12))

    # --- Response Times ---
    plt.figure(figsize=(6, 3))
    plt.plot(history_df['Timestamp'], history_df['Total Min Response Time']/1000, label='Min', linestyle='--', color='green')
    plt.plot(history_df['Timestamp'], history_df['Total Median Response Time']/1000, label='Median', linestyle='-', color='orange')
    plt.plot(history_df['Timestamp'], history_df['Total Max Response Time']/1000, label='Max', linestyle='-.', color='red')
    plt.xlabel('Time')
    plt.ylabel('Response Time (s)')
    plt.title('Response Times Over Time')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    chart_path = "chart_response_times.png"
    plt.savefig(chart_path, dpi=200)
    plt.close()
    story.append(Image(chart_path, width=400, height=250))
    story.append(Spacer(1, 12))

    # --- Number of Users ---
    if 'User Count' in history_df.columns:
        plt.figure(figsize=(6, 3))
        plt.plot(history_df['Timestamp'], history_df['User Count'], label='Users', color='purple')
        plt.xlabel('Time')
        plt.ylabel('Number of Users')
        plt.title('Number of Users Over Time')
        plt.grid(True)
        plt.tight_layout()
        chart_path = "chart_users.png"
        plt.savefig(chart_path, dpi=200)
        plt.close()
        story.append(Image(chart_path, width=400, height=250))
        story.append(Spacer(1, 12))


# === NETWORK TRAFFIC + NEW TABLES ===
def add_network_traffic_charts(network_file, history_file, story, styles):
    if not os.path.exists(network_file):
        print(f"Network file '{network_file}' not found, charts skipped")
        return

    try:
        network_df = pd.read_csv(network_file)
        network_df['timestamp'] = pd.to_datetime(network_df['timestamp'], unit='s')

        unreachable_timestamps = []
        if os.path.exists(history_file):
            try:
                history_df = pd.read_csv(history_file)
                history_df['Timestamp'] = pd.to_datetime(history_df['Timestamp'], unit='s')
                if 'Failures/s' in history_df.columns and 'Requests/s' in history_df.columns:
                    for idx, row in history_df.iterrows():
                        if row['Requests/s'] > 0 and (row['Failures/s']/row['Requests/s']) > 0.5:
                            unreachable_timestamps.append(row['Timestamp'])
            except Exception as e:
                print(f"Warning: Could not process failure data: {e}")

        # --- Total RX/TX MB chart ---
        rx_mb = network_df['rx_total'] / (1024 * 1024)
        tx_mb = network_df['tx_total'] / (1024 * 1024)
        fig, ax1 = plt.subplots(figsize=(6,3))
        ax1.plot(network_df['timestamp'], rx_mb, color='blue', label='RX MB')
        ax1.set_xlabel('Time')
        ax1.set_ylabel('Received MB', color='blue')
        ax2 = ax1.twinx()
        ax2.plot(network_df['timestamp'], tx_mb, color='purple', label='TX MB')
        ax2.set_ylabel('Transmitted MB', color='purple')
        ax1.set_title('Total Network Traffic (Cumulative)')
        for ts in unreachable_timestamps:
            ax1.axvline(x=ts, color='red', alpha=0.3, linewidth=0.5)
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
        plt.tight_layout()
        chart_path = "chart_network_total.png"
        plt.savefig(chart_path, dpi=200)
        plt.close()
        story.append(Image(chart_path, width=400, height=250))
        story.append(Spacer(1,12))

        # --- Transfer Speed chart ---
        fig, ax = plt.subplots(figsize=(6,3))
        ax.plot(network_df['timestamp'], network_df['rx_kbps'], color='blue', label='RX kB/s')
        ax.plot(network_df['timestamp'], network_df['tx_kbps'], color='purple', label='TX kB/s')
        for ts in unreachable_timestamps:
            ax.axvline(x=ts, color='red', alpha=0.3, linewidth=0.5)
        ax.set_xlabel('Time')
        ax.set_ylabel('Speed (kB/s)')
        ax.set_title('Network Transfer Speed')
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        chart_path = "chart_network_speed.png"
        plt.savefig(chart_path, dpi=200)
        plt.close()
        story.append(Image(chart_path, width=400, height=250))
        story.append(Spacer(1,12))

        # Calculate differences from initial values
        rx_total_kb = (network_df['rx_total'] - network_df['rx_total'].iloc[0]) / 1024
        tx_total_kb = (network_df['tx_total'] - network_df['tx_total'].iloc[0]) / 1024

        # Exclude the first row (which is 0) for min/max/avg calculations
        rx_total_kb_nonzero = rx_total_kb.iloc[1:]  # Skip first row
        tx_total_kb_nonzero = tx_total_kb.iloc[1:]  # Skip first row

        rx_total_min = rx_total_kb_nonzero.min() if len(rx_total_kb_nonzero) > 0 else 0
        rx_total_max = rx_total_kb_nonzero.max() if len(rx_total_kb_nonzero) > 0 else 0
        rx_total_avg = rx_total_kb_nonzero.mean() if len(rx_total_kb_nonzero) > 0 else 0

        tx_total_min = tx_total_kb_nonzero.min() if len(tx_total_kb_nonzero) > 0 else 0
        tx_total_max = tx_total_kb_nonzero.max() if len(tx_total_kb_nonzero) > 0 else 0
        tx_total_avg = tx_total_kb_nonzero.mean() if len(tx_total_kb_nonzero) > 0 else 0

        # For speed, filter out zero values
        rx_speed_nonzero = network_df[network_df['rx_kbps'] > 0]['rx_kbps']
        tx_speed_nonzero = network_df[network_df['tx_kbps'] > 0]['tx_kbps']

        rx_speed_min = rx_speed_nonzero.min() if len(rx_speed_nonzero) > 0 else 0
        rx_speed_max = rx_speed_nonzero.max() if len(rx_speed_nonzero) > 0 else 0
        rx_speed_avg = rx_speed_nonzero.mean() if len(rx_speed_nonzero) > 0 else 0

        tx_speed_min = tx_speed_nonzero.min() if len(tx_speed_nonzero) > 0 else 0
        tx_speed_max = tx_speed_nonzero.max() if len(tx_speed_nonzero) > 0 else 0
        tx_speed_avg = tx_speed_nonzero.mean() if len(tx_speed_nonzero) > 0 else 0

        # helper to build small tables with consistent top alignment
        def build_table(title, rows, color):
            table = Table(
                [[title, "Value"]] + rows,
                colWidths=[130, 110]
            )
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(color)),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                # ensure inner table content aligns to top so grid cells line up
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]))
            return table

        tx_total_table = build_table(
            "TX Total [kB]",
            [
                ["Min", f"{tx_total_min:.2f}"],
                ["Max", f"{tx_total_max:.2f}"],
                ["Average", f"{tx_total_avg:.2f}"],
            ],
            "#9B59B6"
        )

        tx_speed_table = build_table(
            "TX [kB/s]",
            [
                ["Min", f"{tx_speed_min:.2f}"],
                ["Max", f"{tx_speed_max:.2f}"],
                ["Average", f"{tx_speed_avg:.2f}"],
            ],
            "#8E44AD"
        )

        rx_total_table = build_table(
            "RX Total [kB]",
            [
                ["Min", f"{rx_total_min:.2f}"],
                ["Max", f"{rx_total_max:.2f}"],
                ["Average", f"{rx_total_avg:.2f}"],
            ],
            "#4A90E2"
        )

        rx_speed_table = build_table(
            "RX [kB/s]",
            [
                ["Min", f"{rx_speed_min:.2f}"],
                ["Max", f"{rx_speed_max:.2f}"],
                ["Average", f"{rx_speed_avg:.2f}"],
            ],
            "#357ABD"
        )

        story.append(Paragraph("<b>Network Traffic Statistics</b>", styles["Heading2"]))
        story.append(Spacer(1,6))

        # 2x2 grid layout - ensure top alignment on parent table too
        grid = Table(
            [
                [tx_total_table, tx_speed_table],
                [rx_total_table, rx_speed_table]
            ],
            colWidths=[250, 250]
        )

        grid.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))

        story.append(grid)
        story.append(Spacer(1, 12))

    except Exception as e:
        print(f"Error creating network traffic charts: {e}")
        story.append(Paragraph(f"<font color='red'>Error creating network charts: {e}</font>", styles["Normal"]))
        story.append(Spacer(1,12))


# === PDF GENERATION ===

def create_pdf_report(stats_file, history_file, output_file):
    if not os.path.exists(stats_file):
        print(f"CSV file '{stats_file}' not found.")
        return

    stats_df = pd.read_csv(stats_file)
    valid_rows = stats_df[stats_df["Type"].notna()]
    if valid_rows.empty:
        print("Stats CSV has no valid rows.")
        return

    data_row = valid_rows.iloc[0]

    req_count = int(data_row["Request Count"])
    fail_count = int(data_row["Failure Count"])
    failure_rate = round((fail_count / req_count) * 100, 2) if req_count > 0 else 0
    avg_resp = round(data_row["Average Response Time"]/1000,3)
    median_resp = round(data_row["Median Response Time"]/1000,3)
    min_resp = round(data_row["Min Response Time"]/1000,3)
    max_resp = round(data_row["Max Response Time"]/1000,3)
    rps = round(data_row["Requests/s"],2)
    fails_s = round(data_row["Failures/s"],2)
    avg_size = round(data_row["Average Content Size"],2)

    start_time, end_time, test_type, target_host, target_ip, used_ips = load_test_times(META_FILE)
    duration = compute_duration(start_time, end_time)

    pdf = SimpleDocTemplate(output_file, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    wrap_style = ParagraphStyle(name='wrap', fontSize=10)
     # === GENERATE NETWORK TOPOLOGY ===
    topology_generated = generate_topology_diagram()  # ADD THIS LINE - calls the generator
    
    
     # --- PRIDANIE OBRAZKU NA ZAČIATOK ---
    logo_path = "vut_logo.png"  # <-- sem daj cestu k svojmu obrázku
    if os.path.exists(logo_path):
        story.append(Image(logo_path, width=200, height=100))
        story.append(Spacer(1,12))
    else:
        print(f"Logo '{logo_path}' not found, skipping image.")

    # Info Table
    info_data = [
        [Paragraph("Test Type", wrap_style), Paragraph(str(test_type), wrap_style)],
        [Paragraph("Target", wrap_style), Paragraph(f"{target_host} ({target_ip})", wrap_style)],
        [Paragraph("Start Time", wrap_style), Paragraph(str(start_time), wrap_style)],
        [Paragraph("End Time", wrap_style), Paragraph(str(end_time), wrap_style)],
        [Paragraph("Report generated", wrap_style), Paragraph(datetime.now().strftime('%d-%m-%Y %H:%M:%S'), wrap_style)]
    ]
    info_table = Table(info_data, colWidths=[None,None])
    info_table.setStyle(TableStyle([
        ("ALIGN",(0,0),(0,-1),"LEFT"),
        ("ALIGN",(1,0),(1,-1),"RIGHT"),
        ("GRID",(0,0),(-1,-1),0.5,colors.black),
        ("FONTNAME",(0,0),(0,-1),"Helvetica-Bold"),
    ]))
    story.append(Paragraph("<b>Test Information</b>", styles["Heading1"]))
    story.append(Paragraph("Testing performed with Locust framework on virtual Ubuntu machine.", styles["Normal"]))
    story.append(Spacer(1,12))
    story.append(info_table)
    story.append(Spacer(1,12))

    # Overview Table
    overview_data = [
        [Paragraph("Metric", wrap_style), Paragraph("Value", wrap_style)],
        [Paragraph("Time", wrap_style), Paragraph(duration, wrap_style)],
        [Paragraph("Request Count", wrap_style), Paragraph(str(req_count), wrap_style)],
        [Paragraph("Failure Count", wrap_style), Paragraph(str(fail_count), wrap_style)],
        [Paragraph("Failure Rate", wrap_style), Paragraph(f"{failure_rate}%", wrap_style)],
        [Paragraph("Median Response Time", wrap_style), Paragraph(f"{median_resp} s", wrap_style)],
        [Paragraph("Average Response Time", wrap_style), Paragraph(f"{avg_resp} s", wrap_style)],
        [Paragraph("Min Response Time", wrap_style), Paragraph(f"{min_resp} s", wrap_style)],
        [Paragraph("Max Response Time", wrap_style), Paragraph(f"{max_resp} s", wrap_style)],
        [Paragraph("Requests/s", wrap_style), Paragraph(str(rps), wrap_style)],
        [Paragraph("Failures/s", wrap_style), Paragraph(str(fails_s), wrap_style)],
        [Paragraph("Average Content Size", wrap_style), Paragraph(f"{avg_size} B", wrap_style)]
    ]
    overview_table = Table(overview_data, colWidths=[None,None])
    overview_table.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(0,0),colors.grey),
        ("TEXTCOLOR",(0,0),(-1,0),colors.whitesmoke),
        ("ALIGN",(0,0),(0,-1),"LEFT"),
        ("ALIGN",(1,0),(1,-1),"RIGHT"),
        ("GRID",(0,0),(-1,-1),0.5,colors.black),
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
    ]))
    story.append(Paragraph("<b>Overview of Testing</b>", styles["Heading1"]))
    story.append(overview_table)
    story.append(Spacer(1,12))
    story.append(PageBreak())
    
    
    # Add Network Topology section
    topology_file = "topology_diagram.png"
    if os.path.exists(topology_file):
        story.append(Paragraph("<b>Network Topology</b>", styles["Heading1"]))
        story.append(Spacer(1, 6))
        story.append(Image(topology_file, width=450, height=360))
        story.append(Spacer(1, 12))
        story.append(Paragraph(
            "Network topology showing the test configuration with attack generation, "
            "monitoring (tester), and reachability verification components.",
            styles["Normal"]
        ))
        story.append(Spacer(1, 12))
    else:
        print(f"Warning: {topology_file} not found, skipping topology section")
    

    # Pie Chart
    success_count = req_count - fail_count
    if req_count > 0:
        sizes = [success_count, fail_count]
    else:
        sizes = [0,0]
    labels = ["Reachable","Unreachable"]
    chart_colors = ["#0ecc16","#F44336"]
    plt.figure(figsize=(4,3))
    wedges,texts,autotexts = plt.pie(sizes, labels=None, colors=chart_colors,
                                     startangle=90, autopct='%1.1f%%', pctdistance=0.7,
                                     textprops={'color':'black','fontsize':8})
    for i,a in enumerate(autotexts):
        a.set_text(f"{labels[i]}\n{a.get_text()}")
    plt.title("Reachable vs Unreachable Requests", weight='bold')
    chart_path = "chart_pie.png"
    plt.savefig(chart_path,bbox_inches="tight", dpi=300)
    plt.close()
    story.append(Image(chart_path,width=350,height=300))
    story.append(Spacer(1,12))
    story.append(Paragraph("Percentage of reachable (success) vs unreachable (failed) requests.", styles["Normal"]))
    story.append(Spacer(1,12))
    
    # Summary
    if failure_rate > 3:
        summary = "<font color='red'><b>Warning:</b></font> High failure rate detected — target may be unstable."
    else:
        summary = "<font color='green'><b>OK:</b></font> Target stable and reachable."
    story.append(Paragraph("Reachability / Performance Summary",
    styles["Heading2"]))
    story.append(Paragraph(summary, styles["Normal"]))
    story.append(Spacer(1, 12))
    # Time Series Charts
    if os.path.exists(history_file):
        history_df = pd.read_csv(history_file)
        story.append(Paragraph("<b>Time Series Charts</b>", styles["Heading1"]))
        add_time_series_charts(history_df, story, styles)
    else:
        print(f"CSV '{history_file}' not found, time series charts skipped.")

    # Network Traffic Analysis (includes new tables)
    story.append(PageBreak())
    story.append(Paragraph("<b>Network Traffic Analysis</b>", styles["Heading1"]))
    add_network_traffic_charts(NETWORK_FILE, history_file, story, styles)

    

    pdf.build(story)

    # Cleanup
    for f in ["chart_pie.png","chart_rps_failures.png","chart_response_times.png","chart_users.png",
              "chart_network_total.png","chart_network_speed.png"]:
        if os.path.exists(f):
            os.remove(f)

    print(f"PDF report generated: {output_file}")


# === MAIN ===
if __name__ == "__main__":
    create_pdf_report(STATS_FILE, HISTORY_FILE, PDF_FILE)

