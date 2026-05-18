# VM Reporting – Projektdokumentation

## Projektziel

Ziel des Projektes ist die Entwicklung einer modularen Python-Anwendung zur automatisierten Erfassung, Verarbeitung, Bewertung und Berichterstellung von VMware-vCenter-Metriken.

Die Anwendung sammelt regelmäßig historische Leistungsdaten virtueller Maschinen, speichert Rohdaten in einer relationalen Datenbank, aggregiert diese monatlich und erzeugt HTML-Reports zur Bewertung der Ressourcenauslastung.

Erfasste Metriken:

- CPU-Auslastung
- Arbeitsspeicherauslastung
- Storage-Auslastung

Die Anwendung soll:

- unter Windows ausführbar sein
- automatisierbar sein
- robust gegenüber fehlenden Metriken arbeiten
- modular erweiterbar bleiben
- fachlich nachvollziehbare Reports erzeugen

---

# Architekturübersicht

Die Anwendung verwendet eine mehrschichtige Architektur.

```text
CLI
→ Services
→ Technical Modules
→ Repositories
→ Database
```

Dadurch werden:

- Präsentationslogik
- Geschäftslogik
- technische Integrationen
- Datenzugriff

sauber voneinander getrennt.

---

# Projektstruktur

```text
app/
├── cli/
│   ├── commands.py
│   └── debug_commands.py
│
├── collectors/
│   └── metric_collector.py
│
├── config/
│   ├── settings.py
│   ├── threshold_loader.py
│   └── thresholds.yaml
│
├── database/
│   ├── connection.py
│   ├── models.py
│   └── repositories.py
│
├── processing/
│   ├── aggregation.py
│   └── evaluation.py
│
├── reporting/
│   ├── html_report.py
│   └── templates/
│       └── report_template.html
│
├── services/
│   ├── aggregation_service.py
│   ├── collection_service.py
│   ├── reporting_service.py
│   └── workflow_service.py
│
├── utils/
│   └── date_utils.py
│
├── vcenter/
│   ├── factory.py
│   └── pyvmomi_client.py
│
└── main.py
```

---

# Datenmodell

## virtual_machines

Speichert Stammdaten virtueller Maschinen.

| Feld | Beschreibung |
|---|---|
| id | Interne Datenbank-ID |
| moid | VMware Managed Object ID |
| name | Anzeigename der VM |
| created_at | Erstellungszeitpunkt |

---

## collection_runs

Dokumentiert jeden Sammellauf.

| Feld | Beschreibung |
|---|---|
| id | Primärschlüssel |
| started_at | Startzeit des Runs |
| finished_at | Endzeit des Runs |
| period_start | Beginn des abgefragten Zeitraums |
| period_end | Ende des abgefragten Zeitraums |
| status | SUCCESS / FAILED |
| processed_vm_count | Anzahl verarbeiteter VMs |
| created_metric_record_count | Anzahl erzeugter MetricRecords |
| error_message | Fehlermeldung |

---

## metric_records

Speichert Rohmetriken einzelner Messpunkte.

| Feld | Beschreibung |
|---|---|
| id | Primärschlüssel |
| vm_id | Referenz auf VM |
| collection_run_id | Referenz auf CollectionRun |
| timestamp | Messzeitpunkt |
| power_state | POWERED_ON / POWERED_OFF |
| cpu_usage_percent | CPU-Auslastung |
| memory_usage_percent | RAM-Auslastung |
| storage_usage_percent | Storage-Auslastung |

### Besonderheit

CPU-, RAM- und Storagewerte sind nullable.

Dadurch bleibt die Anwendung robust gegenüber:

- fehlenden VMware-Metriken
- ausgeschalteten VMs
- Templates
- fehlenden VMware-Tools
- unvollständigen Gastinformationen

Der timestamp bleibt fachlich verpflichtend.

---

## monthly_aggregates

Speichert aggregierte Monatswerte.

