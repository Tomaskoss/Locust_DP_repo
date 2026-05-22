🦗 Locust Load Test GUI
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
📋 Obsah
O projekte
Hlavné funkcie
Štruktúra projektu
Požiadavky
Inštalácia
Konfigurácia
Používanie
Config – nastavenia
HTTP/S – spustenie testu
Generate Report – generovanie PDF
Reports – správa reportov
Stage Presets
Sieťové moduly
PDF Report
Digitálne podpisovanie
Klávesové skratky
Licencia
Autor
---
🔍 O projekte
Locust Load Test GUI je desktopová aplikácia pre Linux, ktorá zjednocuje pracovný postup záťažového testovania do jedného grafického rozhrania. Projekt umožňuje nastaviť HTTP/HTTPS záťažový test, spravovať zdrojové IP adresy, sledovať dostupnosť cieľa, monitorovať sieťovú prevádzku a vytvoriť PDF report s výsledkami.
Aplikácia je navrhnutá najmä pre testovanie webových služieb v lokálnej alebo laboratórnej sieti, kde jeden stroj slúži ako tester a druhý ako testovaný server.
Základný workflow:
```text
1. CONFIGURE   →   2. TEST   →   3. MONITOR   →   4. REPORT
   IP Pool          Locust        Reachability      PDF + grafy
   Interface        HTTP/S        Network RX/TX     Topológia siete
   Parametre        Stages        Live log          Výsledky testu
```
---
✨ Hlavné funkcie
Kategória	Funkcia	Popis
🌐 Sieť	IPv4 + IPv6 podpora	Podpora IPv4 rozsahu, IPv6 rozsahu a IPv6 prefix módu
🌐 Sieť	IP Pool management	Pridávanie, uloženie a odstraňovanie source IP adries na sieťovom rozhraní
🌐 Sieť	Custom IP pool	Možnosť načítať vlastný `.txt` súbor so zoznamom IP adries
🌐 Sieť	Source ports	Vlastný port, rozsah portov alebo systémové ephemeral porty
🌐 Sieť	Network Monitor	Záznam RX/TX prevádzky počas testu do CSV súboru
🌐 Sieť	Reachability Monitor	Priebežné overovanie dostupnosti cieľového servera počas testu
🗺️ Vizualizácia	Topology Diagram	Generovanie diagramu testovacej topológie do reportu
📊 Reporting	PDF Export	Report s tabuľkami, grafmi, metadátami, komentárom a voliteľnou tabuľkou chýb
🔏 Bezpečnosť	PDF Signing	Voliteľné digitálne podpísanie reportu cez PKCS#12 certifikát
⚡ Záťaž	Stage Presets	Preddefinované scenáre: Flat, Stress, Spike, Endurance, Capacity
⚙️ Konfigurácia	Persistent config	Nastavenia z GUI sa ukladajú do `config.env`
🖥️ Monitoring	Real-time log	Live výstup z testu, reachability a monitorovacích vlákien v GUI
🎭 Replay	Voliteľný Playwright replay	Možnosť prehrať requesty zo súboru `session.json` cez samostatný Locustfile
---
📁 Štruktúra projektu
```text
Locust_DP_repo/
│
├── README.md                        # Popis projektu a návod na použitie
├── .gitignore                       # Súbory, ktoré sa nemajú verzovať
├── locust_gui.py                    # Hlavný súbor GUI aplikácie
├── prepare_tester_python.sh         # Inštalačný skript pre tester
├── config.env                       # Lokálna konfigurácia aplikácie
├── stages.json                      # Aktuálne fázy záťažového testu
├── vut_logo.png                     # Logo použité v PDF reporte
│
├── ip_pool.txt                      # Generovaný aktívny IP pool
├── port_pool.txt                    # Generovaný aktívny port pool
├── test_config.csv                  # Snapshot konfigurácie posledného testu
├── requirements.txt                 # Vytvorí sa inštalačným skriptom, ak chýba
│
├── data/                            # Výstupné dáta z testov
│   ├── .gitkeep
│   ├── report_stats.csv             # Generuje Locust
│   ├── report_stats_history.csv     # Generuje Locust
│   ├── report_failures.csv          # Generuje Locust
│   ├── reachability.csv             # Generuje Reachability.py
│   ├── network_usage.csv            # Generuje Network_monitor.py
│   └── report_metadata.csv          # Generuje Locustfile
│
├── IP_pool/                         # Uložené IP pool súbory
│   └── .gitkeep
│
├── report/                          # PDF reporty a reportovací modul
│   ├── Locust_report_v3.py
│   ├── Locust_Report.pdf            # Generovaný report
│   └── cert.p12                     # Voliteľný lokálny certifikát, nezverejňovať
│
├── network/                         # Sieťové a pomocné moduly
│   ├── Create_IP_Pool_skript.py
│   ├── Remove_IP_Pool_skript.py
│   ├── Network_monitor.py
│   ├── Reachability.py
│   ├── Create_topology.py
│   └── playwright_recorder.py
│
└── locust_tests/                    # Locust testovacie súbory
    ├── Locustfile_http.py           # Predvolený HTTP/HTTPS test
    ├── locustfile_playwright.py     # Voliteľný replay zo session.json
    └── report.html                  # Generovaný/samostatný HTML výstup Locustu
```
Niektoré súbory vznikajú automaticky až počas používania aplikácie. Ide najmä o `ip_pool.txt`, `port_pool.txt`, `test_config.csv`, CSV súbory v priečinku `data/` a PDF reporty v priečinku `report/`.
---
📦 Požiadavky
Systémové požiadavky
Požiadavka	Odporúčanie	Poznámka
OS	Linux / Ubuntu	Sieťové operácie sú naviazané na Linux
Python	3.10+	Odporúčané použiť virtuálne prostredie
Sieťové rozhranie	napr. `ens33`, `eth0`, `eth2`	Musí existovať v systéme testera
Oprávnenia	sudo	Potrebné pri pridávaní/odoberaní IP adries
Testovaný server	HTTP alebo HTTPS server	Server musí byť dostupný z testera
Hlavné Python závislosti
```text
locust
requests
pandas
matplotlib
reportlab
python-dotenv
customtkinter
CTkToolTip
pyhanko
```
Pre voliteľné nahrávanie browser session cez `network/playwright_recorder.py` je potrebný ešte Playwright:
```bash
pip install playwright
playwright install chromium
```
---
🚀 Inštalácia
Automatická inštalácia
```bash
git clone https://github.com/Tomaskoss/Locust_DP_repo.git
cd Locust_DP_repo

chmod +x prepare_tester_python.sh
./prepare_tester_python.sh
```
Skript vykoná najmä:
inštaláciu potrebných systémových balíkov,
vytvorenie virtuálneho prostredia `locust_env`,
vytvorenie `requirements.txt`, ak v projekte chýba,
inštaláciu Python závislostí,
vytvorenie základných priečinkov projektu,
vytvorenie predvoleného `config.env`, ak ešte neexistuje.
Spustenie po inštalácii
```bash
source locust_env/bin/activate
python3 locust_gui.py
```
---
⚙️ Konfigurácia
Konfigurácia sa ukladá do súboru `config.env`. Hodnoty z GUI sa do tohto súboru ukladajú automaticky pri spustení testu.
Príklad aktuálnej konfigurácie:
```env
TARGET_HOST='http://127.0.0.1:8080'
PROCESSES='-1'
TEST_TYPE='Load Test'
STOP_TIMEOUT='30'
CONNECT_TIMEOUT='3'
READ_TIMEOUT='10'

HTTP_METHOD='GET'
ENDPOINT_PATH='/,/health,/api/status,/api/products'
REQUEST_BODY='{"message": "hello", "user": "test"}'
SSL_VERIFY='false'
ACCEPT_ENCODING=''
REQUEST_FAILURE_THRESHOLD='1'

INTERFACE='ens33'
IP_VERSION='ipv4'

IP_START='192.168.100.100'
IP_END='192.168.100.120'
IPV4PREFIX='32'

IP6_START='fd00:100::1000'
IP6_END='fd00:100::1050'
IP6_PREFIX='fd00:100::/64'
IPV6_MODE='range'
IPV6RPREFIX='64'

REACH_INTERVAL='5'
REACH_TIMEOUT='5'
REACH_SRC_IP=''
REACH_INTERFACE='ens33'
REACH_THRESHOLD='5'

STAGES='[{"duration": 60, "users": 10, "spawn_rate": 5, "wait_mode": "between", "wait_min": 1.0, "wait_max": 3.0}]'
```
Dôležité je, že počet používateľov, spawn rate a trvanie testu sa v GUI riadia cez `STAGES` a `stages.json`. Staršie premenné typu `USERS`, `SPAWN_RATE`, `RUN_TIME`, `WAIT_MODE`, `WAIT_MIN` a `WAIT_MAX` nie sú hlavným zdrojom nastavenia pre aktuálny GUI workflow.
---
🖥️ Používanie
Po spustení aplikácie sa zobrazí GUI so štyrmi hlavnými časťami:
```text
Config
HTTP/S
Generate Report
Reports
```
---
⚙️ Config – nastavenia
V tejto časti sa nastavuje cieľový server, endpointy, IP pool, source porty, reachability monitoring a sieťový monitoring.
General
Parameter	Popis	Príklad
Target host	URL testovaného servera	`http://[fd00:100::73]:8080`
Endpoint path	Jeden alebo viac endpointov	`/,/health,/api/status`
Interface	Hlavné sieťové rozhranie	`ens33`
Test type	Popis testu do reportu	`Load Test`
Source ports	Voliteľný port, zoznam alebo rozsah portov	`1024-2000`
Request failure threshold	Povolené percento Locust request failures	`1`
Verify SSL certificate	Zapne alebo vypne overovanie HTTPS certifikátu	`true/false`
Disable compression	Odošle hlavičku `Accept-Encoding: identity`	vhodné pri meraní reálnej sieťovej priepustnosti
Endpointy je možné zadať ako zoznam oddelený čiarkou:
```text
/,/health,/api/status,/api/products
```
Ak endpoint nemá úvodnú lomku, aplikácia ju automaticky doplní.
IP Pool
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
Príklad vlastného pool súboru:
```text
fd00:100::1000/64
fd00:100::1001/64
fd00:100::1002/64
```
Odporúčanie:
```text
Server:      fd00:100::73
Tester pool: fd00:100::1000 – fd00:100::1050
```
Tester by nemal používať rovnakú IP adresu ako server. Aplikácia sa pri generovaní poolu snaží vylúčiť cieľovú IP adresu, aby sa znížilo riziko konfliktu.
Reachability
Parameter	Popis
Interval	Ako často sa overuje dostupnosť servera
Timeout	Maximálny čas čakania na odpoveď
Source IP	Zdrojová IP pre reachability požiadavky; ak je prázdna, použije sa prvá IP z poolu
Interface	Rozhranie pre reachability monitoring
Failure threshold	Povolené percento zlyhaných reachability kontrol
Reachability threshold sa vyhodnocuje oddelene od Locust request failure thresholdu.
Actions
Tlačidlo	Popis
Setup IP Pool	Pridá IP adresy z poolu na sieťové rozhranie a vytvorí/aktualizuje `ip_pool.txt`
Save Pool	Uloží aktuálny IP pool do priečinka `IP_pool/`; podporuje aj merge s existujúcim poolom
Cleanup	Odstráni IP adresy z rozhrania podľa `ip_pool.txt`
---
🌐 HTTP/S – spustenie testu
V tejto časti sa nastavuje testovací scenár, Locust parametre, HTTP metóda a použitý Locustfile.
Define Test
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
Wait mode
Režim	Význam
`between`	Náhodné čakanie medzi Min a Max
`constant`	Fixné čakanie podľa hodnoty Min
`constant_throughput`	Min sa používa ako cieľová priepustnosť na používateľa
Locust Parameters
Parameter	Popis
Stop timeout	Čas, ktorý Locust čaká na dokončenie bežiacich taskov
Processes	Počet Locust procesov; `-1` znamená automaticky podľa CPU
Connect timeout	Timeout pre nadviazanie TCP spojenia
Read timeout	Timeout pre čakanie na odpoveď servera
Request Settings
Podporované HTTP metódy v predvolenom `Locustfile_http.py`:
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
Locustfile
Predvolený testovací súbor je:
```text
locust_tests/Locustfile_http.py
```
Cez tlačidlo Browse je možné vybrať aj iný `.py` súbor. Súčasťou repozitára je aj voliteľný replay súbor:
```text
locust_tests/locustfile_playwright.py
```
Pri Playwright replay režime je potrebné mať pripravený súbor `session.json`, ktorý je možné vytvoriť pomocou:
```bash
python3 network/playwright_recorder.py http://example.local 20
```
Následne sa v GUI vyberie `locustfile_playwright.py` ako Locustfile.
Kliknutím na Start Test sa spustí:
```text
Locust test
Reachability monitoring
Network monitoring
```
Tlačidlo Stop ukončí Locust proces vrátane jeho procesovej skupiny a zastaví monitorovanie.
Výstup je dostupný v paneli Output Log.
---
📄 Generate Report – generovanie PDF
Po dokončení testu je možné vygenerovať PDF report.
Parameter	Popis
Report name	Názov PDF súboru
Save to	Cieľový priečinok
Comment	Voliteľný komentár do reportu
Include failure details table	Zobrazí detailnú tabuľku chýb
Sign PDF	Voliteľné podpísanie reportu
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
Niektoré časti sa zobrazujú iba vtedy, keď majú dostupné vstupné dáta. Tlačidlo Delete Data odstráni CSV výstupy z priečinka `data/` a súbor `test_config.csv`.
---
📋 Reports – správa reportov
Táto časť slúži na prezeranie vygenerovaných PDF reportov z priečinka `report/`.
Akcia	Popis
Open	Otvorí PDF report
Delete	Odstráni PDF report
Refresh	Obnoví zoznam reportov
---
📐 Stage Presets
Aplikácia obsahuje preddefinované profily záťaže.
Preset	Popis
Flat	Konštantná záťaž
Stress	Postupné zvyšovanie záťaže a následné zníženie
Spike	Krátkodobý prudký nárast záťaže
Endurance	Dlhodobý test stability
Capacity	Postupné hľadanie kapacity systému s režimom `constant_throughput`
Stages sa ukladajú do súboru:
```text
stages.json
```
Pri spustení testu sa zároveň ukladajú aj do premennej `STAGES` v `config.env`.
---
🧩 Sieťové moduly
`Create_IP_Pool_skript.py`
Pridáva IP adresy na sieťové rozhranie a zapisuje ich do `ip_pool.txt`. Podporuje IPv4, IPv6, rozsah adries aj vlastný zoznam IP adries.
`Remove_IP_Pool_skript.py`
Odstraňuje IP adresy z rozhrania podľa obsahu `ip_pool.txt`.
`Network_monitor.py`
Monitoruje RX/TX prevádzku zo sieťového rozhrania a zapisuje výsledky do `data/network_usage.csv`.
`Reachability.py`
Priebežne overuje dostupnosť cieľového servera a zapisuje výsledky do `data/reachability.csv`. Pri nastavení `REACH_SRC_IP` sa pokúša odosielať kontrolné požiadavky zo zvolenej zdrojovej IP adresy.
`Create_topology.py`
Generuje topologický diagram testovacieho prostredia pre PDF report.
`playwright_recorder.py`
Voliteľný pomocný skript, ktorý pomocou Playwrightu navštívi stránky na rovnakej doméne a uloží zachytené requesty do `session.json`.
---
📊 PDF Report
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
stages.json
```
Hodnoty použité v reporte sa viažu na snapshot konkrétneho testu, nie iba na aktuálny stav GUI. Preto sa pred spustením testu vytvára `test_config.csv`.
---
🔏 Digitálne podpisovanie
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
Ak existuje súbor `report/cert.p12`, GUI ho môže predvyplniť ako predvolenú cestu. Certifikáty a súkromné kľúče by sa však nemali ukladať do verejného repozitára. Pre verejný GitHub je vhodné súbory `*.p12` a `*.pfx` odstrániť a ponechať ich iba lokálne na testeri.
---
⌨️ Klávesové skratky
Skratka	Funkcia
`Ctrl` + `+` / `=`	Priblíženie
`Ctrl` + `-`	Oddialenie
`Ctrl` + `0`	Reset zoomu
---
IPv6 príklad
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
Link-local IPv6 príklad
```text
http://[fe80::20c:29ff:fe7e:a4b0%25ens33]:8080
```
---
🧹 Odporúčaný `.gitignore`
```gitignore
__pycache__/
*.pyc
*.pyo
locust_env/

# lokálna konfigurácia a prostredie
config.env
*.env

# výstupy testov
data/*.csv
report/*.pdf
report/*.png
locust_tests/report.html

test_config.csv
ip_pool.txt
port_pool.txt
session.json
network/local_session.json

# certifikáty a súkromné kľúče
*.p12
*.pfx

# IDE / OS
.vscode/
.idea/
.DS_Store
Thumbs.db

# ponechanie prázdnych priečinkov v repozitári
!data/.gitkeep
!IP_pool/.gitkeep
```
Ak má byť v repozitári uložený predvolený `stages.json`, netreba ho pridávať do `.gitignore`. Ak sa má správať ako lokálny výstup GUI, je možné ho ignorovať.
---
📝 Licencia
Projekt je určený na akademické a testovacie účely. Licenciu je možné upraviť podľa požiadaviek repozitára alebo školy.
---
👤 Autor
Vytvorené ako prototyp nástroja na záťažové testovanie v rámci diplomovej práce.
---
<div align="center">
🦗 Locust Load Test GUI – konfiguruj, testuj, monitoruj, reportuj.
</div>
