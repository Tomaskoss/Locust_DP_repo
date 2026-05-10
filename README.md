# 🦗 Locust Load Test GUI

> **Profesionálne grafické rozhranie pre automatizované záťažové testovanie HTTP/HTTPS**  
> Postavené na Pythone, CustomTkinter a Locust frameworku – celý workflow záťažového testovania v jedinom okne.

<br>

![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Linux-FCC624?logo=linux&logoColor=black)
![Locust](https://img.shields.io/badge/Locust-latest-00AA00?logo=locust&logoColor=white)
![GUI](https://img.shields.io/badge/GUI-CustomTkinter-9B59B6)
![License](https://img.shields.io/badge/License-MIT-2ECC71)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)

---

## 📋 Obsah

- [O projekte](#-o-projekte)
- [Hlavné funkcie](#-hlavné-funkcie)
- [Štruktúra projektu](#-štruktúra-projektu)
- [Požiadavky](#-požiadavky)
- [Inštalácia](#-inštalácia)
- [Konfigurácia](#️-konfigurácia)
- [Používanie](#️-používanie)
  - [Config – nastavenia](#️-config--nastavenia)
  - [HTTP – spustenie testu](#-http--spustenie-testu)
  - [Playwright – replay relácie](#-playwright--replay-relácie)
  - [Generate Report – generovanie PDF](#-generate-report--generovanie-pdf)
  - [Reports – správa reportov](#-reports--správa-reportov)
- [Stage Presets](#-stage-presets)
- [Sieťové moduly](#-sieťové-moduly)
- [PDF Report](#-pdf-report)
- [Digitálne podpisovanie](#-digitálne-podpisovanie)
- [Farebné témy](#-farebné-témy)
- [Klávesové skratky](#️-klávesové-skratky)
- [Rozšírenie a customizácia](#-rozšírenie-a-customizácia)
- [Licencia](#-licencia)

---

## 🔍 O projekte

**Locust Load Test GUI** je desktopová aplikácia pre Linux, ktorá zjednocuje celý pracovný postup záťažového testovania do jedného okna. Projekt vznikol ako diplomová práca a rieši problém fragmentovanosti nástrojov – typicky musíte kombinovať viacero CLI nástrojov, manuálne spravovať IP adresy, sledovať sieť a následne ručne spracovávať výsledky. Táto aplikácia to celé automatizuje.

**Workflow v 4 krokoch:**

```
1. CONFIGURE   →   2. TEST   →   3. MONITOR   →   4. REPORT
  IP Pool            Locust        Reachability      PDF + grafy
  Rozhranie          Playwright    Network RX/TX     Digitálny podpis
  Parametre          Stage preset  Real-time log     Topológia siete
```

---

## ✨ Hlavné funkcie

| Kategória | Funkcia | Popis |
|---|---|---|
| 🌐 **Sieť** | IPv4 + IPv6 podpora | Rozsahy aj prefixy (`fd00::/64`) |
| 🌐 **Sieť** | IP Pool management | Automatické pridávanie/odstraňovanie IP adries na rozhranie cez `ip addr` |
| 🌐 **Sieť** | Network Monitor | Sledovanie RX/TX rýchlosti v reálnom čase z `/proc/net/dev` |
| 🌐 **Sieť** | Reachability Monitor | Meranie dostupnosti cieľa z konkrétnej zdrojovej IP počas testu |
| 🗺️ **Vizualizácia** | Topology Diagram | Auto-generovaný PNG diagram siete (Matplotlib) |
| 📊 **Reporting** | PDF Export | Profesionálny report s grafmi, tabuľkami a metadátami (ReportLab) |
| 🔏 **Bezpečnosť** | PDF Signing | Digitálne podpisovanie reportu cez PKCS#12 certifikát (pyHanko, LTV) |
| ⚡ **Záťaž** | Stage Presets | 5 zabudovaných profilov záťaže (Flat, Stress, Spike, Endurance, Capacity) |
| 🎭 **Playwright** | Session Replay | Záznam a replay reálnych browserových relácií ako záťažový test |
| 🎨 **UI** | 5 farebných tém | Locust Dark, Navy Blue, Discord Light, Discord Darkest, Netflix |
| 🔍 **UI** | Zoom | Škálovanie celého GUI od 50% do 200% (Ctrl+/Ctrl-) |
| ⚙️ **Konfigurácia** | Persistent config | Nastavenia sa automaticky ukladajú do `config.env` |
| 🖥️ **Monitoring** | Real-time log | Live výstup z Locust procesu a všetkých vlákien v jedinom paneli |

---

## 📁 Štruktúra projektu

```
Locust_DP_repo/
│
├── locust_gui.py                    # Hlavný súbor – GUI aplikácia (CustomTkinter)
├── prepare_tester_python.sh         # Automatický inštalačný skript prostredia
├── config.env                       # Konfiguračný súbor (auto-generovaný pri prvom spustení)
├── ip_pool.txt                      # Aktívny zoznam IP adries na rozhraní (auto)
├── port_pool.txt                    # Zoznam zdrojových portov (auto)
├── test_config.csv                  # Konfigurácia posledného testu (auto)
├── stages.json                      # Konfigurácia fáz pre DynamicShape (auto)
├── session.json                     # Záznam Playwright relácie (generovaný recorderom)
│
├── data/                            # Výstupné dáta z testov (auto-vytvorený)
│   ├── report_stats.csv             # Štatistiky Locust (endpointy, percentily)
│   ├── report_stats_history.csv     # Historický priebeh záťaže
│   ├── reachability.csv             # Výsledky reachability monitoringu
│   ├── network_usage.csv            # Sieťová prevádzka (RX/TX v kB/s)
│   ├── report_failures.csv          # Detailné záznamy o zlyhaných requestoch
│   └── report_metadata.csv          # Metadáta testu (čas, cieľ, IP, rozhranie)
│
├── IP_pool/                         # Uložené a pomenované IP pool súbory
│
├── report/                          # PDF reporty, certifikáty a report modul
│   ├── Locust_report_v3.py          # Generátor PDF reportu (ReportLab)
│   ├── cert.p12                     # Certifikát pre podpisovanie (voliteľné)
│   └── topology_diagram.png         # Diagram topológie siete (auto-generovaný)
│
├── network/                         # Sieťové moduly
│   ├── Create_IP_Pool_skript.py     # Pridávanie IPv4/IPv6 adries na rozhranie
│   ├── Remove_IP_Pool_skript.py     # Odstraňovanie IP adries
│   ├── Network_monitor.py           # Thread-based monitor RX/TX prevádzky
│   ├── Reachability.py              # Reachability monitoring cez HTTP
│   ├── Create_topology.py           # Generovanie topologického diagramu
│   └── playwright_recorder.py       # Nahrávanie browserovej relácie
│
└── locust_tests/                    # Locust testovacie súbory
    ├── Locustfile_http.py           # HTTP záťažový test s IP/port binding
    └── locustfile_playwright.py     # Replay Playwright relácie ako Locust test
```

---

## 📦 Požiadavky

### Systémové požiadavky

| Požiadavka | Minimálna verzia | Poznámka |
|---|---|---|
| **OS** | Linux (Ubuntu 20.04+) | Debian, Fedora a ďalšie distribúcie tiež fungujú |
| **Python** | 3.8+ | Vrátane `python3-tk` pre GUI |
| **iproute2** | aktuálna | Nutné pre `sudo ip addr add/del` |
| **xdg-utils** | aktuálna | Pre otváranie PDF v systémovom prehliadači |

> ⚠️ **Aplikácia nie je kompatibilná s Windows ani macOS.** Sieťové operácie využívajú Linux-špecifické rozhrania (`/proc/net/dev`, `ip addr`).

### Python závislosti

```
locust
customtkinter
CTkToolTip
requests
pandas
matplotlib
reportlab
python-dotenv
pyhanko[full]
pyhanko-certvalidator
```

---

## 🚀 Inštalácia

### Možnosť A – Automatická inštalácia (odporúčané)

Projekt obsahuje kompletný inštalačný skript, ktorý nastaví celé prostredie vrátane virtuálneho prostredia, systémových balíkov a defaultného `config.env`:

```bash
# 1. Klonovanie repozitára
git clone https://github.com/your_username/Locust_DP_repo.git
cd Locust_DP_repo

# 2. Spustenie inštalačného skriptu
chmod +x prepare_tester_python.sh
./prepare_tester_python.sh

# 3. Aktivácia prostredia a spustenie
source locust_env/bin/activate
python3 locust_gui.py
```

Skript automaticky:
- Nainštaluje systémové balíky (`python3-tk`, `iproute2`, `xdg-utils`, sieťové nástroje)
- Vytvorí Python virtuálne prostredie `locust_env/`
- Nainštaluje všetky Python závislosti
- Vytvorí adresárovú štruktúru (`data/`, `report/`, `IP_pool/`)
- Vygeneruje defaultný `config.env`

### Možnosť B – Manuálna inštalácia

```bash
# Systémové závislosti
sudo apt-get install python3 python3-pip python3-venv python3-tk iproute2 xdg-utils

# Klonovanie
git clone https://github.com/your_username/Locust_DP_repo.git
cd Locust_DP_repo

# Python závisosti
pip install locust customtkinter CTkToolTip requests pandas matplotlib \
            reportlab python-dotenv "pyhanko[full]" pyhanko-certvalidator

# Spustenie
python3 locust_gui.py
```

> ⚠️ Operácie s IP adresami (`Setup` / `Cleanup`) vyžadujú `sudo` práva, ktoré sa využívajú interne cez `subprocess`.

---

## ⚙️ Konfigurácia

Konfigurácia sa ukladá do súboru `config.env` a automaticky sa načítava pri každom štarte aplikácie. Zmeny cez GUI sa do súboru zapisujú okamžite.

### Úplný zoznam parametrov `config.env`

```env
# ── Locust ─────────────────────────────────────────
TARGET_HOST=https://google.sk         # URL testovaného servera
TEST_TYPE=Load Test                   # Typ testu (informačný popis)
PROCESSES=-1                          # Počet Locust procesov (-1 = auto)
STOP_TIMEOUT=30                       # Timeout pri zastavení (s)
CONNECT_TIMEOUT=5                     # TCP connection timeout (s)
READ_TIMEOUT=15                       # HTTP read timeout (s)

# ── HTTP Request ────────────────────────────────────
HTTP_METHOD=GET                       # GET | POST | PUT | DELETE | PATCH
ENDPOINT_PATH=/                       # Testovaná cesta
REQUEST_BODY={}                       # JSON telo pre POST/PUT
SSL_VERIFY=true                       # Verifikácia SSL certifikátu
REQUEST_FAILURE_THRESHOLD=1           # Počet zlyhaní pred označením za chybu

# ── Sieť / IP Pool ──────────────────────────────────
INTERFACE=ens33                       # Sieťové rozhranie
IP_VERSION=ipv4                       # ipv4 | ipv6

# IPv4
IP_START=192.168.xxx.100              # Začiatok rozsahu
IP_END=192.168.xxx.120                # Koniec rozsahu
IPV4PREFIX=32                         # Prefix masky

# IPv6
IP6_START=fd00:100::1000              # Začiatok rozsahu
IP6_END=fd00:100::1050                # Koniec rozsahu
IP6_PREFIX=fd00:100::/64              # Prefix siete
IPV6_MODE=range                       # range | prefix
IPV6RPREFIX=64                        # Dĺžka prefixu

# ── Reachability ────────────────────────────────────
REACH_INTERVAL=5                      # Frekvencia merania (s)
REACH_TIMEOUT=5                       # HTTP timeout pre meranie (s)
REACH_SRC_IP=                         # Zdrojová IP (default = IP_START)
REACH_INTERFACE=ens33                 # Rozhranie pre meranie
REACH_THRESHOLD=50                    # Prah zlyhania pre report (%)

# ── Stage Presets ───────────────────────────────────
STAGES=[{"duration":60,"users":10,"spawn_rate":5,...}]
```

---

## 🖥️ Používanie

Po spustení `python3 locust_gui.py` sa otvorí hlavné okno s navigáciou na ľavej strane.

### ⚙️ Config – nastavenia

Prvá karta pre konfiguráciu všetkých parametrov testovania.

**General**

| Parameter | Popis | Príklad |
|---|---|---|
| Target host | URL testovaného servera | `https://api.example.com` |
| Interface | Sieťové rozhranie | `ens33`, `eth0`, `enp3s0` |
| Test type | Popis typu testu (do reportu) | `Load Test`, `Stress Test` |
| Source ports | Rozsah alebo zoznam portov | `1024-65535` alebo `8000,8001` |

**IP Pool – IPv4 / IPv6**

Aplikácia podporuje dva módy IPv6: **Range** (konkrétne adresy `fd00::10` – `fd00::40`) a **Prefix** (automatické generovanie z prefixu `fd00::/64`).

**Reachability**

| Parameter | Default | Popis |
|---|---|---|
| Interval (s) | 5 | Ako často sa meria dostupnosť |
| Timeout (s) | 5 | Max čakanie na HTTP odpoveď |
| Source IP | = IP_START | Z akej IP sa meria |
| Failure threshold (%) | 50 | Nad túto hodnotu = varovaniev reporte |

**Actions**

- **⚙ Setup** – pridá IP adresy na rozhranie (`sudo ip addr add`) a vygeneruje topologický diagram
- **🗑 Cleanup** – odstráni všetky pridané IP adresy (`sudo ip addr del`)

---

### 🌐 HTTP – spustenie testu

Karta pre konfiguráciu Locust parametrov a spustenie záťažového testu.

**Locust parametre**

| Parameter | Default | Popis |
|---|---|---|
| Users | 1 | Počet súbežných virtuálnych používateľov |
| Run time (s) | 20 | Celková dĺžka testu |
| Spawn rate | 1 | Počet nových používateľov za sekundu |
| Processes | -1 | Počet Locust worker procesov (`-1` = podľa CPU) |

**Locustfile** – cez tlačidlo **Browse** môžete vybrať vlastný `.py` Locustfile; bez výberu sa použije defaultný `locust_tests/Locustfile_http.py`.

Kliknutím na **▶ Start Test** sa súčasne spustia:
1. **Locust** – záťažový test
2. **Reachability Monitor** – periodické meranie dostupnosti cieľa
3. **Network Monitor** – sledovanie RX/TX prevádzky

Výstup je viditeľný v live **Output Log** paneli. Test je možné kedykoľvek zastaviť tlačidlom **⛔ Stop Test**.

---

### 🎭 Playwright – replay relácie

Locust GUI podporuje aj replay reálnych browserových relácií namiesto syntetických HTTP requestov.

**Krok 1: Nahratie relácie**

```bash
# Spustí Playwright recorder – otvorí browser, v ktorom nahráte reláciu
python3 network/playwright_recorder.py
# Výsledok sa uloží do session.json
```

**Krok 2: Konfigurácia v `config.env`**

```env
SESSION_FILE=session.json         # cesta k nahranej relácii
REPLAY_TYPES=document,xhr,fetch   # typy requestov na replay (alebo "all")
TASK_MODE=sequential              # sequential | random
THINK_TIME_MS=0                   # extra oneskorenie medzi requestmi (ms)
```

**Krok 3: Spustenie testu**

Na karte **HTTP** vyberte `locust_tests/locustfile_playwright.py` cez **Browse** a spustite test štandardne.

---

### 📄 Generate Report – generovanie PDF

Po dokončení testu vygenerujte profesionálny PDF report.

| Parameter | Default | Popis |
|---|---|---|
| Report name | `Locust_Report.pdf` | Názov výstupného súboru |
| Save to | `report/` | Cieľový adresár |
| Comment | — | Vlastný komentár testera (zobrazí sa v reporte) |

Sekcia **PDF Signing** – zaškrtnutím **Sign PDF** aktivujete digitálne podpisovanie:

```
Certificate → vyberte .p12 / .pfx súbor
Password    → heslo k privátneho kľúču
```

Kliknite **📄 Generate Report** – report sa automaticky otvorí po dokončení.

---

### 📋 Reports – správa reportov

Prehľad všetkých vygenerovaných PDF reportov v adresári `report/`.

| Stĺpec | Popis |
|---|---|
| Report name | Názov PDF súboru |
| Created | Dátum a čas vytvorenia |
| Signed | ✅ Signed / ❌ No – stav digitálneho podpisu |

Dostupné akcie: **Open** (otvoriť v systémovom prehliadači), **🗑** (zmazať), **⟳ Refresh** (obnoviť zoznam).

---

## 📐 Stage Presets

Namiesto fixných parametrov je možné definovať viacfázový test cez **stage preset**. Preset vygeneruje `stages.json`, ktorý `Locustfile_http.py` načíta cez `LoadTestShape`.

| Preset | Popis | Trvanie |
|---|---|---|
| **Flat** | Konštantná záťaž – 50 používateľov | 5 min |
| **Stress** | Stupňovanie: 10 → 50 → 100 → 300 používateľov | ~6 min |
| **Spike** | Nárazová záťaž: skok na 500 a späť | ~90 s |
| **Endurance** | Dlhodobý test: 25 používateľov | 2 hod |
| **Capacity** | Stupňovanie throughputu: 10 → 200 používateľov | ~10 min |

**Vlastný preset** môžete definovať priamo v GUI editore stages alebo úpravou `stages.json`:

```json
[
  {"duration": 60, "users": 10, "spawn_rate": 5, "wait_mode": "between", "wait_min": 1.0, "wait_max": 3.0},
  {"duration": 120, "users": 100, "spawn_rate": 20, "wait_mode": "constant", "wait_min": 0.5, "wait_max": 0.5}
]
```

---

## 🧩 Sieťové moduly

### `Create_IP_Pool_skript.py`

Pridáva rozsah IPv4 alebo IPv6 adries na sieťové rozhranie pomocou `sudo ip addr add`. Ukladá zoznam pridaných IP do `ip_pool.txt`.

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

Odstraňuje IP adresy z rozhrania pomocou `sudo ip addr del`. Číta zoznam z `ip_pool.txt` – bezpečné volanie aj pri čiastočne pridanom poole.

### `Network_monitor.py`

Thread-based monitor sieťovej prevádzky čítajúci `/proc/net/dev`. Loguje RX/TX rýchlosť v kB/s do CSV každú sekundu (konfigurovateľné).

```python
monitor = NetworkMonitor(interface="ens33", interval=1, output_file="data/network_usage.csv")
monitor.start()
# ... prebieha test ...
monitor.stop()
```

### `Reachability.py`

Periodicky meria HTTP dostupnosť cieľa z konkrétnej zdrojovej IP. Podporuje IPv6 link-local adresy s automatickým pridaním zóny (`fe80::1%ens33`). Výsledky (timestamp, status_code, elapsed_ms) ukladá do `data/reachability.csv`.

### `Create_topology.py`

Generuje PNG diagram sieťovej topológie pomocou Matplotlib. Vizualizuje vzťah tester → zdrojové IP → cieľ s metadátami rozhrania a IP rozsahu.

### `playwright_recorder.py`

Spúšťa Playwright browser a zaznamenáva HTTP reláciu vrátane requestov, headerov a tela. Výstup je `session.json` pre replay cez `locustfile_playwright.py`.

---

## 📊 PDF Report

Vygenerovaný report je profesionálny A4 PDF dokument s bielym pozadím a zeleným akcentom.

**Štruktúra reportu:**

| # | Sekcia | Obsah |
|---|---|---|
| 1 | **Titulná strana** | Názov testu, dátum, cieľ, zdrojové IP, rozhranie, typ testu |
| 2 | **Test Summary** | Celkový počet requestov, failure rate, trvanie testu |
| 3 | **Performance Statistics** | Tabuľka: min/avg/max/p50/p95/p99 response time, RPS, failures per endpoint |
| 4 | **Response Time Graph** | Časový priebeh odozvy (percentily 50/95/99) |
| 5 | **Requests per Second** | Priebeh throughputu počas testu |
| 6 | **Reachability Graph** | Dostupnosť cieľa (pass/fail) počas testu |
| 7 | **Network Traffic** | RX/TX prevádzka na sieťovom rozhraní |
| 8 | **Network Topology** | Vizuálny diagram testovacieho prostredia |
| 9 | **Komentár** | Vlastná poznámka testera |
| 10 | **Digitálny podpis** | LTV podpis (ak bol aktivovaný) |

---

## 🔏 Digitálne podpisovanie

PDF reporty je možné digitálne podpísať pomocou PKCS#12 certifikátu (`.p12` / `.pfx`) cez knižnicu **pyHanko** s podporou LTV (Long-Term Validation).

### Vytvorenie self-signed certifikátu (pre testovacie účely)

```bash
# 1. Vytvorenie privátneho kľúča a certifikátu
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes \
  -subj "/CN=Locust Test Signer/O=Test Organization"

# 2. Export do PKCS#12 formátu
openssl pkcs12 -export -out report/cert.p12 -inkey key.pem -in cert.pem

# 3. Vyčistenie dočasných súborov
rm key.pem cert.pem
```

### Postup podpisovania v GUI

1. Na karte **Generate Report** zaškrtnite **Sign PDF**
2. Vyberte `.p12` certifikát cez **Browse**
3. Zadajte heslo certifikátu
4. Kliknite **Generate Report**

Podpísané reporty sú označené `✅ Signed` v zozname reportov.

---

## 🎨 Farebné témy

Aplikácia obsahuje 5 vstavaných farebných tém prepínateľných v dolnej časti sidebaru. Zmena témy reštartuje aplikáciu (nastavenia sa zachovajú).

| Téma | Primárny akcentu | Pozadie | Charakter |
|---|---|---|---|
| **Locust Dark** | `#2a5f3a` tmavá zelená | `#111111` | Predvolená, minimalistická |
| **Navy Blue** | `#23395B` tmavomodrá | `#1c2128` | Profesionálna, monochromatická |
| **Discord Light** | `#7289da` fialová | `#36393e` | Discord-inšpirovaná |
| **Discord Darkest** | `#5b73c7` tmavá fialová | `#1a1a1e` | Najtemnejší variant |
| **Netflix** | `#800000` tmavá červená | `#181818` | Čierne pozadie, červený akcentu |

### Pridanie vlastnej témy

V `locust_gui.py` rozšírte slovník `THEMES`:

```python
THEMES["My Theme"] = {
    "BG_SIDEBAR":   "#1a1a2e",
    "BG_MAIN":      "#16213e",
    "BG_CARD":      "#1f2b47",
    "ACCENT":       "#ff6b35",
    "ACCENT_HOVER": "#e55a2b",
    "FG_TEXT":      "#ffffff",
    "FG_MUTED":     "#888888",
    "FG_LABEL":     "#cccccc",
    "FG_HEADER":    "#ff6b35",
    "BG_INPUT":     "#0d0e10",
    "BTN_DANGER":   "#922b21",
    "BTN_START":    "#ff6b35",
    "BTN_REPORT":   "#ff6b35",
    "BTN_SETUP":    "#ff6b35",
}
```

---

## ⌨️ Klávesové skratky

| Skratka | Funkcia |
|---|---|
| `Ctrl` + `+` / `=` | Priblíženie (zoom in) |
| `Ctrl` + `-` | Oddialenie (zoom out) |
| `Ctrl` + `0` | Reset zoomu na 100% |
| `Scroll wheel` | Scrollovanie v zoznamoch a formulároch |

---

## 🔧 Rozšírenie a customizácia

### Vlastný Locustfile

Vytvorte `.py` súbor s Locust testom a vyberte ho cez **Browse** na karte HTTP:

```python
from locust import HttpUser, task, between

class MyUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def homepage(self):
        self.client.get("/")

    @task(1)
    def api_endpoint(self):
        self.client.post("/api/data", json={"key": "value"})
```

### Vlastný Playwright recorder

```bash
# Spustenie – otvorí Chromium browser
python3 network/playwright_recorder.py

# Nahrajte reláciu manuálnym klikaním v browseri
# Po zatvorení sa uloží session.json

# Konfigurácia replay
echo "SESSION_FILE=session.json" >> config.env
echo "TASK_MODE=sequential" >> config.env
```

### Integrácia do CI/CD

```bash
# Headless spustenie testu (bez GUI)
cd Locust_DP_repo
source locust_env/bin/activate

# Priamy Locust príkaz s parametrami
locust -f locust_tests/Locustfile_http.py \
  --headless \
  --users 50 \
  --spawn-rate 10 \
  --run-time 60s \
  --host https://target.example.com \
  --csv data/report
```

---

## 🐛 Riešenie problémov

| Problém | Príčina | Riešenie |
|---|---|---|
| `ModuleNotFoundError: customtkinter` | Závislosti nie sú nainštalované | Spustite `prepare_tester_python.sh` alebo `pip install customtkinter` |
| `Permission denied` pri Setup | Chýbajú sudo práva | Overte, že váš user je v sudoers; app volá `sudo ip addr add` interne |
| GUI sa nespustí (display error) | Nie je dostupný X display | Nastavte `DISPLAY=:0` alebo spustite cez SSH s `-X` flagom |
| PDF sa negeneruje | Chýbajú dáta z testu | Uistite sa, že test prebehol a súbory v `data/` existujú |
| `pyhanko` sign error | Nesprávne heslo alebo formát cert | Overte `.p12` certifikát: `openssl pkcs12 -info -in cert.p12` |
| IPv6 adresy sa nepridajú | Kernel nepodporuje IPv6 | Skontrolujte: `cat /proc/sys/net/ipv6/conf/all/disable_ipv6` (musí byť `0`) |

---

## 📝 Licencia

Tento projekt je distribuovaný pod licenciou **MIT**. Pozri súbor `LICENSE` pre úplné podmienky.

---

## 👤 Autor

Vytvorené v rámci **diplomovej práce**, 2026.

---

<div align="center">

*🦗 Locust Load Test GUI – automatizuj, testuj, analyzuj.*

</div>