| Feld | Beschreibung |
|---|---|
| vm_id | Referenz auf VM |
| month | YYYY-MM |
| metric_record_count | Anzahl berücksichtigter Rohdaten |
| cpu_avg_percent | Durchschnitt CPU |
| cpu_min_percent | Minimum CPU |
| cpu_max_percent | Maximum CPU |
| memory_avg_percent | Durchschnitt RAM |
| memory_min_percent | Minimum RAM |
| memory_max_percent | Maximum RAM |
| storage_avg_percent | Durchschnitt Storage |
| storage_min_percent | Minimum Storage |
| storage_max_percent | Maximum Storage |

Alle Aggregatwerte sind nullable.

---

## evaluation_results

Speichert Bewertungsresultate.

| Feld | Beschreibung |
|---|---|
| overall_status | Gesamtstatus |
| cpu_status | CPU-Bewertung |
| memory_status | RAM-Bewertung |
| storage_status | Storage-Bewertung |

Statuswerte:

- UNDERUTILIZED
- NORMAL
- WARNING
- CRITICAL
- NO_DATA

---

# vCenter-Anbindung

Die VMware-Kommunikation erfolgt über pyVmomi.

## pyVmomiClient

Die Klasse kapselt:

- Verbindungsaufbau
- VM-Abfrage
- Counter-Abfrage
- historische Metrikabfragen
- Storageberechnung

---

# Historische CPU- und RAM-Metriken

CPU- und RAM-Werte werden über den VMware PerformanceManager abgefragt.

Verwendete Counter:

| Metrik | Counter |
|---|---|
| CPU | cpu.usage.average |
| RAM | mem.usage.average |

Die Werte werden historisch für ein Zeitfenster abgefragt.

---

# Storage-Auslastung

Die Storage-Auslastung wird nicht über den VMware PerformanceManager ermittelt.

Stattdessen wird die Gast-Dateisystembelegung verwendet:

```python
vm.guest.disk
```

Dadurch entsteht eine realistischere Auslastung innerhalb des Betriebssystems.

Berechnung:

```text
used_percent =
(capacity - freeSpace) / capacity * 100
```

Die Werte aller Laufwerke werden summiert.

Vorteile:

- reale Gastbelegung
- keine Thin-Provisioning-Verfälschung
- keine Werte >100%
- verständlichere Reports

Einschränkungen:

- VMware Tools erforderlich
- Gastinformationen müssen verfügbar sein

---

# Aggregation

Die Aggregation erfolgt in:

```text
app/processing/aggregation.py
```

Berechnet werden:

- Durchschnitt
- Minimum
- Maximum

Die Aggregation ist vollständig None-sicher.

Fehlende Werte werden ignoriert.

Beispiel:

```python
[10, 20, None, 30]
→ Durchschnitt = 20
```

Wenn keine gültigen Werte vorhanden sind:

```python
None
```

---

# Bewertungssystem

Die Bewertung erfolgt in:

```text
app/processing/evaluation.py
```

Thresholds werden extern geladen.

---

## thresholds.yaml

```yaml
cpu:
  underutilized_below: 20
  warning_above: 70
  critical_above: 90
```

Dies ermöglicht:

- fachliche Anpassung ohne Codeänderung
- bessere Wartbarkeit
- klare Trennung von Logik und Konfiguration

---

# Overall-Status

Die Gesamtbewertung wird aus Einzelbewertungen bestimmt.

Priorität:

```text
CRITICAL
→ WARNING
→ UNDERUTILIZED
→ NORMAL
```

Fehlende Einzelmetriken werden ignoriert.

Dadurch werden VMs mit:

```text
CPU = UNDERUTILIZED
RAM = UNDERUTILIZED
Storage = NORMAL
```

insgesamt als:

```text
NORMAL
```

bewertet.

---

# Service-Schicht

Die Services kapseln Geschäftslogik.

## collection_service.py

Startet die Metrikerfassung.

```text
CLI
→ collection_service
→ metric_collector
```

---

## aggregation_service.py

Führt Monatsaggregation und Bewertung durch.

```text
CLI
→ aggregation_service
→ aggregation/evaluation
→ repositories
```

---

## reporting_service.py

Erzeugt HTML-Reports.

```text
CLI
→ reporting_service
→ html_report
```

---

## workflow_service.py

