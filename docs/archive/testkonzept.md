# Testkonzept – VM-Reporting vCenter

## Ziel des Testkonzepts

Das Testkonzept beschreibt, wie die fachliche Kernlogik der Anwendung überprüft wird.

Die Tests sollen sicherstellen, dass die Verarbeitung von VM-Metriken reproduzierbar und nachvollziehbar funktioniert.

Im Fokus stehen zunächst:

- Datenbankmodelle
- Repository-Funktionen
- Aggregationslogik
- Bewertungslogik
- korrekte Monatszuordnung von Messwerten

---

## Eingesetztes Testframework

Für automatisierte Tests wird `pytest` verwendet.

Die Tests können im Projektverzeichnis mit folgendem Befehl ausgeführt werden:

```powershell
pytest
```

---

## Testkonfiguration

Die pytest-Konfiguration erfolgt über `pyproject.toml`.

```toml
[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
```

Dadurch erkennt `pytest` das Projektpaket `app` und sucht Tests im Ordner `tests`.

---

## Testdatenbank

Die automatisierten Tests verwenden eine SQLite-Datenbank im Arbeitsspeicher:

```python
create_engine("sqlite:///:memory:", future=True)
```

Dadurch wird die reguläre Entwicklungsdatenbank nicht verändert.

### Vorteile der In-Memory-Datenbank

- keine Veränderung echter Entwicklungsdaten
- reproduzierbare Testläufe
- schnelle Ausführung
- keine manuelle Bereinigung notwendig

Die Tabellen werden für jeden Testlauf über SQLAlchemy erzeugt:

```python
Base.metadata.create_all(bind=engine)
```

---

## Getesteter Kernworkflow

Der aktuelle Haupttest prüft den vollständigen fachlichen Kernprozess:

```text
VM anlegen
→ CollectionRun anlegen
→ MetricRecords speichern
→ Rohdaten für Monat laden
→ Monatswerte berechnen
→ MonthlyAggregate speichern
→ Aggregation bewerten
→ EvaluationResult speichern
→ CollectionRun abschließen
```

Dieser Ablauf stellt sicher, dass die wichtigsten Schichten der Anwendung zusammenarbeiten.

---

## Testfall vollständiger Aggregationsworkflow

### Zweck-Testfall vollständiger Aggregationsworkflow

Der Test `test_full_aggregation_workflow()` prüft, ob aus gespeicherten Rohdaten korrekte Monatswerte berechnet, gespeichert und bewertet werden.

### Geprüfte Funktionen

- `create_vm()`
- `create_collection_run()`
- `create_metric_record()`
- `get_metric_records_for_vm_and_month()`
- `aggregate_metric_records()`
- `create_monthly_aggregate()`
- `evaluate_aggregate()`
- `create_evaluation_result()`
- `finish_collection_run()`

### Beispielwerte

Im Test werden zwei Messwerte erzeugt:

| Metrik | Wert 1 | Wert 2 | Erwarteter Durchschnitt | Minimum | Maximum |
| --- | ---: | ---: | ---: | ---: | ---: |
| CPU | 10.0 | 30.0 | 20.0 | 10.0 | 30.0 |
| Memory | 50.0 | 70.0 | 60.0 | 50.0 | 70.0 |
| Storage | 70.0 | 90.0 | 80.0 | 70.0 | 90.0 |

### Erwartete Bewertung

Auf Basis der konfigurierten Thresholds wird erwartet:

```text
cpu_status = NORMAL
memory_status = NORMAL
storage_status = WARNING
overall_status = WARNING
```

### Geprüfte Assertions

Beispielhafte Prüfungen:

```python
assert len(records) == 2
assert aggregation_result["cpu_avg_percent"] == 20.0
assert evaluation_result.overall_status == "WARNING"
```

---

## Testfall Monats- und Jahresgrenze

### Zweck-Testfall Monats- und Jahresgrenze

