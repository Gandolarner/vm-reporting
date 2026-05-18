# Datenmodell – VM-Reporting vCenter

## Ziel des Datenmodells

Das Datenmodell bildet die Grundlage für die Speicherung, Auswertung und Bewertung historischer VM-Metriken.

Die Daten werden bewusst in mehrere fachliche Bereiche getrennt:

- VM-Stammdaten
- Datensammelläufe
- Rohdaten
- Monatsaggregationen
- Bewertungsergebnisse

Diese Trennung verbessert Nachvollziehbarkeit, Wartbarkeit und spätere Erweiterbarkeit.

---

## Überblick über die Tabellen

| Modell | Tabelle | Zweck |
| --- | --- | --- |
| `VirtualMachine` | `virtual_machines` | Stammdaten virtueller Maschinen |
| `CollectionRun` | `collection_runs` | Protokoll eines Datensammellaufs |
| `MetricRecord` | `metric_records` | einzelne Messwerte einer VM |
| `MonthlyAggregate` | `monthly_aggregates` | berechnete Monatswerte je VM |
| `EvaluationResult` | `evaluation_results` | fachliche Bewertung einer Monatsaggregation |

---

## Fachlicher Datenfluss

```text
VirtualMachine
     ↓
MetricRecord
     ↓
MonthlyAggregate
     ↓
EvaluationResult
```

Zusätzlich dokumentiert `CollectionRun`, aus welchem Sammellauf einzelne Messwerte stammen.

```text
CollectionRun
     ↓
MetricRecord
```

---

## Architekturentscheidung zur Trennung der Datenbereiche

Die Anwendung speichert Rohdaten, Aggregationen und Bewertungen getrennt.

### Vorteile

- Rohdaten bleiben nachvollziehbar erhalten
- Aggregationen können bei Bedarf neu berechnet werden
- Bewertungsschwellwerte können geändert und neu angewendet werden
- Reports können aus bereits vorhandenen Daten erzeugt werden
- externe Datenerfassung und fachliche Auswertung bleiben getrennt

---

## Modell VirtualMachine

### VirtualMachine-Zweck

`VirtualMachine` speichert die Stammdaten einer virtuellen Maschine.

### VirtualMachine-Felder

| Feld | Typ | Bedeutung |
| --- | --- | --- |
| `id` | Integer | interner Primärschlüssel |
| `moid` | String(100) | VMware Managed Object ID |
| `name` | String(255) | Anzeigename der VM |
| `created_at` | DateTime | Zeitpunkt der Anlage in der Datenbank |

### Entscheidung für interne ID und moid

Die interne `id` wird als Primärschlüssel verwendet. Die VMware-`moid` wird zusätzlich eindeutig gespeichert.

`moid` steht für:

```text
Managed Object ID
```

Sie identifiziert ein Objekt innerhalb von VMware vCenter eindeutig, ist aber eine externe Systemkennung.

### Gründe für diese Trennung

- die Datenbank bleibt unabhängig vom externen System
- Fremdschlüssel bleiben klein und effizient
- spätere Erweiterungen werden einfacher
- mehrere oder wechselnde Datenquellen können später leichter berücksichtigt werden

Die `moid` erhält `unique=True`, damit dieselbe VM nicht mehrfach gespeichert wird.

---

## Beziehungen von VirtualMachine

```python
metric_records = relationship(back_populates="virtual_machine")
monthly_aggregates = relationship(back_populates="virtual_machine")
```

Eine VM kann viele Messwerte und viele Monatsaggregationen besitzen.

Diese Beziehungen erzeugen keine zusätzlichen Tabellenspalten, sondern ermöglichen den Zugriff über Python-Objekte:

```python
vm.metric_records
vm.monthly_aggregates
```

---

## Modell CollectionRun

### CollectionRun-Zweck

`CollectionRun` protokolliert einen Datensammellauf.

Ein Sammellauf beschreibt nicht nur den Zeitpunkt, zu dem die Anwendung ausgeführt wurde, sondern auch den Zeitraum, für den Performance-Daten aus dem vCenter abgefragt wurden.

Damit kann nachvollzogen werden:

- wann ein Sammellauf gestartet wurde
- wann er beendet wurde
- welchen Zeitraum der Sammellauf abgedeckt hat
- ob er erfolgreich war
- wie viele VMs verarbeitet wurden
- wie viele Messdatensätze erzeugt wurden
- ob ein Fehler auftrat

