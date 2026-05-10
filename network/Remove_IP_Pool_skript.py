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


def remove_ip_from_interface(ip, interface, ip_version="ipv4", prefix_len=None):
    if prefix_len is None:
        prefix = "128" if ip_version == "ipv6" else "32"
    else:
        prefix = str(prefix_len)
    cmd = ["sudo", "ip", "addr", "del", f"{ip}/{prefix}", "dev", interface]
    try:
        subprocess.run(cmd, check=True, stderr=subprocess.DEVNULL)
        print(f"[OK] Removed {ip}/{prefix} from {interface}")
    except subprocess.CalledProcessError:
        print(f"[WARN] Could not remove {ip}/{prefix} (maybe not present?)")


def _load_from_pool_file(pool_file):
    """
    Načíta IP adresy z pool súboru.

    Podporované formáty:
      - 192.168.100.10
      - 192.168.100.10/32
      - fd00:100::10
      - fd00:100::10/64

    Vracia list dvojíc:
      [(ip, prefix), ...]
    """
    entries = []

    if not os.path.exists(pool_file):
        return entries

    with open(pool_file) as f:
        for line in f:
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            if "/" in line:
                ip, prefix = line.split("/", 1)
                entries.append((ip.strip(), prefix.strip()))
            else:
                entries.append((line.strip(), None))

    return entries


def main(
    ip_start=IP_RANGE_START,
    ip_end=IP_RANGE_END,
    interface=INTERFACE,
    pool_file=POOL_FILE,
    ip_version="ipv4",
    ip_list=None,
    prefix_len=None,
):
    # ── Zostavenie zoznamu IP ──────────────────────────────────────
    entries = []

    if ip_list is not None:
        # GUI poslalo hotový zoznam IP adries bez prefixu
        print(f"Using provided IP list ({len(ip_list)} addresses)...")
        entries = [(ip, prefix_len) for ip in ip_list]

    else:
        # Najprv sa pokúsime načítať presný obsah ip_pool.txt
        entries = _load_from_pool_file(pool_file)

        if entries:
            print(f"Loaded {len(entries)} IPs from {pool_file}...")
        else:
            # Fallback — generuj z range
            if ip_version == "ipv6":
                generated = generate_ip_range_v6(ip_start, ip_end)
                print(
                    f"Generating IPv6 range {ip_start} - {ip_end} "
                    f"({len(generated)} addresses)..."
                )
            else:
                generated = generate_ip_range_v4(ip_start, ip_end)
                print(
                    f"Generating IPv4 range {ip_start} - {ip_end} "
                    f"({len(generated)} addresses)..."
                )

            entries = [(ip, prefix_len) for ip in generated]

    if not entries:
        print("[INFO] No IP addresses to remove.")
        return

    # ── Odstránenie z interface ────────────────────────────────────
    print(f"Removing {len(entries)} IPs from interface {interface}...")

    for ip, stored_prefix in entries:
        # Detekcia IP verzie pre každú adresu samostatne
        try:
            ipaddress.IPv6Address(ip)
            detected_version = "ipv6"
            default_prefix = "128"
        except ValueError:
            detected_version = "ipv4"
            default_prefix = "32"

        final_prefix = stored_prefix or prefix_len or default_prefix

        remove_ip_from_interface(
            ip=ip,
            interface=interface,
            ip_version=detected_version,
            prefix_len=final_prefix
        )

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
    parser.add_argument("--prefix-len", default=None,            help="Prefix length, e.g. 24 or 64")
    args = parser.parse_args()

    main(
        ip_start    = args.start,
        ip_end      = args.end,
        interface   = args.interface,
        pool_file   = args.pool_file,
        ip_version  = args.ip_version,
        prefix_len  = args.prefix_len,
    )

