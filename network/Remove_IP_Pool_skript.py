import ipaddress
import subprocess
import argparse
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---- DEFAULT KONFIGURÁCIA ----
IP_RANGE_START = "192.168.10.10"
IP_RANGE_END   = "192.168.10.40"
INTERFACE      = "ens33"
POOL_FILE      = os.path.join(BASE_DIR, "ip_pool.txt")
# ------------------------------

def generate_ip_range(start_ip, end_ip):
    start = ipaddress.IPv4Address(start_ip)
    end   = ipaddress.IPv4Address(end_ip)
    return [str(ipaddress.IPv4Address(i)) for i in range(int(start), int(end) + 1)]

def remove_ip_from_interface(ip, interface):
    cmd = ["sudo", "ip", "addr", "del", f"{ip}/32", "dev", interface]
    try:
        subprocess.run(cmd, check=True)
        print(f"[OK] Removed {ip} from {interface}")
    except subprocess.CalledProcessError:
        print(f"[WARN] Could not remove {ip} (maybe not present?)")

def main(
    ip_start=IP_RANGE_START,
    ip_end=IP_RANGE_END,
    interface=INTERFACE,
    pool_file=POOL_FILE
):
    print(f"Generating IP range {ip_start} - {ip_end} to remove...")
    ip_list = generate_ip_range(ip_start, ip_end)

    print(f"Removing {len(ip_list)} IPs from interface {interface}...")
    for ip in ip_list:
        remove_ip_from_interface(ip, interface)

    if os.path.exists(pool_file):
        try:
            os.remove(pool_file)
            print(f"[OK] Deleted file {pool_file}")
        except Exception as e:
            print(f"[WARN] Could not delete {pool_file}: {e}")
    else:
        print(f"[INFO] File {pool_file} does not exist, nothing to delete.")

    print("DONE.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Remove IP pool from interface")
    parser.add_argument("--start",     default=IP_RANGE_START, help="IP range start")
    parser.add_argument("--end",       default=IP_RANGE_END,   help="IP range end")
    parser.add_argument("--interface", default=INTERFACE,       help="Network interface")
    parser.add_argument("--pool-file", default=POOL_FILE,       help="Pool file to delete")
    args = parser.parse_args()

    main(
        ip_start=args.start,
        ip_end=args.end,
        interface=args.interface,
        pool_file=args.pool_file
    )