### CollectionRun-Felder

| Feld | Typ | Bedeutung |
| --- | --- | --- |
| `id` | Integer | interner Primärschlüssel |
| `started_at` | DateTime | Startzeitpunkt des Programmlaufs |
| `finished_at` | DateTime / NULL | Endzeitpunkt des Programmlaufs |
| `period_start` | DateTime | Beginn des abgefragten Metrikzeitraums |
| `period_end` | DateTime | Ende des abgefragten Metrikzeitraums |
| `status` | String(20) | Status des Sammellaufs |
| `processed_vm_count` | Integer | Anzahl verarbeiteter VMs |
| `created_metric_record_count` | Integer | Anzahl erzeugter Messdatensätze |
| `error_message` | Text / NULL | Fehlermeldung bei Problemen |

### Gründe für period_start und period_end

Würde die Anwendung nur Momentanwerte erfassen, könnten kurzzeitige Lastspitzen zwischen zwei Ausführungszeitpunkten verloren gehen.

Durch die Speicherung eines abgefragten Zeitraums kann ein CollectionRun historische vCenter-Performance-Daten für ein definiertes Zeitfenster erfassen.

### Unterschied zwischen Ausführungszeit und Abfragezeitraum

`started_at` und `finished_at` beschreiben, wann die Anwendung tatsächlich ausgeführt wurde.

`period_start` und `period_end` beschreiben dagegen, für welchen Zeitraum Metrikdaten aus dem vCenter abgefragt wurden.

Beispiel:

```text
started_at:    2026-05-11 07:00
finished_at:   2026-05-11 07:03
period_start:  2026-05-10 07:00
period_end:    2026-05-11 07:00
```

### Geplante Statuswerte

Mögliche Werte für `status`:

```text
RUNNING
SUCCESS
FAILED
PARTIAL_SUCCESS
```

### Beziehung zu MetricRecord

```python
metric_records = relationship(back_populates="collection_run")
```

Ein Sammellauf kann viele Messdatensätze erzeugen.

Dadurch kann später nachvollzogen werden:

```python
run.metric_records
```

---

## Modell MetricRecord

### MetricRecord-Zweck

`MetricRecord` speichert einen einzelnen Messdatensatz einer VM zu einem bestimmten Zeitpunkt.

### MetricRecord-Felder

| Feld | Typ | Bedeutung |
| --- | --- | --- |
| `id` | Integer | interner Primärschlüssel |
| `vm_id` | Integer | Fremdschlüssel auf `virtual_machines.id` |
| `collection_run_id` | Integer | Fremdschlüssel auf `collection_runs.id` |
| `timestamp` | DateTime | Zeitpunkt der Messung |
| `cpu_usage_percent` | Float | CPU-Auslastung in Prozent |
| `memory_usage_percent` | Float | RAM-Auslastung in Prozent |
| `storage_usage_percent` | Float | Storage-Auslastung in Prozent |

### MetricRecord-Beziehungen

```python
virtual_machine = relationship(back_populates="metric_records")
collection_run = relationship(back_populates="metric_records")
```

Dadurch sind folgende Zugriffe möglich:

```python
metric.virtual_machine
metric.collection_run
```

### Bedeutung der Fremdschlüssel

`vm_id` ordnet den Messwert einer VM zu.

`collection_run_id` ordnet den Messwert dem Sammellauf zu, durch den er erzeugt wurde.

---

## Entscheidung für Prozentwerte

Die Rohdaten speichern zunächst CPU-, RAM- und Storage-Auslastung als Prozentwerte.

### Prozentwerte-Vorteile

- einfache Vergleichbarkeit zwischen VMs
- einfache Aggregation
- einfache Bewertung über Schwellenwerte
- übersichtliche Reports

Absolute Werte können später ergänzt werden, sind für den ersten Projektumfang aber nicht zwingend notwendig.

---

## Modell MonthlyAggregate

### MonthlyAggregate-Zweck

`MonthlyAggregate` speichert berechnete Monatswerte je VM.

Es verdichtet viele einzelne Messwerte zu einem Monatsdatensatz.

### MonthlyAggregate-Felder

