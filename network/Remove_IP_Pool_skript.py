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


def generate_ip_range_v4(start_ip, end_ip):
    start = ipaddress.IPv4Address(start_ip)
    end   = ipaddress.IPv4Address(end_ip)
    return [str(ipaddress.IPv4Address(i)) for i in range(int(start), int(end) + 1)]


def generate_ip_range_v6(start_ip, end_ip):
    start = int(ipaddress.IPv6Address(start_ip))
    end   = int(ipaddress.IPv6Address(end_ip))
    return [str(ipaddress.IPv6Address(i)) for i in range(start, end + 1)]


def remove_ip_from_interface(ip, interface, ip_version="ipv4"):
    prefix = "128" if ip_version == "ipv6" else "32"
    cmd = ["sudo", "ip", "addr", "del", f"{ip}/{prefix}", "dev", interface]
    try:
        subprocess.run(cmd, check=True, stderr=subprocess.DEVNULL)
        print(f"[OK] Removed {ip}/{prefix} from {interface}")
    except subprocess.CalledProcessError:
        print(f"[WARN] Could not remove {ip} (maybe not present?)")


def _load_from_pool_file(pool_file):
    """Načíta IP adresy z pool súboru (fallback)."""
    if os.path.exists(pool_file):
        with open(pool_file) as f:
            return [line.strip() for line in f if line.strip()]
    return []


def main(
    ip_start=IP_RANGE_START,
    ip_end=IP_RANGE_END,
    interface=INTERFACE,
    pool_file=POOL_FILE,
    ip_version="ipv4",
    ip_list=None,    # hotový zoznam z GUI
):
    # ── Zostavenie zoznamu IP ──────────────────────────────────────
    if ip_list is not None:
        # GUI poslalo hotový zoznam
        print(f"Using provided IP list ({len(ip_list)} addresses)...")
    else:
        # Pokus načítať z pool súboru (najpresnejší zdroj)
        ip_list = _load_from_pool_file(pool_file)
        if ip_list:
            print(f"Loaded {len(ip_list)} IPs from {pool_file}...")
        else:
            # Fallback — generuj z range
            if ip_version == "ipv6":
                ip_list = generate_ip_range_v6(ip_start, ip_end)
                print(f"Generating IPv6 range {ip_start} - {ip_end} "
                      f"({len(ip_list)} addresses)...")
            else:
                ip_list = generate_ip_range_v4(ip_start, ip_end)
                print(f"Generating IPv4 range {ip_start} - {ip_end} "
                      f"({len(ip_list)} addresses)...")

    # ── Detekcia ip_version z prvej adresy (ak nie je explicitne) ──
    if ip_list and ip_version == "ipv4":
        try:
            ipaddress.IPv6Address(ip_list[0])
            ip_version = "ipv6"
            print("[INFO] Detected IPv6 addresses in pool file → using /128")
        except ValueError:
            pass

    # ── Odstránenie z interface ────────────────────────────────────
    print(f"Removing {len(ip_list)} IPs from interface {interface}...")
    for ip in ip_list:
        remove_ip_from_interface(ip, interface, ip_version)

    # ── Zmazanie pool súboru ───────────────────────────────────────
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
    parser.add_argument("--start",      default=IP_RANGE_START, help="IP range start")
    parser.add_argument("--end",        default=IP_RANGE_END,   help="IP range end")
    parser.add_argument("--interface",  default=INTERFACE,       help="Network interface")
    parser.add_argument("--pool-file",  default=POOL_FILE,       help="Pool file to delete")
    parser.add_argument("--ip-version", default="ipv4",
                        choices=["ipv4", "ipv6"],                help="IP version")
    args = parser.parse_args()

    main(
        ip_start   = args.start,
        ip_end     = args.end,
        interface  = args.interface,
        pool_file  = args.pool_file,
        ip_version = args.ip_version,
    )

