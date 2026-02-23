import ipaddress
import subprocess
import argparse

# ---- DEFAULT KONFIGURÁCIA ----
IP_RANGE_START = "192.168.10.10"
IP_RANGE_END   = "192.168.10.40"
INTERFACE      = "ens33"
OUTPUT_FILE    = "ip_pool.txt"
# ------------------------------

def generate_ip_range(start_ip, end_ip):
    start = ipaddress.IPv4Address(start_ip)
    end   = ipaddress.IPv4Address(end_ip)
    return [str(ipaddress.IPv4Address(i)) for i in range(int(start), int(end) + 1)]

def add_ip_to_interface(ip, interface):
    cmd = ["sudo", "ip", "addr", "add", f"{ip}/32", "dev", interface]
    try:
        subprocess.run(cmd, check=True)
        print(f"[OK] Added {ip} to {interface}")
    except subprocess.CalledProcessError:
        print(f"[WARN] Could not add {ip} (maybe already exists?)")

def main(
    ip_start=IP_RANGE_START,
    ip_end=IP_RANGE_END,
    interface=INTERFACE,
    output_file=OUTPUT_FILE
):
    print(f"Generating IP range {ip_start} - {ip_end}...")
    ip_list = generate_ip_range(ip_start, ip_end)

    print(f"Adding {len(ip_list)} IPs to interface {interface}...")
    for ip in ip_list:
        add_ip_to_interface(ip, interface)

    print(f"Saving pool to {output_file}...")
    with open(output_file, "w") as f:
        for ip in ip_list:
            f.write(ip + "\n")

    print("DONE.")
    return ip_list  # vráti zoznam pre prípadné ďalšie použitie

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create IP pool on interface")
    parser.add_argument("--start",     default=IP_RANGE_START, help="IP range start")
    parser.add_argument("--end",       default=IP_RANGE_END,   help="IP range end")
    parser.add_argument("--interface", default=INTERFACE,       help="Network interface")
    parser.add_argument("--output",    default=OUTPUT_FILE,     help="Output pool file")
    args = parser.parse_args()

    main(
        ip_start=args.start,
        ip_end=args.end,
        interface=args.interface,
        output_file=args.output
    )

