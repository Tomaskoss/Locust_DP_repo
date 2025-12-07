from locust import HttpUser, task, events
from datetime import datetime
import socket
import csv
import random
TEST_TYPE = "Load Test"  # 🔸 Tu si nastavíš typ testu

@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    global start_time, target_host, target_ip
    start_time = datetime.now()

    # host priamo z CLI (-H alebo --host)
    target_host = environment.host or "Unknown"

    # Získaj IP adresu danej domény
    try:
        # odstráň https:// alebo http:// a prípadné cesty
        clean_host = target_host.replace("https://", "").replace("http://", "").split("/")[0]
        target_ip = socket.gethostbyname(clean_host)
    except Exception:
        target_ip = "Unknown"

    print(f" Test started at: {start_time}")
    print(f" Target: {target_host} ({target_ip})")

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    global end_time
    end_time = datetime.now()
    print(f"Test ended at: {end_time}")

  # Získaj všetky použité IP adresy
    used_ips = sorted(list(getattr(environment, "used_ips", [])))
    used_ips_str = ", ".join(used_ips)

    # Zapíš čas + typ testu + target host a IP do CSV
    with open("report_metadata.csv", "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["start_time", "end_time", "test_type", "target_host", "target_ip","used_ips"])
        writer.writerow([start_time, end_time, TEST_TYPE, target_host, target_ip, used_ips_str])

def load_ip_pool():
    with open("ip_pool.txt") as f:
        return [line.strip() for line in f.readlines()]

class MyUser(HttpUser):
    def on_start(self):
        self.ip_pool = load_ip_pool()
        self.source_ip = random.choice(self.ip_pool)
        self.client._transport_kwargs = {
            "source_address": (self.source_ip, 0)
        }
# Ulož do environment pre neskorší export
        if not hasattr(self.environment, "used_ips"):
            self.environment.used_ips = set()
        self.environment.used_ips.add(self.source_ip)
    @task
    def index(self):
        self.client.get("/")

        
