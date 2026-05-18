# VM Reporting

Automatisierte VMware-vCenter-Auswertung mit Python, SQLAlchemy und HTML-Reporting.

---

## Projektziel

Die Anwendung sammelt historische Leistungsmetriken virtueller Maschinen aus VMware vCenter, speichert Rohdaten in einer relationalen Datenbank, aggregiert Monatswerte und erzeugt HTML-Reports zur Bewertung der Ressourcenauslastung.

Erfasste Metriken:

- CPU-Auslastung
- Arbeitsspeicherauslastung
- Storage-Auslastung

---

## Funktionen

- VMware-vCenter-Anbindung über pyVmomi
- Historische CPU- und RAM-Metriken
- Gastbasierte Storage-Auswertung
- Speicherung von Rohdaten
- Monatsaggregation
- Bewertungslogik mit Thresholds
- HTML-Reporting
- Sortierbare Reporttabellen
- Top-Consumer-Auswertung
- Debug-Commands
- Logging
- Automatisierung über Workflows

---

## Projektstruktur

```text
app/
├── cli/
├── collectors/
├── config/
├── database/
├── processing/
├── reporting/
├── services/
├── utils/
├── vcenter/
└── main.py
```

---

## Voraussetzungen

- Python 3.12+
- VMware-vCenter-Zugriff
- Windows oder Linux
- virtuelle Umgebung (venv)
- Git installiert

---

## Installation

### Repository klonen

```powershell
git clone https://github.com/Gandolarner/vm-reporting.git
cd vm-reporting
```

### Virtuelle Umgebung erstellen

```powershell
python -m venv .venv
```

---

### Virtuelle Umgebung aktivieren

```powershell
.venv\Scripts\Activate.ps1
```

---

### Abhängigkeiten installieren

```powershell
pip install -r requirements.txt
```

---

## Konfiguration

### .env anlegen

Beispiel:

```env
DATABASE_URL=sqlite:///data/vm_reporting.db
REPORT_OUTPUT_DIR=output/reports

VCENTER_HOST=vcenter.example.local
VCENTER_USERNAME=username
VCENTER_PASSWORD=password
VCENTER_PORT=443
VCENTER_VERIFY_SSL=false

LOG_LEVEL=INFO
```

---

## Demo-Konfiguration

Für Präsentationen ohne Zugriff auf ein echtes VMware-vCenter kann eine separate Demo-Umgebung verwendet werden.

Datei:

```text
.env.demo
```

Beispiel:

```env
DATABASE_URL=sqlite:///data/demo_vm_reporting.db
REPORT_OUTPUT_DIR=output/demo-reports

VCENTER_HOST=demo
VCENTER_USERNAME=demo
VCENTER_PASSWORD=demo
VCENTER_PORT=443
VCENTER_VERIFY_SSL=false

LOG_LEVEL=INFO
```

---

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

## Monatsaggregation durchführen

```powershell
python -m app.main aggregate 2026-05
```

---

## HTML-Report erzeugen

```powershell
python -m app.main report 2026-05
```

---

## Daily Workflow

Führt die tägliche Metriksammlung aus.

```powershell
python -m app.main daily-workflow
```

---

## Monthly Workflow

Aggregiert automatisch den Vormonat und erzeugt einen Report.

```powershell
python -m app.main monthly-workflow
```

---

## Debug-Commands

### Aggregierte Monatswerte anzeigen

```powershell
python -m app.main debug show-aggregates 2026-05
```

---

### Evaluationsstatus anzeigen

```powershell
python -m app.main debug show-evaluations 2026-05
```

---

### Kritische Systeme anzeigen

```powershell
python -m app.main debug show-evaluations 2026-05 --status CRITICAL
```

---

## Logging

Logs werden gespeichert unter:

```text
logs/vm_reporting.log
```

Das Logging dokumentiert:

- Verbindungsaufbau
- Metriksammlung
- Aggregation
- Reportgenerierung
- Workflow-Ausführung
- Warnungen und Fehler

---

## Reports

Reports werden erzeugt unter:

```text
output/reports/
```

Enthalten sind:

- Summary Cards
- Top Consumers
- Bewertungsstatus
- sortierbare Tabellen
- farbliche Statusmarkierungen

---

## Threshold-Konfiguration

Thresholds werden konfiguriert in:

```text
app/config/thresholds.yaml
```

Beispiel:

```yaml
cpu:
  underutilized_below: 20
  warning_above: 70
  critical_above: 90
```

---

## Testing

Tests ausführen:

```powershell
pytest
```

---

## Demo-Modus

Der Demo-Modus ermöglicht die lokale Demonstration der Anwendung ohne Verbindung zu einem echten VMware-vCenter.

Dabei werden:

- eine separate Demo-Datenbank
- separate Report-Ausgabeverzeichnisse
- synthetische Demo-Metrikdaten

verwendet.

Der Produktivbetrieb bleibt dabei vollständig getrennt.
Echte vCenter-Datenbanken und Reports werden nicht verändert.

---

### Demo-Modus aktivieren

```powershell
$env:APP_ENV="demo"
```

---

### Demo-Datenbank neu erzeugen

```powershell
Remove-Item .\data\demo_vm_reporting.db -ErrorAction SilentlyContinue
```

---

### Demo-Daten erzeugen

```powershell
python -m app.main init-db
python -m app.main seed-demo-data 2026-05
```

---

### Demo-Workflow ausführen

```powershell
python -m app.main aggregate 2026-05
python -m app.main report 2026-05
```

---

### Demo-Report

Demo-Reports werden erzeugt unter:

```text
output/demo-reports/
```

---

### Zurück zum Standardmodus

```powershell
Remove-Item Env:APP_ENV
```

---

## Repository initialisieren

Falls noch kein Git-Repository vorhanden ist:

```powershell
git init
git status
git add .
git commit -m "Initial project state"
```

Vor dem ersten Commit sollte die `.gitignore` geprüft werden, damit keine sensiblen Daten wie `.env`, Datenbanken, Logs oder erzeugte Reports versioniert werden.

---

## Geplante/Mögliche Erweiterungen

- E-Mail-Versand
- PDF-/Excel-Export
- Airflow-Integration
- Trenddiagramme
- REST-API
- Webfrontend

---

## Technologien

- Python 3.12
- SQLAlchemy
- SQLite
- pyVmomi
- Typer
- Rich
- pytest

---

## Autor

Marius-Christian Claus
