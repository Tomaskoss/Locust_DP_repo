import ipaddress
import subprocess
import os

# ---- KONFIGURÁCIA ----
IP_RANGE_START = "192.168.10.10"
IP_RANGE_END   = "192.168.10.40"
INTERFACE = "ens33"
POOL_FILE = "ip_pool.txt"
# -----------------------


def generate_ip_range(start_ip, end_ip):
    start = ipaddress.IPv4Address(start_ip)
    end = ipaddress.IPv4Address(end_ip)
    return [str(ipaddress.IPv4Address(i)) for i in range(int(start), int(end) + 1)]


def remove_ip_from_interface(ip, interface):
    cmd = ["sudo", "ip", "addr", "del", f"{ip}/32", "dev", interface]
    try:
        subprocess.run(cmd, check=True)
        print(f"[OK] Removed {ip} from {interface}")
    except subprocess.CalledProcessError:
        print(f"[WARN] Could not remove {ip} (maybe not present?)")


def main():
    print("Generating IP range to remove...")
    ip_list = generate_ip_range(IP_RANGE_START, IP_RANGE_END)

    print(f"Removing IPs from interface {INTERFACE}...")
    for ip in ip_list:
        remove_ip_from_interface(ip, INTERFACE)

    # --- Remove pool file ---
    if os.path.exists(POOL_FILE):
        try:
            os.remove(POOL_FILE)
            print(f"[OK] Deleted file {POOL_FILE}")
        except Exception as e:
            print(f"[WARN] Could not delete {POOL_FILE}: {e}")
    else:
        print(f"[INFO] File {POOL_FILE} does not exist, nothing to delete.")

    print("DONE.")


if __name__ == "__main__":
    main()

