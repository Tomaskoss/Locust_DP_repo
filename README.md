# Locust Load Test GUI

A Python-based prototype for load testing web services with [Locust](https://locust.io/). The project provides a graphical interface for configuring HTTP/S load tests, generating IP pools, monitoring reachability and network traffic, and exporting PDF reports.

The tool was designed for controlled testing in a local network, typically with one machine acting as the tester and another as the tested server.

---

## Features

- GUI-based configuration of Locust load tests
- HTTP `GET` and `POST` support
- Single or multiple endpoint testing
- IPv4 and IPv6 source IP pool generation
- Optional custom source port configuration
- Multi-stage load scenarios
- Reachability monitoring during the test
- Network traffic monitoring
- PDF report generation
- Optional failure details table in the report
- Optional PDF signing with a `.p12` certificate

---

## Recommended Test Topology

Use two machines in the same local network:

```text
Tester machine  -> runs this project and generates the load
Server machine  -> runs the tested web application
```

Example IPv6 setup:

```text
Tester: fd00:100::72/64
Server: fd00:100::73/64
Target: http://[fd00:100::73]:8080
```

When using IPv6, make sure the tester source IP pool is in the correct network and does not conflict with the server IP address.

---

## Installation

Run the preparation script on the tester machine:

```bash
chmod +x prepare_tester_python.sh
./prepare_tester_python.sh
```

The script installs required system packages, creates the Python virtual environment `locust_env`, installs Python dependencies, and prepares the project directories.

If the virtual environment already exists, activate it manually:

```bash
source locust_env/bin/activate
```

---

## Running the GUI

```bash
source locust_env/bin/activate
python3 locust_gui.py
```

---

## Basic Workflow

1. Open the **Config** tab.
2. Set the target host, endpoint path, network interface, IP version, and IP pool.
3. Click **Setup IP Pool** to add source IP addresses to the selected interface.
4. Open the **HTTP/S** tab.
5. Configure stages, Locust parameters, HTTP method, and optional request body.
6. Click **Start Test**.
7. After the test finishes, open **Generate Report**.
8. Generate the PDF report.
9. Use **Cleanup** after testing to remove the generated IP addresses from the interface.

---

## Target and Endpoints

Target examples:

```text
http://192.168.100.73:8080
http://[fd00:100::73]:8080
```

Endpoint examples:

```text
/
/health
/api/status
```

Multiple endpoints can be entered as comma-separated values:

```text
/,/health,/api/status,/api/products
```

Endpoint paths are normalized automatically. For example, `api/products` becomes `/api/products`.

---

## Test Stages

Each stage defines a load level for a specific duration.

```text
Duration (s) = duration of the current stage only
Users        = number of active users in the stage
Spawn rate   = user spawn rate for the stage
```

Example:

```text
Stage 1: 60 s, 10 users
Stage 2: 120 s, 50 users
Stage 3: 120 s, 100 users
```

Total test duration:

```text
60 + 120 + 120 = 300 s
```

---

## Source Ports

The **Source ports** field is optional.

If it is empty, the operating system assigns ephemeral ports automatically.

Example shown in the report:

```text
OS ephemeral (32768–60999)
```

You can also set a specific port or range:

```text
1025
1024-2000
1025,1026,1027
```

---

## IP Pool

The IP pool defines source IP addresses used by the tester.

Supported modes:

- IPv4 range
- IPv6 range
- IPv6 prefix mode
- Custom IP pool file

Example IPv6 range:

```text
IP start: fd00:100::1000
IP end:   fd00:100::1050
Prefix:   64
```

Avoid using a range that contains the server IP address.

---

## Reachability Monitoring

Reachability monitoring runs during the load test and periodically checks whether the target is reachable.

Configurable parameters:

- source IP
- interface
- interval
- timeout
- failure threshold

Reachability failures are evaluated separately from Locust HTTP request failures.

---

## Generated Files

Common generated files:

```text
data/report_stats.csv
data/report_stats_history.csv
data/report_failures.csv
data/network_usage.csv
data/reachability.csv
data/report_metadata.csv
test_config.csv
ip_pool.txt
port_pool.txt
report/Locust_Report.pdf
```

These files are generated during testing and normally should not be committed to version control.

---

## Recommended `.gitignore`

```gitignore
__pycache__/
*.pyc
locust_env/
venv/
.venv/

data/*.csv
report/*.pdf
report/*.png

test_config.csv
ip_pool.txt
port_pool.txt

*.p12
*.pfx

.vscode/
.idea/
.DS_Store
```

---

## Troubleshooting

### IPv6 `ConnectTimeout`

Check whether the source IP pool and target IP are in the correct IPv6 network.

Incorrect example:

```text
Source IP: fd00::100
Target:    fd00:100::73
```

Correct example:

```text
Source IP: fd00:100::1000
Target:    fd00:100::73
```

### Link-local IPv6

For link-local IPv6 addresses, include the interface scope in the URL.

Example:

```text
http://[fe80::20c:29ff:fe7e:a4b0%25ens33]:8080
```

### Empty source ports shown as `nan`

An empty source ports field means the OS uses ephemeral ports. The report should show the OS ephemeral range, not `nan`.

---

## Notes

- Run **Cleanup** after testing to remove generated IP addresses from the interface.
- Do not commit private certificates such as `.p12` or `.pfx` files.
- For realistic testing, use a separate tester and server machine in the same local network.