Der Test `test_month_boundary_separation()` prüft, ob Messwerte korrekt anhand ihres Messzeitpunkts einem Monat zugeordnet werden.

Dies ist wichtig, weil ein `CollectionRun` einen Zeitraum abdecken kann, der über Monats- oder Jahresgrenzen hinweg verläuft.

### Beispielszenario

Ein CollectionRun deckt folgenden Zeitraum ab:

```text
31.12.2025 07:00
bis
01.01.2026 07:00
```

Dabei entstehen zwei Messwerte:

| Messzeitpunkt | Erwartete Monatszuordnung |
| --- | --- |
| 31.12.2025 23:00 | Dezember 2025 |
| 01.01.2026 01:00 | Januar 2026 |

### Erwartetes Verhalten

Die Abfrage für Dezember 2025 findet nur den Dezemberwert.

Die Abfrage für Januar 2026 findet nur den Januarwert.

Dadurch wird sichergestellt, dass nicht der Zeitraum des `CollectionRun`, sondern der `timestamp` des jeweiligen `MetricRecord` über die Monatszuordnung entscheidet.

### Fachliche Bedeutung

Dieser Test stellt sicher, dass Monatsreports auch dann korrekt erzeugt werden können, wenn ein Datensammellauf historische Daten über Monats- oder Jahresgrenzen hinweg verarbeitet.

---

## Bedeutung von Assertions

Die Tests verwenden `assert`-Anweisungen, um erwartete Ergebnisse automatisch zu prüfen.

Beispiel:

```python
assert len(records) == 2
assert aggregation_result["cpu_avg_percent"] == 20.0
```

Schlägt eine Bedingung fehl, meldet `pytest` den Test als fehlgeschlagen.

---

## Trennung zwischen Entwicklungsdatenbank und Testdatenbank

Die produktive Entwicklungsdatenbank liegt als SQLite-Datei im Projekt.

Die Tests verwenden dagegen ausschließlich eine temporäre In-Memory-Datenbank.

Dadurch werden:

- keine echten Entwicklungsdaten verändert
- keine manuellen Bereinigungen notwendig
- Testläufe reproduzierbar
- Seiteneffekte zwischen Tests minimiert

---

## Aktueller Teststand

Aktuell vorhandene Tests:

| Test | Zweck |
| --- | --- |
| `test_full_aggregation_workflow()` | prüft den vollständigen Kernworkflow |
| `test_month_boundary_separation()` | prüft Monats- und Jahresgrenzen |

Ausführung:

```powershell
pytest
```

Erwartetes Ergebnis:

```text
2 passed
```

---

## Aktuell getestete Komponenten

Der aktuelle Teststand umfasst:

- SQLAlchemy-Modelle
- Repository-Schicht
- Aggregationslogik
- Bewertungslogik
- Threshold-Konfiguration
- Monatsfilterung
- Monats-/Jahresgrenzen
- CollectionRun-Workflow

---

## Geplante Erweiterungen des Testkonzepts

Mögliche spätere Ergänzungen:

- Bewertung einzelner Threshold-Grenzfälle
- Verhalten bei leerer MetricRecord-Liste
- Tests für Unique Constraints
- Fehlerfälle beim Speichern doppelter VMs
- Tests für Reportgenerierung
- Tests für vCenter-API-Integration
- Mocking externer API-Antworten
- Performance-Tests größerer Datenmengen

---

## Zusammenfassung

Die aktuelle Teststrategie verfolgt das Ziel, den fachlichen Kernprozess der Anwendung automatisiert und reproduzierbar zu überprüfen.

Im Mittelpunkt stehen:

```text
Rohdaten
→ Aggregation
→ Bewertung
→ Speicherung
```

Durch die automatisierten Tests kann die Anwendung schrittweise erweitert werden, ohne bestehende Kernfunktionalitäten unbeabsichtigt zu beschädigen.
