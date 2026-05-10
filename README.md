# 🦗 Locust Load Test GUI

> **Grafické rozhranie pre automatizované záťažové testovanie HTTP/HTTPS**  
> Postavené na Pythone, CustomTkinter a Locust frameworku – konfigurácia testu, monitoring a PDF report v jednom nástroji.

<br>

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Linux-FCC624?logo=linux&logoColor=black)
![Locust](https://img.shields.io/badge/Locust-load%20testing-00AA00)
![GUI](https://img.shields.io/badge/GUI-CustomTkinter-9B59B6)
![Status](https://img.shields.io/badge/Status-Prototype-orange)
![License](https://img.shields.io/badge/License-Academic-lightgrey)

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
  - [HTTP/S – spustenie testu](#-https--spustenie-testu)
  - [Generate Report – generovanie PDF](#-generate-report--generovanie-pdf)
  - [Reports – správa reportov](#-reports--správa-reportov)
- [Stage Presets](#-stage-presets)
- [Sieťové moduly](#-sieťové-moduly)
- [PDF Report](#-pdf-report)
- [Digitálne podpisovanie](#-digitálne-podpisovanie)
- [Klávesové skratky](#️-klávesové-skratky)
- [Licencia](#-licencia)
- [Autor](#-autor)

---

## 🔍 O projekte

**Locust Load Test GUI** je desktopová aplikácia pre Linux, ktorá zjednocuje pracovný postup záťažového testovania do jedného grafického rozhrania. Projekt rieši potrebu jednoducho nastaviť záťažový test, spravovať zdrojové IP adresy, sledovať dostupnosť cieľa, monitorovať sieťovú prevádzku a vytvoriť prehľadný PDF report.

Aplikácia je navrhnutá najmä pre testovanie webových služieb v lokálnej sieti, kde môže jeden stroj slúžiť ako tester a druhý ako testovaný server.

**Základný workflow:**

```text
1. CONFIGURE   →   2. TEST   →   3. MONITOR   →   4. REPORT
   IP Pool          Locust        Reachability      PDF + grafy
   Interface        HTTP/S        Network RX/TX     Topológia siete
   Parametre        Stages        Live log          Výsledky testu
```

---

## ✨ Hlavné funkcie

| Kategória | Funkcia | Popis |
|---|---|---|
| 🌐 **Sieť** | IPv4 + IPv6 podpora | Podpora rozsahov aj IPv6 prefix módu |
| 🌐 **Sieť** | IP Pool management | Pridávanie a odstraňovanie source IP adries na sieťové rozhranie |
| 🌐 **Sieť** | Source ports | Vlastný rozsah portov alebo systémové ephemeral porty |
| 🌐 **Sieť** | Network Monitor | Sledovanie RX/TX prevádzky počas testu |
| 🌐 **Sieť** | Reachability Monitor | Priebežné overovanie dostupnosti cieľového servera |
| 🗺️ **Vizualizácia** | Topology Diagram | Automaticky generovaný diagram testovacej topológie |
| 📊 **Reporting** | PDF Export | Report s tabuľkami, grafmi, metadátami a komentárom |
| 🔏 **Bezpečnosť** | PDF Signing | Voliteľné digitálne podpísanie reportu cez PKCS#12 certifikát |
| ⚡ **Záťaž** | Stage Presets | Preddefinované testovacie scenáre: Flat, Stress, Spike, Endurance, Capacity |
| ⚙️ **Konfigurácia** | Persistent config | Nastavenia sa ukladajú do `config.env` |
| 🖥️ **Monitoring** | Real-time log | Live výstup z testu a monitorovacích vlákien v GUI |

---

## 📁 Štruktúra projektu

```text
Locust_DP_repo/
│
├── locust_gui.py                    # Hlavný súbor GUI aplikácie
├── prepare_tester_python.sh         # Inštalačný skript pre tester
├── config.env                       # Konfiguračný súbor
├── requirements.txt                 # Python závislosti
├── ip_pool.txt                      # Aktívny IP pool, generovaný súbor
├── port_pool.txt                    # Aktívny port pool, generovaný súbor
├── test_config.csv                  # Snapshot konfigurácie posledného testu
├── stages.json                      # Konfigurácia fáz testu
│
├── data/                            # Výstupné dáta z testov
│   ├── report_stats.csv
│   ├── report_stats_history.csv
│   ├── report_failures.csv
│   ├── reachability.csv
│   ├── network_usage.csv
│   └── report_metadata.csv
│
├── IP_pool/                         # Uložené IP pool súbory
│
├── report/                          # PDF reporty a reportovací modul
│   ├── Locust_report_v3.py
│   └── Locust_Report.pdf
│
├── network/                         # Sieťové moduly
│   ├── Create_IP_Pool_skript.py
│   ├── Remove_IP_Pool_skript.py
│   ├── Network_monitor.py
│   ├── Reachability.py
│   └── Create_topology.py
│
└── locust_tests/                    # Locust testovacie súbory
    ├── Locustfile_http.py
    └── locustfile_playwright.py
```

Niektoré súbory vznikajú automaticky až počas používania aplikácie.

---

## 📦 Požiadavky

### Systémové požiadavky

| Požiadavka | Odporúčanie | Poznámka |
|---|---|---|
| **OS** | Linux / Ubuntu | Sieťové operácie sú naviazané na Linux |
| **Python** | 3.10+ | Odporúčané použiť virtuálne prostredie |
| **Sieťové rozhranie** | `ens33`, `eth0`, `wlan0`, ... | Musí byť dostupné v systéme |
| **Oprávnenia** | sudo | Potrebné pri pridávaní/odoberaní IP adries |
| **Testovaný server** | HTTP/S server | Server musí byť dostupný z testera |

### Hlavné Python závislosti

```text
locust
customtkinter
CTkToolTip
requests
pandas
matplotlib
reportlab
python-dotenv
pyhanko
```

---

## 🚀 Inštalácia

### Automatická inštalácia

```bash
git clone https://github.com/your_username/Locust_DP_repo.git
cd Locust_DP_repo

chmod +x prepare_tester_python.sh
./prepare_tester_python.sh
```

Skript vykoná najmä:

- inštaláciu potrebných systémových balíkov,
- vytvorenie virtuálneho prostredia `locust_env`,
- inštaláciu Python závislostí,
- vytvorenie základných priečinkov projektu,
- vytvorenie predvoleného `config.env`, ak ešte neexistuje.

### Spustenie po inštalácii

```bash
source locust_env/bin/activate
python3 locust_gui.py
```

---

## ⚙️ Konfigurácia

Konfigurácia sa ukladá do súboru `config.env`. Hodnoty z GUI sa do tohto súboru ukladajú automaticky.

Príklad konfigurácie:

```env
TARGET_HOST='http://[fd00:100::73]:8080'
PROCESSES='-1'
TEST_TYPE='Load Test'
STOP_TIMEOUT='30'
CONNECT_TIMEOUT='3'
READ_TIMEOUT='10'

HTTP_METHOD='GET'
ENDPOINT_PATH='/,/health,/api/status,/api/products'
REQUEST_BODY='{"message": "hello", "user": "test"}'
SSL_VERIFY='false'
REQUEST_FAILURE_THRESHOLD='1'

INTERFACE='ens33'
IP_VERSION='ipv6'

IP_START='192.168.10.10'
IP_END='192.168.100.200'
IPV4PREFIX='28'

IP6_START='fd00:100::1000'
IP6_END='fd00:100::1050'
IP6_PREFIX='fd00:100::/64'
IPV6_MODE='range'
IPV6RPREFIX='64'

REACH_INTERVAL='5'
REACH_TIMEOUT='5'
REACH_SRC_IP='fd00:100::1000'
REACH_INTERFACE='ens33'
REACH_THRESHOLD='5'
```

---

## 🖥️ Používanie

Po spustení aplikácie sa zobrazí GUI so štyrmi hlavnými časťami:

```text
Config
HTTP/S
Generate Report
Reports
```

---

### ⚙️ Config – nastavenia

V tejto časti sa nastavuje cieľový server, endpointy, IP pool, source porty, reachability monitoring a sieťový monitoring.

#### General

| Parameter | Popis | Príklad |
|---|---|---|
| Target host | URL testovaného servera | `http://[fd00:100::73]:8080` |
| Endpoint path | Jeden alebo viac endpointov | `/,/health,/api/status` |
| Interface | Hlavné sieťové rozhranie | `ens33` |
| Test type | Popis testu do reportu | `Load Test` |
| Source ports | Voliteľný port alebo rozsah portov | `1024-2000` |
| Request failure threshold | Povolené percento request failures | `1` |

Endpointy je možné zadať ako zoznam oddelený čiarkou:

```text
/,/health,/api/status,/api/products
```

Ak endpoint nemá úvodnú lomku, aplikácia ju automaticky doplní.

#### IP Pool

Podporované režimy:

```text
IPv4 range
IPv6 range
IPv6 prefix
Custom pool file
```

Príklad IPv6 rozsahu:

```text
fd00:100::1000 – fd00:100::1050
```

Odporúčanie:

```text
Server:      fd00:100::73
Tester pool: fd00:100::1000 – fd00:100::1050
```

Tester by nemal používať rovnakú IP adresu ako server.

#### Reachability

| Parameter | Popis |
|---|---|
| Interval | Ako často sa overuje dostupnosť servera |
| Timeout | Maximálny čas čakania na odpoveď |
| Source IP | Zdrojová IP pre reachability požiadavky |
| Interface | Rozhranie pre reachability monitoring |
| Failure threshold | Povolené percento zlyhaných reachability kontrol |

Reachability threshold sa vyhodnocuje oddelene od Locust request failure thresholdu.

#### Actions

| Tlačidlo | Popis |
|---|---|
| **Setup IP Pool** | Pridá IP adresy z poolu na sieťové rozhranie |
| **Save Pool** | Uloží aktuálny IP pool do priečinka `IP_pool/` |
| **Cleanup** | Odstráni IP adresy z rozhrania |

---

### 🌐 HTTP/S – spustenie testu

V tejto časti sa nastavuje testovací scenár, Locust parametre a HTTP metóda.

#### Define Test

Test je rozdelený do stages. Každá fáza obsahuje:

```text
Duration (s)
Users
Spawn rate
Wait mode
Min
Max
```

Hodnota `Duration (s)` znamená trvanie konkrétnej fázy, nie kumulatívny čas.

Príklad:

```text
Stage 1: 60 s, 10 users
Stage 2: 120 s, 50 users
Stage 3: 120 s, 100 users
```

Celkové trvanie:

```text
60 + 120 + 120 = 300 s
```

#### Wait mode

| Režim | Význam |
|---|---|
| `between` | Náhodné čakanie medzi Min a Max |
| `constant` | Fixné čakanie podľa hodnoty Min |
| `constant_throughput` | Min sa používa ako cieľová priepustnosť na používateľa |

#### Locust Parameters

| Parameter | Popis |
|---|---|
| Stop timeout | Čas, ktorý Locust čaká na dokončenie bežiacich taskov |
| Processes | Počet Locust procesov, `-1` znamená automaticky podľa CPU |
| Connect timeout | Timeout pre nadviazanie TCP spojenia |
| Read timeout | Timeout pre čakanie na odpoveď servera |

#### Request Settings

Podporované HTTP metódy:

```text
GET
POST
```

Pri `GET` sa request body nepoužíva.  
Pri `POST` je možné zadať JSON request body:

```json
{
  "message": "hello",
  "user": "test"
}
```

Kliknutím na **Start Test** sa spustí:

```text
Locust test
Reachability monitoring
Network monitoring
```

Výstup je dostupný v paneli **Output Log**.

---

### 📄 Generate Report – generovanie PDF

Po dokončení testu je možné vygenerovať PDF report.

| Parameter | Popis |
|---|---|
| Report name | Názov PDF súboru |
| Save to | Cieľový priečinok |
| Comment | Voliteľný komentár do reportu |
| Include failure details table | Zobrazí detailnú tabuľku chýb |
| Sign PDF | Voliteľné podpísanie reportu |

PDF report obsahuje najmä:

```text
Test Information
Performance Overview
Test Stages
Network Topology
Reachability
Time Series Charts
Network Traffic Analysis
Failure Details
```

Niektoré časti sa zobrazujú iba vtedy, keď majú význam.

---

### 📋 Reports – správa reportov

Táto časť slúži na prezeranie vygenerovaných PDF reportov.

| Akcia | Popis |
|---|---|
| Open | Otvorí PDF report |
| Delete | Odstráni PDF report |
| Refresh | Obnoví zoznam reportov |

---

## 📐 Stage Presets

Aplikácia obsahuje preddefinované profily záťaže.

| Preset | Popis |
|---|---|
| **Flat** | Konštantná záťaž |
| **Stress** | Postupné zvyšovanie záťaže |
| **Spike** | Krátkodobý prudký nárast záťaže |
| **Endurance** | Dlhodobý test stability |
| **Capacity** | Postupné hľadanie kapacity systému |

Stages sa ukladajú do súboru:

```text
stages.json
```

---

## 🧩 Sieťové moduly

### `Create_IP_Pool_skript.py`

Pridáva IP adresy na sieťové rozhranie a zapisuje ich do `ip_pool.txt`.

### `Remove_IP_Pool_skript.py`

Odstraňuje IP adresy z rozhrania podľa obsahu `ip_pool.txt`.

### `Network_monitor.py`

Monitoruje RX/TX prevádzku zo sieťového rozhrania a zapisuje výsledky do `data/network_usage.csv`.

### `Reachability.py`

Priebežne overuje dostupnosť cieľového servera a zapisuje výsledky do `data/reachability.csv`.

### `Create_topology.py`

Generuje topologický diagram testovacieho prostredia.

---

## 📊 PDF Report

PDF report je generovaný modulom:

```text
report/Locust_report_v3.py
```

Report využíva CSV súbory vytvorené počas testu:

```text
data/report_stats.csv
data/report_stats_history.csv
data/report_failures.csv
data/network_usage.csv
data/reachability.csv
data/report_metadata.csv
test_config.csv
```

Hodnoty použité v reporte sa viažu na snapshot konkrétneho testu, nie iba na aktuálny stav GUI.

---

## 🔏 Digitálne podpisovanie

PDF report je možné podpísať certifikátom vo formáte:

```text
.p12
.pfx
```

V GUI je potrebné nastaviť:

```text
Certificate
Password
```

Certifikáty a súkromné kľúče sa nemajú ukladať do verejného repozitára.

---

## ⌨️ Klávesové skratky

| Skratka | Funkcia |
|---|---|
| `Ctrl` + `+` / `=` | Priblíženie |
| `Ctrl` + `-` | Oddialenie |
| `Ctrl` + `0` | Reset zoomu |

---

### IPv6 príklad

Nesprávne:

```text
Source IP: fd00::100
Target:    fd00:100::73
```

Správne:

```text
Source IP: fd00:100::1000
Target:    fd00:100::73
```

### Link-local IPv6 príklad

```text
http://[fe80::20c:29ff:fe7e:a4b0%25ens33]:8080
```

---

## 🧹 Odporúčaný `.gitignore`

```gitignore
__pycache__/
*.pyc
locust_env/

data/*.csv
report/*.pdf
report/*.png

ip_pool.txt
port_pool.txt
test_config.csv
stages.json

*.p12
*.pfx

.vscode/
.idea/
```

---

## 📝 Licencia

Projekt je určený na akademické a testovacie účely. Licenciu je možné upraviť podľa požiadaviek repozitára alebo školy.

---

## 👤 Autor

Vytvorené ako prototyp nástroja na záťažové testovanie v rámci diplomovej práce.

---

<div align="center">

*🦗 Locust Load Test GUI – konfiguruj, testuj, monitoruj, reportuj.*

</div>
