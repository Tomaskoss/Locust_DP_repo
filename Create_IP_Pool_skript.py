import ipaddress
import subprocess

# ---- KONFIGURÁCIA ----
IP_RANGE_START = "192.168.10.10"
IP_RANGE_END   = "192.168.10.40"
INTERFACE = "ens33"
OUTPUT_FILE = "ip_pool.txt"
# -----------------------


def generate_ip_range(start_ip, end_ip):
    start = ipaddress.IPv4Address(start_ip)
    end = ipaddress.IPv4Address(end_ip)

    ip_list = []
    for i in range(int(start), int(end) + 1):
        ip_list.append(str(ipaddress.IPv4Address(i)))  # <-- prevod čísla späť na IP
    return ip_list


def add_ip_to_interface(ip, interface):
    cmd = ["sudo", "ip", "addr", "add", f"{ip}/32", "dev", interface]
    try:
        subprocess.run(cmd, check=True)
        print(f"[OK] Added {ip} to {interface}")
    except subprocess.CalledProcessError:
        print(f"[WARN] Could not add {ip} (maybe already exists?)")


def main():
    print("Generating IP range...")
    ip_list = generate_ip_range(IP_RANGE_START, IP_RANGE_END)

    print(f"Adding IPs to interface {INTERFACE}...")
    for ip in ip_list:
        add_ip_to_interface(ip, INTERFACE)

    print(f"Saving pool to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, "w") as f:
        for ip in ip_list:
            f.write(ip + "\n")

    print("DONE.")


if __name__ == "__main__":
    main()