| Feld | Typ | Bedeutung |
| --- | --- | --- |
| `id` | Integer | interner Primärschlüssel |
| `vm_id` | Integer | Fremdschlüssel auf `virtual_machines.id` |
| `month` | String(7) | Monat im Format `YYYY-MM` |
| `cpu_avg_percent` | Float | durchschnittliche CPU-Auslastung |
| `cpu_min_percent` | Float | minimale CPU-Auslastung |
| `cpu_max_percent` | Float | maximale CPU-Auslastung |
| `memory_avg_percent` | Float | durchschnittliche RAM-Auslastung |
| `memory_min_percent` | Float | minimale RAM-Auslastung |
| `memory_max_percent` | Float | maximale RAM-Auslastung |
| `storage_avg_percent` | Float | durchschnittliche Storage-Auslastung |
| `storage_min_percent` | Float | minimale Storage-Auslastung |
| `storage_max_percent` | Float | maximale Storage-Auslastung |
| `created_at` | DateTime | Zeitpunkt der Berechnung/Speicherung |

### Monat als String

Der Monat wird im Format gespeichert:

```text
YYYY-MM
```

Beispiel:

```text
2026-05
```

Dafür reicht `String(7)`.

### Eindeutigkeitsregel

Pro VM darf es pro Monat nur eine Monatsaggregation geben.

Diese Regel wird über einen Unique Constraint umgesetzt:

```python
UniqueConstraint(
    "vm_id",
    "month",
    name="uq_monthly_aggregate_vm_month",
)
```

Damit wird verhindert, dass für dieselbe VM und denselben Monat mehrere widersprüchliche Aggregationen entstehen.

### MonthlyAggregate-Beziehungen

```python
virtual_machine = relationship(back_populates="monthly_aggregates")
evaluation_result = relationship(back_populates="monthly_aggregate")
```

Dadurch sind folgende Zugriffe möglich:

```python
aggregate.virtual_machine
aggregate.evaluation_result
```

---

## Modell EvaluationResult

### EvaluationResult-Zweck

`EvaluationResult` speichert die fachliche Bewertung einer Monatsaggregation.

Die Aggregation beschreibt objektive Messwerte.  
Die Bewertung interpretiert diese Messwerte anhand definierter Schwellenwerte.

### EvaluationResult-Felder

| Feld | Typ | Bedeutung |
| --- | --- | --- |
| `id` | Integer | interner Primärschlüssel |
| `monthly_aggregate_id` | Integer | Fremdschlüssel auf `monthly_aggregates.id` |
| `overall_status` | String(20) | Gesamtbewertung |
| `cpu_status` | String(20) | Bewertung der CPU-Auslastung |
| `memory_status` | String(20) | Bewertung der RAM-Auslastung |
| `storage_status` | String(20) | Bewertung der Storage-Auslastung |
| `note` | Text / NULL | optionale Begründung oder Zusatzinformation |
| `created_at` | DateTime | Zeitpunkt der Bewertung |

### Geplante Bewertungsstatus

Mögliche Statuswerte:

```text
UNDERUTILIZED
NORMAL
WARNING
CRITICAL
```

### Bedeutung von overall_status

`overall_status` fasst die Einzelbewertungen zusammen.

Beispiel:

```text
cpu_status     = NORMAL
memory_status  = WARNING
storage_status = CRITICAL
overall_status = CRITICAL
```

Die Gesamtbewertung kann später im Report verwendet werden, um besonders auffällige VMs schnell zu erkennen.

### EvaluationResult-Eindeutigkeitsregel

Pro Monatsaggregation soll genau eine Bewertung existieren.

Diese Regel wird über einen Unique Constraint umgesetzt:

```python
UniqueConstraint(
    "monthly_aggregate_id",
    name="uq_evaluation_result_monthly_aggregate",
)
```

---

## Bedeutung von ForeignKey und relationship

### ForeignKey

`ForeignKey` beschreibt die Beziehung auf Datenbankebene.

Beispiel:

```python
ForeignKey("virtual_machines.id")
```

Dadurch wird sichergestellt, dass ein Messwert nur auf eine existierende VM verweisen kann.

### relationship

`relationship()` beschreibt die Beziehung auf Python-/ORM-Ebene.

Sie erzeugt keine eigene Tabellenspalte, sondern ermöglicht komfortable Objektzugriffe.

Beispiel:

```python
metric.virtual_machine
vm.metric_records
```

### Merksatz

```text
ForeignKey verbindet Tabellen.
relationship verbindet Python-Objekte.
```

---

## Entscheidung gegen automatische Lösch-Cascades

In der aktuellen Version werden keine automatischen Lösch-Cascades verwendet.

### Grund