Orchestriert den Monatsworkflow.

Ablauf:

```text
monthly-workflow
├── determine previous month
├── aggregate
├── check for data
└── report
```

Dadurch entstehen keine verschachtelten CLI-Aufrufe.

---

# HTML-Reporting

Die Reports werden erzeugt in:

```text
output/reports/
```

Dateiname:

```text
report_YYYY-MM.html
```

---

# Report-Inhalt

Der HTML-Report enthält:

## Summary Cards

- Anzahl VMs
- Anzahl WARNING
- Anzahl CRITICAL
- Anzahl UNDERUTILIZED

---

## Top Consumers

Anzeige der höchsten Verbraucher für:

- CPU
- RAM
- Storage

Mit farblicher Statusmarkierung.

---

## Haupttabelle

Enthält:

- VM-Name
- Durchschnittswerte
- Statuswerte
- Overall-Status

---

# Tabellenfunktionen

Die Haupttabelle unterstützt:

- clientseitige Sortierung
- Klick auf Tabellenkopf
- aufsteigende/absteigende Sortierung
- visuelle Dreiecke zur Sortierrichtung

---

# Farbsystem

Verwendete Statusfarben:

| Status | Farbe |
|---|---|
| UNDERUTILIZED | Blau |
| NORMAL | Grün |
| WARNING | Orange |
| CRITICAL | Rot |
| NO_DATA | Grau |

Die Reports enthalten:

- Statuslegende
- farbige Statuspunkte
- farbige Top-Consumer-Markierungen

---

# Debug-Commands

Unterkommandos:

```text
python -m app.main debug ...
```

---

## show-aggregates

Zeigt aggregierte Monatsdaten.

Beispiel:

```powershell
python -m app.main debug show-aggregates 2026-05
```

---

## show-evaluations

Zeigt Bewertungsresultate.

Beispiel:

```powershell
python -m app.main debug show-evaluations 2026-05
```

Mit Statusfilter:

```powershell
python -m app.main debug show-evaluations 2026-05 --status CRITICAL
```

---

# Automatisierungskonzept

## Tägliche Datensammlung

Geplanter Ablauf:

```text
mehrfach täglich
→ collect-metrics
```

Jeder Run sammelt historische Werte eines Zeitfensters.

---

## Monatlicher Workflow

```text
monthly-workflow
├── previous month
├── aggregation
├── evaluation
└── report generation
```

Nur bei vorhandenen Daten wird ein Report erzeugt.

---

# Fehlerrobustheit

Die Anwendung behandelt:

- fehlende Gastinformationen
- fehlende Storagewerte
- fehlende CPU/RAM-Metriken
- ausgeschaltete Systeme
- teilweise verfügbare Metriken

ohne Abbruch des Gesamtlaufs.

---

# Testing

Die Anwendung verwendet pytest.

Aktuelle Tests:

- Aggregationsworkflow
- Bewertungsworkflow

Beispiel:

```powershell
pytest
```

---

# Typischer Ablauf

## Datenbank initialisieren

```powershell
python -m app.main init-db
```

---

## Metriken sammeln

```powershell
python -m app.main collect-metrics
```

---

## Monatsaggregation

```powershell
python -m app.main aggregate 2026-05
```

---

## Report erzeugen

```powershell
python -m app.main report 2026-05
```

---

## Gesamter Monatsworkflow

```powershell
python -m app.main monthly-workflow
```

---

# Aktueller Projektstand

Der aktuelle Stand umfasst:

- VMware-vCenter-Anbindung
- historische CPU/RAM-Abfrage
- Gastbasierte Storageauswertung
- relationale Persistenz
- CollectionRuns
- Rohdatenhaltung
- Monatsaggregation
- Bewertungslogik
- externe Threshold-Konfiguration
- HTML-Reporting
- sortierbare Reports
- Summary Cards
- Top Consumers
- Debug-Commands
- Service-Schicht
- Workflow-Orchestrierung
- Nullable-/None-Fehlertoleranz
- pytest-Tests
- Automatisierungsvorbereitung

Die Anwendung befindet sich damit in einem stabilen und erweiterbaren Zustand.

