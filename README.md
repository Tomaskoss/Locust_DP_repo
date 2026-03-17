# 🦗 Locust Load Test GUI

> **Profesionálne grafické rozhranie pre automatizované záťažové testovanie HTTP/HTTPS** postavené na Pythone, CustomTkinter a Locusts.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)
![Platform](https://img.shields.io/badge/Platform-Linux-informational?logo=linux)
![License](https://img.shields.io/badge/License-MIT-green)
![GUI](https://img.shields.io/badge/GUI-CustomTkinter-purple)

---

## 📋 Obsah

- [Prehľad](#-prehľad)
- [Funkcie](#-funkcie)
- [Štruktúra projektu](#-štruktúra-projektu)
- [Požiadavky](#-požiadavky)
- [Inštalácia](#-inštalácia)
- [Konfigurácia](#-konfigurácia)
- [Používanie](#-používanie)
  - [Config](#️-config)
  - [HTTP](#-http)
  - [Generate Report](#-generate-report)
  - [Reports](#-reports)
- [Moduly](#-moduly)
- [Témy](#-témy)
- [PDF Report](#-pdf-report)
- [Digitálne podpisovanie](#-digitálne-podpisovanie)
- [Klávesové skratky](#-klávesové-skratky)

---

## 🔍 Prehľad

**Locust Load Test GUI** je desktopová aplikácia pre Linux, ktorá zjednocuje celý pracovný postup záťažového testovania do jedného okna:

1. **Konfigurácia** – nastavenie cieľa, IP pool-u (IPv4/IPv6), sieťového rozhrania, reachability a network monitoru
2. **Spustenie testu** – automatické spustenie Locust-u spolu s monitorovaním dostupnosti a sieťovej prevádzky
3. **Generovanie reportu** – export výsledkov do profesionálneho PDF s grafmi, topológiou siete a voliteľným digitálnym podpisom
4. **Správa reportov** – prehľad, otvorenie a mazanie vygenerovaných PDF súborov

---

## ✨ Funkcie

| Funkcia | Popis |
|---|---|
| 🎨 **4 farebné témy** | Dark Blue, Dark Green, Dark Red, Locust Dark |
| 🔍 **Zoom** | Ctrl+/Ctrl- na škálovanie celého GUI (50%–200%) |
| 🌐 **IPv4 + IPv6** | Podpora rozsahov aj prefixov pre IPv6 |
| 📡 **Network Monitor** | Sledovanie RX/TX rýchlosti v reálnom čase |
| 📊 **Reachability Monitor** | Meranie dostupnosti cieľa počas testu |
| 🗺️ **Topology Diagram** | Automatické generovanie diagramu siete |
| 📄 **PDF Export** | Profesionálny report s grafmi a metadátami |
| 🔏 **PDF Signing** | Digitálne podpisovanie reportu (PKCS#12) |
| 🖥️ **Real-time log** | Live výstup z Locust procesu a všetkých vlákien |
| ⚙️ **Persistent config** | Nastavenia sa ukladajú do `config.env` |

---

## 📁 Štruktúra projektu

```
Locust_DP_repo/
│
├── locust_gui.py              # Hlavný súbor – GUI aplikácia
├── config.env                 # Konfiguračný súbor (auto-generovaný)
├── ip_pool.txt                # Zoznam pridaných IP adries (auto-generovaný)
├── port_pool.txt              # Zoznam zdrojových portov (auto-generovaný)
├── test_config.csv            # Konfigurácia posledného testu (auto-generovaný)
│
├── data/                      # Výstupné dáta z testov
│   ├── report_stats.csv           # Štatistiky Locust (endpointy)
│   ├── report_stats_history.csv   # Historické dáta Locust
│   ├── reachability.csv           # Výsledky reachability monitoringu
│   ├── network_usage.csv          # Sieťová prevádzka (RX/TX)
│   └── report_metadata.csv        # Metadáta testu
│
├── report/                    # PDF reporty a certifikáty
│   ├── Locust_Report.pdf          # Príklad vygenerovaného reportu
│   ├── topology_diagram.png       # Diagram topológie siete
│   └── cert.p12                   # Certifikát pre podpisovanie (voliteľné)
│
├── network/                   # Sieťové moduly
│   ├── Create_IP_Pool_skript.py   # Pridávanie IP adries na rozhranie
│   ├── Remove_IP_Pool_skript.py   # Odstraňovanie IP adries
│   ├── Network_monitor.py         # Monitor sieťovej prevádzky
│   ├── Reachability.py            # Reachability monitoring
│   └── Create_topology.py         # Generovanie topologického diagramu
│
├── report/                    # Report moduly
│   └── Locust_report_v3.py        # Generovanie PDF reportu (ReportLab)
│
└── locust_tests/              # Locust testovacie súbory
    └── Locustfile_http.py         # HTTP záťažový test
```

---

## 📦 Požiadavky

### Systém
- **OS**: Linux (Ubuntu 20.04+, Debian, Fedora, ...)
- **Python**: 3.8+
- **Locust**: nainštalovaný globálne (`pip install locust`)

### Python balíčky

```bash
pip install customtkinter
pip install requests
pip install pandas
pip install python-dotenv
pip install reportlab
pip install matplotlib
pip install pyhanko          # pre PDF podpisovanie
pip install pyhanko[pkcs11]  # voliteľné
```

Alebo jednorázovo:

```bash
pip install customtkinter requests pandas python-dotenv reportlab matplotlib pyhanko
```

### Systémové nástroje

```bash
# Pre pridávanie IP adries na rozhranie:
sudo apt install iproute2

# Pre otváranie PDF:
sudo apt install xdg-utils
```

---

## 🚀 Inštalácia

```bash
# 1. Klonovanie repozitára
git clone https://github.com/your_username/Locust_DP_repo.git
cd Locust_DP_repo

# 2. Inštalácia závislostí
pip install -r requirements.txt

# 3. Spustenie aplikácie
python3 locust_gui.py
```

> ⚠️ Niektoré operácie (pridávanie IP adries) vyžadujú `sudo` práva. Skript `Create_IP_Pool_skript.py` spúšťa `sudo ip addr add` interne.

---

## ⚙️ Konfigurácia

Konfigurácia sa ukladá do súboru `config.env` v koreňovom adresári projektu. Tento súbor je automaticky načítaný pri spustení aplikácie a aktualizovaný pri každom uložení nastavení.

### Príklad `config.env`

```env
TARGET_HOST=https://google.sk
INTERFACE=ens33
TEST_TYPE=Load Test
IP_VERSION=ipv4
IP_START=192.168.10.10
IP_END=192.168.10.40
IP6_START=fd00::10
IP6_END=fd00::40
IP6_PREFIX=fd00::/64
IPV6_MODE=range
USERS=10
RUN_TIME=60
SPAWN_RATE=1
PROCESSES=-1
REACH_INTERVAL=5
REACH_TIMEOUT=5
REACH_SRC_IP=
REACH_INTERFACE=
REACH_THRESHOLD=50
```

---

## 🖥️ Používanie

Po spustení `python3 locust_gui.py` sa otvorí hlavné okno aplikácie s navigáciou na ľavej strane.

---

### ⚙️ Config

Prvá stránka slúži na nastavenie všetkých parametrov testovania.

#### General
| Parameter | Popis | Príklad |
|---|---|---|
| **Target host** | URL cieľového servera | `https://google.sk` |
| **Interface** | Sieťové rozhranie | `ens33`, `eth0` |
| **Test type** | Typ testu (informačný) | `Load Test` |
| **Source ports** | Rozsah zdrojových portov | `1024-65535` alebo `8000,8001,8002` |

#### IP Pool – IPv4
| Parameter | Popis | Príklad |
|---|---|---|
| **IP range start** | Začiatok rozsahu IP | `192.168.10.10` |
| **IP range end** | Koniec rozsahu IP | `192.168.10.40` |

#### IP Pool – IPv6
Prepínač **Range / Prefix** určuje spôsob definície IP adries:

- **Range**: zadaj `IPv6 start` a `IPv6 end` (napr. `fd00::10` – `fd00::40`)
- **Prefix**: zadaj prefix siete (napr. `fd00::/64`) – adresy sa automaticky vygenerujú

#### Reachability
| Parameter | Popis | Default |
|---|---|---|
| **Interval (s)** | Frekvencia merania dostupnosti | `5` |
| **Timeout (s)** | Timeout pre HTTP request | `5` |
| **Source IP** | IP adresa z ktorej sa meria | = IP range start |
| **Interface** | Rozhranie pre reachability | = hlavné rozhranie |
| **Failure threshold (%)** | Prah zlyhania pre report | `50` |

#### Network Monitor
Vyber rozhranie pre sledovanie RX/TX prevádzky počas testu.

#### Actions
- **⚙ Setup** – Pridá IP adresy na rozhranie (`sudo ip addr add`) a vygeneruje topologický diagram
- **🗑 Cleanup** – Odstráni všetky pridané IP adresy z rozhrania

---

### 🌐 HTTP

Stránka pre konfiguráciu Locust parametrov a spustenie testu.

#### Locust Parameters
| Parameter | Popis | Default |
|---|---|---|
| **Users** | Počet virtuálnych používateľov | `1` |
| **Run time (s)** | Dĺžka trvania testu v sekundách | `20` |
| **Spawn rate** | Počet nových používateľov za sekundu | `1` |
| **Processes** | Počet Locust procesov (`-1` = auto) | `-1` |

#### Locustfile
- Tlačidlom **Browse** môžeš vybrať vlastný Locustfile (`.py`)
- Ak nevyberieš žiadny, použije sa defaultný `locust_tests/Locustfile_http.py`
- Tlačidlo **✖** resetuje výber na defaultný súbor

#### Spustenie testu
Kliknutím na **▶ Start Test** sa súčasne spustia:

1. **Locust** – záťažový test podľa parametrov
2. **Reachability Monitor** – meranie dostupnosti cieľa v intervale
3. **Network Monitor** – sledovanie RX/TX prevádzky na rozhraní

Priebeh je viditeľný v **Output Log** paneli v spodnej časti okna.

Tlačidlom **⛔ Stop Test** možno test kedykoľvek prerušiť.

---

### 📄 Generate Report

Po dokončení testu vygeneruj PDF report.

#### Comment
Textové pole pre vlastný komentár, ktorý sa zobrazí v reporte.

#### Output
| Parameter | Popis | Default |
|---|---|---|
| **Report name** | Názov výstupného PDF súboru | `Locust_Report.pdf` |
| **Save to** | Adresár pre uloženie reportu | `report/` |

#### PDF Signing
Zaškrtnutím **Sign PDF** sa aktivuje sekcia digitálneho podpisovania:

| Parameter | Popis |
|---|---|
| **Certificate** | Cesta k `.p12` / `.pfx` certifikátu |
| **Password** | Heslo pre privátny kľúč certifikátu |

Tlačidlom **📄 Generate Report** sa spustí generovanie – report sa automaticky otvorí po dokončení.

---

### 📋 Reports

Prehľad všetkých vygenerovaných PDF reportov v adresári `report/`.

| Stĺpec | Popis |
|---|---|
| **Report name** | Názov PDF súboru |
| **Created** | Dátum a čas vytvorenia |
| **Signed** | ✅ Signed / ❌ No – či je PDF digitálne podpísané |

- **Open** – otvorí PDF v systémovom prehliadači (`xdg-open`)
- **🗑** – zmaže report zo súborového systému
- **⟳ Refresh** – aktualizuje zoznam reportov

---

## 🧩 Moduly

### `Create_IP_Pool_skript.py`
Pridáva rozsah IPv4/IPv6 adries na sieťové rozhranie pomocou `sudo ip addr add`. Ukladá zoznam pridaných IP do `ip_pool.txt`.

```python
create_pool(
    ip_start="192.168.10.10",
    ip_end="192.168.10.40",
    interface="ens33",
    output_file="ip_pool.txt",
    ip_version="ipv4"
)
```

### `Remove_IP_Pool_skript.py`
Odstraňuje IP adresy z rozhrania pomocou `sudo ip addr del`. Číta zoznam z `ip_pool.txt`.

### `Network_monitor.py`
Thread-based monitor sieťovej prevádzky čítajúci `/proc/net/dev`. Loguje RX/TX v kB/s do CSV súboru.

```python
monitor = NetworkMonitor(interface="ens33", interval=1, output_file="data/network_usage.csv")
monitor.start()
# ... test ...
monitor.stop()
```

### `Reachability.py`
Periodicky meria HTTP dostupnosť cieľa z konkrétnej zdrojovej IP adresy. Výsledky (timestamp, status_code, elapsed_time) ukladá do `data/reachability.csv`.

### `Create_topology.py`
Generuje PNG diagram sieťovej topológie pomocou Matplotlib. Vizualizuje vzťah medzi útočníkom (tester), zdrojovými IP adresami a cieľom.

### `Locust_report_v3.py`
Hlavný report generátor. Zo CSV dát vytvára profesionálny PDF dokument obsahujúci:
- Titulnú stranu s metadátami
- Tabuľky výkonnostných štatistík (RPS, response times, failures)
- Časové grafy (response time, requests/s)
- Graf sieťovej prevádzky (RX/TX)
- Graf reachability (dostupnosť cieľa)
- Topologický diagram siete
- Voliteľný digitálny podpis

---

## 🎨 Témy

Aplikácia obsahuje 4 vstavaných farebných tém prepínateľných v dolnej časti sidebaru:

| Téma | Primárna farba | Popis |
|---|---|---|
| **Locust Dark** | `#2a5f3a` (tmavá zelená) | Predvolená – minimalistická tmavá |
| **Dark Blue** | `#85b832` (limetková) | Tmavá s modrou základňou |
| **Dark Green** | `#4caf50` (zelená) | Zelená na tmavom pozadí |
| **Dark Red** | `#e53935` (červená) | Červená na tmavom pozadí |

> Zmena témy reštartuje aplikáciu s novými farbami (nastavenia sa zachovajú).

---

## 📊 PDF Report

Vygenerovaný PDF report obsahuje tieto sekcie:

1. **Titulná strana** – názov testu, dátum, cieľ, zdrojové IP, rozhranie, typ testu
2. **Test Summary** – celkový počet requestov, failure rate, trvanie testu
3. **Performance Statistics** – tabuľka štatistík pre každý endpoint (min/avg/max response time, RPS, failures)
4. **Response Time Graph** – časový priebeh odozvy (percentily 50/95/99)
5. **Requests per Second** – priebeh počtu požiadaviek za sekundu
6. **Reachability Graph** – dostupnosť cieľa počas testu (pass/fail)
7. **Network Traffic** – RX/TX prevádzka na sieťovom rozhraní
8. **Network Topology** – vizuálny diagram testovacieho prostredia
9. **Komentár** – vlastná poznámka testera
10. **Digitálny podpis** – LTV podpis (ak bol aktivovaný)

---

## 🔏 Digitálne podpisovanie

PDF reporty je možné digitálne podpísať pomocou PKCS#12 certifikátu (`.p12` / `.pfx`).

### Príprava certifikátu

```bash
# Vytvorenie self-signed certifikátu pre testovacie účely:
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
openssl pkcs12 -export -out cert.p12 -inkey key.pem -in cert.pem
```

Umiestni `cert.p12` do adresára `report/` – aplikácia ho automaticky predvyplní.

### Postup podpisovania
1. Na stránke **Generate Report** zaškrtni **Sign PDF**
2. Vyber `.p12` certifikát tlačidlom **Browse**
3. Zadaj heslo certifikátu
4. Klikni **Generate Report**

Podpísané reporty sú označené `✅ Signed` v zozname reportov.

---

## ⌨️ Klávesové skratky

| Skratka | Funkcia |
|---|---|
| `Ctrl` + `+` / `=` | Priblíženie (zoom in) |
| `Ctrl` + `-` | Oddialenie (zoom out) |
| `Ctrl` + `0` | Reset zoomu na 100% |
| `Scroll wheel` | Scrollovanie v zoznamoch a formulároch |

---

## 🔧 Rozšírenie / Customizácia

### Pridanie vlastnej témy

V `locust_gui.py` rozšír slovník `THEMES`:

```python
THEMES["My Theme"] = {
    "SIDEBAR":  "#1a1a2e",
    "CONTENT":  "#16213e",
    "CARD":     "#1f2b47",
    "ACTIVE":   "#ff6b35",   # tvoja farba
    "HOVER":    "#e55a2b",
    ...
}
```

### Vlastný Locustfile

Vytvor `.py` súbor s Locust testom a vyber ho cez **Browse** na stránke HTTP. Príklad:

```python
from locust import HttpUser, task, between

class MyUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def homepage(self):
        self.client.get("/")
```

---

## 📝 Licencia

Tento projekt je distribuovaný pod licenciou MIT. Pozri súbor `LICENSE` pre detaily.

---

## 👤 Autor

Vytvorené v rámci diplomovej práce, 2026.

---

*Locust Load Test GUI – automatizuj, testuj, analyzuj.*