Historische Messdaten, Aggregationen und Bewertungen sollen nicht versehentlich gelöscht werden, nur weil ein übergeordneter Datensatz entfernt wird.

Löschlogik soll später bewusst über Anwendungscode oder Archivierungsmechanismen gesteuert werden.

---

## Zeitstempel und UTC

Zeitstempel werden mit UTC-Zeit erzeugt:

```python
datetime.now(UTC)
```

Dies vermeidet Probleme mit:

- lokalen Zeitzonen
- Sommerzeit
- unterschiedlichen Systemumgebungen

Die Verwendung von `lambda` sorgt dafür, dass der Zeitstempel erst beim Anlegen eines neuen Datensatzes erzeugt wird.

Beispiel:

```python
default=lambda: datetime.now(UTC)
```

---

## Reports als Ausgabeartefakte

Reports werden nicht als eigene Tabelle modelliert.

Sie werden aus vorhandenen Daten erzeugt:

- `VirtualMachine`
- `MetricRecord`
- `MonthlyAggregate`
- `EvaluationResult`

Der erzeugte Report ist ein Ausgabeartefakt, z. B.:

```text
output/reports/vm_report_2026-05.html
```

Eine eigene Report-Tabelle wäre erst sinnvoll, wenn später zusätzlich gespeichert werden soll:

- wann ein Report erzeugt wurde
- mit welchen Parametern
- mit welchem Dateipfad
- von welchem Benutzer
- mit welchem Status

Für den aktuellen Projektumfang ist das nicht notwendig.

---

## Repository-Schicht

Die Datei `app/database/repositories.py` kapselt zentrale Datenbankoperationen.

Repositories trennen den direkten Datenbankzugriff von der fachlichen Verarbeitung.

### Zweck der Repository-Schicht

Die Repository-Schicht ist verantwortlich für:

- Anlegen von VMs
- Abrufen von VMs über die VMware-`moid`
- Erzeugen und Abschließen von CollectionRuns
- Speichern von MetricRecords
- Abrufen von MetricRecords für VM und Monat
- Speichern von MonthlyAggregates
- Speichern von EvaluationResults

Dadurch müssen andere Anwendungsteile keine direkten SQLAlchemy-Abfragen enthalten.

### Repository-Schicht-Vorteile

- bessere Trennung von Datenzugriff und Fachlogik
- besser testbarer Code
- zentralisierte Datenbankoperationen
- geringere Kopplung zwischen Modulen

### Beispielhafter Ablauf

```text
Collector / Processing
        ↓
Repository-Funktion
        ↓
SQLAlchemy Session
        ↓
Datenbank
```

---

## Aktuelle Repository-Funktionen

| Funktion | Zweck |
| --- | --- |
| `create_vm()` | erstellt einen VM-Stammdatensatz |
| `get_vm_by_moid()` | sucht eine VM anhand der VMware-`moid` |
| `create_collection_run()` | startet einen neuen Sammellauf |
| `finish_collection_run()` | beendet einen Sammellauf mit Statusinformationen |
| `create_metric_record()` | speichert einen Messdatensatz |
| `get_metric_records_for_vm_and_month()` | lädt Messwerte einer VM für einen Monat |
| `create_monthly_aggregate()` | speichert berechnete Monatswerte |
| `create_evaluation_result()` | speichert eine Bewertung |

---

## Aggregationslogik

Die Datei `app/processing/aggregation.py` enthält die fachliche Logik zur Verdichtung von Rohdaten.

Die Aggregation berechnet aus mehreren `MetricRecord`-Einträgen Monatswerte.

### Berechnete Werte

Für CPU, RAM und Storage werden jeweils berechnet:

- Durchschnitt
- Minimum
- Maximum

### Beispiel

```text
CPU-Werte: 10, 20, 30

cpu_avg_percent = 20
cpu_min_percent = 10
cpu_max_percent = 30
```

### Trennung von Berechnung und Speicherung

Die Aggregationslogik berechnet nur Werte.

Die Speicherung erfolgt anschließend über die Repository-Schicht.

```text
MetricRecords
        ↓
aggregate_metric_records()
        ↓
Aggregationsergebnis
        ↓
create_monthly_aggregate()
        ↓
MonthlyAggregate
```

Diese Trennung verhindert, dass fachliche Berechnungen und Datenbankzugriffe vermischt werden.

---

## Bewertungslogik

