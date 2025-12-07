import os
import pandas as pd
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from datetime import datetime

# === CONFIGURATION ===
STATS_FILE = "report_stats.csv"            # agregované dáta
HISTORY_FILE = "report_stats_history.csv"  # časové dáta
PDF_FILE = "Locust_Report.pdf"
META_FILE = "report_metadata.csv"          # info o teste

# === HELPER FUNCTIONS ===

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
            print(f" Nepodarilo sa načítať {meta_path}: {e}")
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
    """Pridá tri grafy: Total RPS + Failures, Response Times, Number of Users"""
    if 'Timestamp' not in history_df.columns:
        print("CSV nemá 'Timestamp' stĺpec, grafy nebudú vytvorené")
        return

    # Konvertuj Unix timestamp na datetime
    history_df['Timestamp'] = pd.to_datetime(history_df['Timestamp'], unit='s')

    # --- Graf 1: Total Requests per Second ---
    plt.figure(figsize=(6, 3))
    plt.plot(history_df['Timestamp'], history_df['Requests/s'], label='Requests/s', color='green')
    plt.plot(history_df['Timestamp'], history_df['Failures/s'], label='Failures/s', color='red')
    plt.xlabel('Time')
    plt.ylabel('Requests/s')
    plt.title('Total Requests per Second')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    chart_path = "chart_rps_failures.png"
    plt.savefig(chart_path, dpi=200)
    plt.close()
    story.append(Image(chart_path, width=400, height=250))
    story.append(Spacer(1, 12))

    # --- Graf 2: Response Times ---
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

    # --- Graf 3: Number of Users ---
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

# === PDF GENERATION ===

def create_pdf_report(stats_file, history_file, output_file):
    if not os.path.exists(stats_file):
        print(f"CSV file '{stats_file}' not found.")
        return

    stats_df = pd.read_csv(stats_file)
    data_row = stats_df[stats_df["Type"].notna()].iloc[0]

    # === BASIC METRICS ===
    req_count = int(data_row["Request Count"])
    fail_count = int(data_row["Failure Count"])
    failure_rate = round((fail_count / req_count) * 100, 2) if req_count > 0 else 0
    avg_resp = round(data_row["Average Response Time"]/1000, 3)
    median_resp = round(data_row["Median Response Time"]/1000, 3)
    min_resp = round(data_row["Min Response Time"]/1000, 3)
    max_resp = round(data_row["Max Response Time"]/1000, 3)
    rps = round(data_row["Requests/s"], 2)
    fails_s = round(data_row["Failures/s"], 2)
    avg_size = round(data_row["Average Content Size"], 2)

    # === LOAD START / END TIME ===
    start_time, end_time, test_type, target_host, target_ip, used_ips  = load_test_times(META_FILE)
    duration = compute_duration(start_time, end_time)

    # === PDF DOCUMENT ===
    pdf = SimpleDocTemplate(output_file, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    # Info Table
    info_data = [
        ["Test Type", test_type],
        ["Target", f"{target_host} ({target_ip})"],
        ["Start Time", start_time],
        ["End Time", end_time],
        ["Report generated", datetime.now().strftime('%d-%m-%Y %H:%M:%S')]
    ]
    info_table = Table(info_data, colWidths=[150, 350])
    info_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
    ]))
    story.append(Paragraph("<b>Test Information</b>", styles["Heading1"]))
    story.append(Paragraph("For this testing was used Locust framework on virtual station running ubuntu", styles["Normal"]))
    story.append(Spacer(1, 12))
    story.append(info_table)
    story.append(Spacer(1, 12))

    # Overview table
    overview_data = [
        ["Metric", "Value"],
        ["Time", duration],
        ["Request Count", req_count],
        ["Failure Count", fail_count],
        ["Failure Rate", f"{failure_rate}%"],
        ["Median Response Time", f"{median_resp} s"],
        ["Average Response Time", f"{avg_resp} s"],
        ["Min Response Time", f"{min_resp} s"],
        ["Max Response Time", f"{max_resp} s"],
        ["Requests/s", rps],
        ["Failures/s", fails_s],
        ["Average Content Size", f"{avg_size} B"]
    ]
    overview_table = Table(overview_data, colWidths=[200, 200])
    overview_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ]))
    story.append(Paragraph("<b>Overview of testing</b>", styles["Heading1"]))
    story.append(overview_table)
    story.append(Spacer(1, 12))

    # Pie chart
    success_count = req_count - fail_count
    labels = ["Reachable", "Unreachable"]
    sizes = [success_count, fail_count]
    chart_colors = ["#0ecc16", "#F44336"]
    plt.figure(figsize=(4, 3))
    wedges, texts, autotexts = plt.pie(
        sizes, labels=None, colors=chart_colors,
        startangle=90, autopct='%1.1f%%', pctdistance=0.7,
        textprops={'color': 'black', 'fontsize': 8}
    )
    for i, a in enumerate(autotexts):
        a.set_text(f"{labels[i]}\n{a.get_text()}")
    plt.title("Reachable vs Unreachable Requests")
    chart_path = "chart_pie.png"
    plt.savefig(chart_path, bbox_inches="tight", dpi=300)
    plt.close()
    story.append(Image(chart_path, width=350, height=300))
    story.append(Spacer(1, 12))
    story.append(Paragraph(
        "This pie chart shows the percentage of reachable (successful) and unreachable (failed) requests.",
        styles["Normal"]
    ))
    story.append(Spacer(1, 12))

    # Time series charts
    if os.path.exists(history_file):
        history_df = pd.read_csv(history_file)
        story.append(Paragraph("<b>Time Series Charts</b>", styles["Heading1"]))
        add_time_series_charts(history_df, story, styles)
    else:
        print(f"CSV file '{history_file}' not found, time series charts will not be created.")

    # Summary
    if failure_rate > req_count/100*3:
        summary = "<font color='red'><b>Warning:</b></font> High failure rate detected — target may be unstable."
    else:
        summary = "<font color='green'><b>OK:</b></font> Target stable and reachable."
    story.append(Paragraph("<b>Reachability / Performance Summary</b>", styles["Heading2"]))
    story.append(Paragraph(summary, styles["Normal"]))

    pdf.build(story)

    # Cleanup temporary images
    for f in ["chart_pie.png", "chart_rps.png", "chart_resp_time.png", "chart_users.png"]:
        if os.path.exists(f):
            os.remove(f)

    print(f"PDF report generated: {output_file}")

# === MAIN ===
if __name__ == "__main__":
    create_pdf_report(STATS_FILE, HISTORY_FILE, PDF_FILE)

