from locust import events, HttpUser, task, between
from datetime import datetime
import subprocess
import socket
import csv
import random
from requests.adapters import HTTPAdapter

# --- Konštanty ---
TEST_TYPE = "Locust Load Test"

# --- Globálne premenne ---
start_time = None
target_host = None
target_ip = None
network_proc = None

# --- Test start ---
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    global start_time, target_host, target_ip
    start_time = datetime.now()
    target_host = environment.host or "Unknown"

    try:
        clean_host = target_host.replace("https://", "").replace("http://", "").split("/")[0]
        target_ip = socket.gethostbyname(clean_host)
    except Exception:
        target_ip = "Unknown"

    print(f"Test started at: {start_time}")
    print(f"Target: {target_host} ({target_ip})")
    
    
    
    
# --- Spustenie reachability skriptu pri štarte testu ---
reachability_proc = None

#@events.test_start.add_listener
#def start_reachability(environment, **kwargs):
#    global reachability_proc
#    print("Starting reachability script...")
    # cesta k tvojmu skriptu
#    reachability_proc = subprocess.Popen(["python3", "reachability.py"])
#@events.test_stop.add_listener
#def stop_reachability(environment, **kwargs):#
#    global reachability_proc
#    if reachability_proc:
 #       print("Stopping reachability script...")
 #       reachability_proc.terminate()


# --- Test stop ---
@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    end_time = datetime.now()
    print(f"Test ended at: {end_time}")

    # zapis do CSV
    with open("report_metadata.csv", "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["start_time", "end_time", "test_type", "target_host", "target_ip"])
        writer.writerow([start_time, end_time, TEST_TYPE, environment.host, target_ip])

# --- Adapter na source IP ---
class SourceIPAdapter(HTTPAdapter):
    def __init__(self, source_ip, **kwargs):
        self.source_ip = source_ip
        super().__init__(**kwargs)

    def init_poolmanager(self, *args, **kwargs):
        kwargs['source_address'] = (self.source_ip, 0)
        return super().init_poolmanager(*args, **kwargs)

# --- Load IP pool ---
def load_ip_pool():
    with open("ip_pool.txt") as f:
        return [line.strip() for line in f.readlines()]

# --- User class ---
class MyUser(HttpUser):
    ip_pool = load_ip_pool()
    wait_time = between(1,2)

    def on_start(self):
        

        self.source_ip = random.choice(self.ip_pool)
        print(f"User {self} uses source IP {self.source_ip}")
        adapter = SourceIPAdapter(self.source_ip)
        self.client.mount("http://", SourceIPAdapter(self.source_ip))
        self.client.mount("https://", SourceIPAdapter(self.source_ip))
     
    @task
    def index(self):
        self.client.get("/")