Die Datei `app/processing/evaluation.py` bewertet aggregierte Monatswerte anhand konfigurierbarer Schwellenwerte.

### Bewertungsstatus

Verwendete Statuswerte:

```text
UNDERUTILIZED
NORMAL
WARNING
CRITICAL
```

### Einzelbewertung

Für CPU, RAM und Storage wird jeweils ein eigener Status berechnet.

Beispiel:

```text
cpu_avg_percent = 55.5      → NORMAL
memory_avg_percent = 76.0   → WARNING
storage_avg_percent = 91.0  → CRITICAL
```

### Gesamtbewertung

Aus den Einzelbewertungen wird ein `overall_status` bestimmt.

Dabei haben kritische Zustände Vorrang vor Warnungen und Normalzuständen.

Beispiel:

```text
cpu_status     = NORMAL
memory_status  = WARNING
storage_status = CRITICAL
overall_status = CRITICAL
```

---

## Threshold-Konfiguration

Die Schwellenwerte werden nicht fest im Code hinterlegt, sondern in der Datei `app/config/thresholds.yaml` gespeichert.

### Zweck

Thresholds definieren, ab wann ein Messwert als unterausgelastet, normal, auffällig oder kritisch gilt.

### Threshold-Beispiel

```yaml
cpu:
  underutilized_below: 20
  warning_above: 70
  critical_above: 90
```

### Thresholds-Vorteile

- keine Codeänderung bei geänderten Schwellenwerten
- klare Trennung von Konfiguration und Fachlogik
- bessere Wartbarkeit
- bessere Nachvollziehbarkeit in der Projektdokumentation

---

## Laden der Thresholds

Die Datei `app/config/threshold_loader.py` lädt die YAML-Konfiguration.

```text
thresholds.yaml
        ↓
threshold_loader.py
        ↓
evaluation.py
```

Dadurch kann die Bewertungslogik dynamisch auf die konfigurierten Werte zugreifen.

---

## Vollständiger aktueller Verarbeitungsablauf

Der bisher umgesetzte Kernprozess lautet:

```text
VM anlegen oder abrufen
        ↓
CollectionRun starten
        ↓
MetricRecords speichern
        ↓
MetricRecords für VM und Monat laden
        ↓
Monatswerte berechnen
        ↓
MonthlyAggregate speichern
        ↓
Aggregation bewerten
        ↓
EvaluationResult speichern
        ↓
CollectionRun abschließen
```

Dieser Ablauf bildet den fachlichen Kern der Anwendung ab.

---

## Teststrategie

Der aktuelle Entwicklungsstand wurde zunächst manuell über die Python-Konsole geprüft.

Dabei wurden folgende Schritte erfolgreich getestet:

- Anlegen einer VM
- Starten eines CollectionRuns
- Speichern eines MetricRecords
- Laden von MetricRecords für VM und Monat
- Berechnung von Min-/Max-/Durchschnittswerten
- Speichern eines MonthlyAggregates
- Bewertung des Aggregationsergebnisses
- Speichern eines EvaluationResults
- Abschließen eines CollectionRuns

Im nächsten Schritt werden diese manuellen Tests in automatisierte `pytest`-Tests überführt.

### Ziel der automatisierten Tests

Die Tests sollen sicherstellen, dass der komplette fachliche Kernprozess reproduzierbar funktioniert.

```text
Rohdaten
→ Aggregation
→ Bewertung
→ Speicherung
```

## Aktueller Entwicklungsstand

### Bereits umgesetzt

- zentrale SQLAlchemy-Basis
- Datenbank-Engine
- Session-Factory
- Modell `VirtualMachine`
- Modell `CollectionRun`
- Modell `MetricRecord`
- Modell `MonthlyAggregate`
- Modell `EvaluationResult`
- Foreign-Key-Beziehungen
- ORM-Relationships
- Unique Constraints
- UTC-Zeitstempel
- Datenbankinitialisierung über CLI
- Erzeugung der SQLite-Datenbank
- Repository-Funktionen für VM, CollectionRun, MetricRecord, MonthlyAggregate und EvaluationResult
- Aggregationslogik für Min-/Max-/Durchschnittswerte
- YAML-basierte Threshold-Konfiguration
- Bewertungslogik für Aggregationsergebnisse
- automatisierte Tests mit `pytest`

### Nächste Schritte

- Testdatenbank für reproduzierbare Tests
- CLI-Workflow für Aggregation und Bewertung
- Reportgenerierung
