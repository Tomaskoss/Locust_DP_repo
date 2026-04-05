import os
import ipaddress
import subprocess
import argparse

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---- DEFAULT KONFIGURÁCIA ----
IP_RANGE_START = "192.168.10.10"
IP_RANGE_END   = "192.168.10.40"
INTERFACE      = "ens33"
OUTPUT_FILE    = os.path.join(BASE_DIR, "ip_pool.txt")
# ------------------------------


def generate_ip_range_v4(start_ip, end_ip):
    start = ipaddress.IPv4Address(start_ip)
    end   = ipaddress.IPv4Address(end_ip)
    return [str(ipaddress.IPv4Address(i)) for i in range(int(start), int(end) + 1)]


def generate_ip_range_v6(start_ip, end_ip):
    start = int(ipaddress.IPv6Address(start_ip))
    end   = int(ipaddress.IPv6Address(end_ip))
    return [str(ipaddress.IPv6Address(i)) for i in range(start, end + 1)]


def generate_ip_prefix_v6(prefix_str, max_count=256):
    net = ipaddress.IPv6Network(prefix_str, strict=False)
    return [str(ip) for ip in list(net.hosts())[:max_count]]


def add_ip_to_interface(ip, interface, ip_version="ipv4", prefix_len=None):
    if prefix_len is None:
        prefix = "128" if ip_version == "ipv6" else "32"
    else:
        prefix = str(prefix_len)
    cmd = ["sudo", "ip", "addr", "add", f"{ip}/{prefix}", "dev", interface]
    try:
        subprocess.run(cmd, check=True, stderr=subprocess.DEVNULL)
        print(f"[OK] Added {ip}/{prefix} to {interface}")
    except subprocess.CalledProcessError:
        print(f"[WARN] Could not add {ip} (maybe already exists?)")


def load_existing_ips(output_file):
    """Načíta existujúce IP adresy z pool súboru (ak existuje)."""
    if not os.path.exists(output_file):
        return set()
    try:
        with open(output_file) as f:
            return {line.strip() for line in f
                    if line.strip() and not line.startswith("#")}
    except Exception as e:
        print(f"[WARN] Could not read existing pool file: {e}")
        return set()


def save_ip_pool(ip_set, output_file):
    """Uloží zlúčený a zoradený zoznam IP do pool súboru."""
    sorted_ips = sorted(ip_set, key=lambda x: ipaddress.ip_address(x))
    with open(output_file, "w") as f:
        for ip in sorted_ips:
            f.write(ip + "\n")
    return sorted_ips


def main(
    ip_start=IP_RANGE_START,
    ip_end=IP_RANGE_END,
    interface=INTERFACE,
    output_file=OUTPUT_FILE,
    ip_version="ipv4",
    ip_list=None,
    ip6_prefix=None,
    prefix_len=None
):
    # ── Zostavenie zoznamu IP ──────────────────────────────────────
    if ip_list is not None:
        # GUI poslalo hotový zoznam (IPv6 prefix mód)
        pass
    elif ip_version == "ipv6":
        if ip6_prefix:
            ip_list = generate_ip_prefix_v6(ip6_prefix)
            print(f"Generating IPv6 prefix {ip6_prefix} "
                  f"({len(ip_list)} addresses)...")
        else:
            ip_list = generate_ip_range_v6(ip_start, ip_end)
            print(f"Generating IPv6 range {ip_start} - {ip_end} "
                  f"({len(ip_list)} addresses)...")
    else:
        ip_list = generate_ip_range_v4(ip_start, ip_end)
        print(f"Generating IPv4 range {ip_start} - {ip_end} "
              f"({len(ip_list)} addresses)...")

    # ── Pridanie na interface ──────────────────────────────────────
    print(f"Adding {len(ip_list)} IPs to interface {interface}...")
    for ip in ip_list:
        add_ip_to_interface(ip, interface, ip_version, prefix_len)

    # ── Zlúčenie s existujúcim pool súborom ───────────────────────
    existing_ips = load_existing_ips(output_file)
    new_ips      = set(ip_list)
    added_count  = len(new_ips - existing_ips)
    merged_ips   = existing_ips | new_ips

    if existing_ips:
        print(f"Merging with existing pool: "
              f"{len(existing_ips)} existing + {added_count} new "
              f"= {len(merged_ips)} total IPs")
    else:
        print(f"Creating new pool with {len(merged_ips)} IPs...")

    # ── Uloženie pool súboru ───────────────────────────────────────
    print(f"Saving pool to {output_file}...")
    sorted_ips = save_ip_pool(merged_ips, output_file)

    print("DONE.")
    return sorted_ips


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create IP pool on interface")
    parser.add_argument("--start",      default=IP_RANGE_START, help="IP range start")
    parser.add_argument("--end",        default=IP_RANGE_END,   help="IP range end")
    parser.add_argument("--interface",  default=INTERFACE,       help="Network interface")
    parser.add_argument("--output",     default=OUTPUT_FILE,     help="Output pool file")
    parser.add_argument("--ip-version", default="ipv4",
                        choices=["ipv4", "ipv6"],                help="IP version")
    parser.add_argument("--ip6-prefix", default=None,            help="IPv6 prefix, e.g. fd00::/64")
    args = parser.parse_args()

    main(
        ip_start    = args.start,
        ip_end      = args.end,
        interface   = args.interface,
        output_file = args.output,
        ip_version  = args.ip_version,
        ip6_prefix  = args.ip6_prefix,
    )
