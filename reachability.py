import requests
import time
import csv
from requests.adapters import HTTPAdapter

# -------------------------------
# Konfigurácia
# -------------------------------
SOURCE_IP = "10.10.10.20"       # tvoja alias IP
URL = "https://www.vut.cz"      # server na testovanie
CSV_FILE = "reachability.csv"   # výstupný súbor
INTERVAL = 5                    # čas medzi checkmi v sekundách
DURATION = 10                  # trvanie testu v sekundách (napr. 300 = 5 minút)

# Adapter na konkrétnu IP
class SourceIPAdapter(HTTPAdapter):
    def __init__(self, source_ip, **kwargs):
        self.source_ip = source_ip
        super().__init__(**kwargs)

    def init_poolmanager(self, *args, **kwargs):
        kwargs['source_address'] = (self.source_ip, 0)
        return super().init_poolmanager(*args, **kwargs)

# -------------------------------
# Hlavný loop
# -------------------------------
session = requests.Session()
session.mount("http://", SourceIPAdapter(SOURCE_IP))
session.mount("https://", SourceIPAdapter(SOURCE_IP))

# Otvorenie CSV súboru a zápis hlavičky
with open(CSV_FILE, mode="w", newline="") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["timestamp", "status_code", "elapsed_time_s"])

    start_time = time.time()  # začiatok testu

    try:
        while time.time() - start_time < DURATION:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            try:
                r = session.get(URL, timeout=5)
                status = r.status_code
                elapsed = r.elapsed.total_seconds()
            except Exception as e:
                status = "FAIL"
                elapsed = -1
            writer.writerow([timestamp, status, elapsed])
            csvfile.flush()
            print(timestamp, status, elapsed)
            time.sleep(INTERVAL)
    except KeyboardInterrupt:
        print("Reachability check stopped by user.")

