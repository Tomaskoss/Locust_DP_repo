# Locust Load Test GUI

Projekt slúži na spúšťanie záťažových testov pomocou frameworku **Locust** cez jednoduché grafické rozhranie.  
Aplikácia umožňuje nastaviť cieľový server, HTTP/S requesty, IP pool, reachability monitoring, sieťový monitoring a následne vygenerovať PDF report z výsledkov testu.

---

## Hlavné funkcie

- spustenie Locust testu cez GUI,
- podpora HTTP metód `GET` a `POST`,
- možnosť testovať jeden alebo viac endpointov,
- podpora IPv4 aj IPv6,
- generovanie a správa source IP poolu,
- možnosť použiť vlastné source porty alebo OS ephemeral porty,
- viacfázový test pomocou stages,
- reachability monitoring počas testu,
- monitorovanie sieťovej prevádzky,
- generovanie PDF reportu,
- voliteľné zobrazenie detailov chýb v reporte,
- voliteľné podpísanie PDF reportu.

---

## Odporúčaná topológia

Odporúčané je použiť dva stroje v jednej lokálnej sieti:

```text
PC / VM       tester – spúšťa Locust GUI
Notebook      server – prijíma HTTP/S požiadavky
```

Príklad IPv6 konfigurácie:

```text
Tester: fd00:100::72/64
Server: fd00:100::73/64
```

Príklad cieľovej URL:

```text
http://[fd00:100::73]:8080
```

Pri testovaní cez IPv6 je dôležité, aby source IP adresy testera patrili do rovnakej siete ako cieľový server.

---

## Inštalácia na testeri

Najskôr nastav práva pre prípravný skript:

```bash
chmod +x prepare_tester_python.sh
```

Potom spusti prípravu prostredia:

```bash
./prepare_tester_python.sh
```

Skript nainštaluje potrebné systémové balíky, vytvorí virtuálne prostredie `locust_env` a nainštaluje Python knižnice potrebné pre beh projektu.

---

## Spustenie aplikácie

Aktivuj virtuálne prostredie:

```bash
source locust_env/bin/activate
```

Spusti GUI:

```bash
python3 locust_gui.py
```

---

## Základný postup použitia

1. V časti **Config** nastav cieľový server, endpointy, interface a IP pool.
2. Klikni na **Setup IP Pool**.
3. V časti **HTTP/S** nastav testovací scenár, Locust parametre a HTTP metódu.
4. Spusti test cez **Start Test**.
5. Po skončení testu prejdi do **Generate Report**.
6. Vygeneruj PDF report.
7. Po testovaní použi **Cleanup**, aby sa IP adresy odstránili z interface.

---

## Endpointy

Endpointy sa zadávajú do poľa **Endpoint path**.

Jeden endpoint:

```text
/
```

Viac endpointov:

```text
/,/health,/api/status,/api/products
```

Ak endpoint neobsahuje úvodnú lomku, aplikácia ju automaticky doplní.

---

## HTTP/S nastavenia

Podporované metódy:

```text
GET
POST
```

Pri `GET` sa request body nepoužíva.  
Pri `POST` je možné zadať JSON telo požiadavky.

Príklad:

```json
{
  "message": "hello",
  "user": "test"
}
```

---

## Locust stages

Test sa skladá z jednej alebo viacerých fáz. Každá fáza obsahuje:

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

Celkové trvanie testu bude:

```text
60 + 120 + 120 = 300 s
```

---

## Wait mode

Dostupné režimy čakania medzi requestmi:

```text
between
constant
constant_throughput
```

Význam:

```text
between              náhodné čakanie medzi Min a Max
constant             fixné čakanie podľa hodnoty Min
constant_throughput  Min sa používa ako cieľová priepustnosť na používateľa
```

---

## Source ports

Pole **Source ports** je voliteľné.

Ak zostane prázdne, operačný systém použije ephemeral porty automaticky.

Príklad zobrazenia v reporte:

```text
OS ephemeral (32768–60999)
```

Možné ručné zadanie:

```text
1025
```

alebo rozsah:

```text
1024-2000
```

---

## IP Pool

IP pool určuje zdrojové IP adresy, z ktorých sa budú odosielať požiadavky.

Podporované možnosti:

```text
IPv4 range
IPv6 range
IPv6 prefix
Custom pool file
```

Príklad IPv6 poolu:

```text
fd00:100::1000 – fd00:100::1050
```

Odporúčanie:

```text
Server:      fd00:100::73
Tester pool: fd00:100::1000 – fd00:100::1050
```

Tester by nemal používať rovnakú IP adresu ako server.

---

## Reachability monitoring

Reachability monitoring overuje dostupnosť cieľového servera počas testu.  
Je oddelený od Locust requestov.

Nastaviteľné hodnoty:

```text
Source IP
Interface
Interval
Timeout
Failure threshold
```

Reachability threshold sa vyhodnocuje samostatne a nemieša sa s Locust request failure thresholdom.

---

## Report

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

Niektoré časti sa zobrazia iba vtedy, keď majú význam.  
Napríklad detailná tabuľka failures sa zobrazí iba pri zapnutej možnosti **Include failure details table**.

---

## Generované súbory

Počas testovania vznikajú najmä tieto súbory:

```text
data/report_stats.csv
data/report_stats_history.csv
data/report_failures.csv
data/network_usage.csv
data/reachability.csv
data/report_metadata.csv
test_config.csv
ip_pool.txt
port_pool.txt
report/Locust_Report.pdf
```

Tieto súbory predstavujú výstupy konkrétnych testov a bežne sa nemusia ukladať do repozitára.

---

## Odporúčaný .gitignore

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

*.p12
*.pfx
.vscode/
.idea/
```

Projekt je určený ako prototyp nástroja na záťažové testovanie v rámci diplomovej práce.
