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

## Idempotente Aggregations- und Bewertungslogik

Die Aggregations- und Bewertungsfunktionen sind so umgesetzt, dass ein Monatslauf mehrfach ausgeführt werden kann, ohne doppelte Datensätze zu erzeugen.

Dies ist wichtig, weil Monatsaggregationen bei nachträglich ergänzten Rohdaten erneut berechnet werden können.

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
| `metric_record_count` | Integer | Anzahl der verwendeten Messdatensätze |
| `cpu_avg_percent` | Float | durchschnittliche CPU-Auslastung |
| `cpu_min_percent` | Float | minimale CPU-Auslastung |
| `cpu_max_percent` | Float | maximale CPU-Auslastung |
| `memory_avg_percent` | Float | durchschnittliche RAM-Auslastung |
| `memory_min_percent` | Float | minimale RAM-Auslastung |
| `memory_max_percent` | Float | maximale RAM-Auslastung |
| `storage_avg_percent` | Float | durchschnittliche Storage-Auslastung |
| `storage_min_percent` | Float | minimale Storage-Auslastung |
| `storage_max_percent` | Float | maximale Storage-Auslastung |
| `created_at` | DateTime | Zeitpunkt der erstmaligen Erstellung |
| `updated_at` | DateTime / NULL | Zeitpunkt der letzten fachlichen Änderung |

### Bedeutung von metric_record_count

`metric_record_count` gibt an, aus wie vielen `MetricRecord`-Einträgen die Aggregation berechnet wurde.

Dadurch kann die Aussagekraft einer Aggregation besser bewertet werden.

Beispiel:

| VM | CPU-Durchschnitt | Messpunkte |
| --- | ---: | ---: |
| VM-A | 55 % | 2 |
| VM-B | 55 % | 720 |

Beide VMs haben denselben Durchschnittswert, aber eine unterschiedliche Datenbasis.

---

## Create-or-Update-Verhalten für MonthlyAggregate

Für Monatsaggregationen wird kein reines `create` verwendet, sondern ein Create-or-Update-Verfahren.

Dabei gilt:

```text
VM + Monat bereits vorhanden
→ vorhandenen Datensatz aktualisieren

VM + Monat noch nicht vorhanden
→ neuen Datensatz erstellen
```

Die Eindeutigkeit wird weiterhin durch den Unique Constraint abgesichert:

```python
UniqueConstraint(
    "vm_id",
    "month",
    name="uq_monthly_aggregate_vm_month",
)
```

### Änderungserkennung

Vorhandene Monatsaggregationen werden nur aktualisiert, wenn sich berechnete Werte tatsächlich geändert haben.

Dazu werden die neuen Aggregationswerte mit den gespeicherten Werten verglichen.

Bei Änderungen wird das Feld `updated_at` gesetzt.

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
| `note` | Text / NULL | optionale Zusatzinformation |
| `created_at` | DateTime | Zeitpunkt der erstmaligen Erstellung |
| `updated_at` | DateTime / NULL | Zeitpunkt der letzten fachlichen Änderung |

---

## Create-or-Update-Verhalten für EvaluationResult

Auch Bewertungsergebnisse werden per Create-or-Update-Verfahren gespeichert.

Dabei gilt:

```text
Bewertung für MonthlyAggregate bereits vorhanden
→ vorhandenen Datensatz aktualisieren

Bewertung noch nicht vorhanden
→ neuen Datensatz erstellen
```

Die Eindeutigkeit wird durch folgenden Unique Constraint abgesichert:

```python
UniqueConstraint(
    "monthly_aggregate_id",
    name="uq_evaluation_result_monthly_aggregate",
)
```

### Änderungserkennung

Vorhandene Bewertungen werden nur aktualisiert, wenn sich mindestens ein Bewertungswert geändert hat.

Geprüft werden:

- `overall_status`
- `cpu_status`
- `memory_status`
- `storage_status`
- `note`

Bei Änderungen wird `updated_at` gesetzt.

---

## Bedeutung von created_at und updated_at

`created_at` speichert, wann ein Datensatz erstmals erzeugt wurde.

`updated_at` speichert, wann ein bestehender Datensatz zuletzt fachlich verändert wurde.

Dadurch kann nachvollzogen werden:

- wann eine Aggregation erstmals berechnet wurde
- ob sie später durch neue Rohdaten aktualisiert wurde
- wann eine Bewertung zuletzt angepasst wurde

---

# Testkonzept – VM-Reporting vCenter

## Ziel des Testkonzepts

Das Testkonzept beschreibt, wie die fachliche Kernlogik der Anwendung überprüft wird.

Die Tests sollen sicherstellen, dass die Verarbeitung von VM-Metriken reproduzierbar und nachvollziehbar funktioniert.

---

## Eingesetztes Testframework

Für automatisierte Tests wird `pytest` verwendet.

Die Tests können im Projektverzeichnis mit folgendem Befehl ausgeführt werden:

```powershell
pytest
```

---

## Testdatenbank

Die automatisierten Tests verwenden eine SQLite-Datenbank im Arbeitsspeicher:

```python
create_engine("sqlite:///:memory:", future=True)
```

Dadurch wird die reguläre Entwicklungsdatenbank nicht verändert.

---

## Testfall vollständiger Aggregationsworkflow

Der Test `test_full_aggregation_workflow()` prüft den vollständigen Kernprozess:

```text
VM anlegen
→ CollectionRun anlegen
→ MetricRecords speichern
→ Monatswerte berechnen
→ MonthlyAggregate erstellen oder aktualisieren
→ Bewertung berechnen
→ EvaluationResult erstellen oder aktualisieren
→ CollectionRun abschließen
```

---

## Testfall Monats- und Jahresgrenze

Der Test `test_month_boundary_separation()` prüft, ob Messwerte korrekt anhand ihres Messzeitpunkts einem Monat zugeordnet werden.

Dies stellt sicher, dass nicht der Zeitraum des `CollectionRun`, sondern der `timestamp` des jeweiligen `MetricRecord` über die Monatszuordnung entscheidet.

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

## vCenter-Integration

### Ziel der vCenter-Integration

Die Anwendung soll VM-Informationen und Performance-Metriken automatisiert aus VMware vCenter abrufen.

Die vCenter-Integration bildet damit die Grundlage für:

- automatische Datensammlung
- historische Auswertungen
- Monatsreports
- Kapazitätsbewertungen
- spätere Automatisierung über Scheduler oder Airflow

---

## Erste Implementierung über die vCenter REST API

Zu Beginn des Projekts wurde die moderne vCenter REST API als möglicher Integrationsweg untersucht.

Dabei wurden erfolgreich umgesetzt:

- Authentifizierung gegen vCenter
- Abruf von VM-Inventardaten
- Abruf detaillierter VM-Konfigurationsdaten
- Synchronisierung von VM-Stammdaten

### Getestete REST-Endpunkte

| Endpunkt | Zweck |
| --- | --- |
| `/api/vcenter/vm` | VM-Inventar |
| `/api/vcenter/vm/{moid}` | VM-Details |
| `/api/appliance/system/version` | Versionsinformationen |

---

## Erkenntnisse aus der REST-API-Analyse

Die REST API eignete sich gut für:

- Inventardaten
- VM-Konfiguration
- Appliance-Informationen

Die benötigten historischen Performance-Metriken konnten über die untersuchten REST-Endpunkte jedoch nicht bereitgestellt werden.

Mehrere mögliche Statistik-Endpunkte lieferten:

```text
404 Not Found
```

### Fachliche Konsequenz

Die Anwendung verwendet deshalb für den produktiven Kernpfad nicht primär die REST API, sondern die VMware Web Services API über `pyVmomi`.

Die REST-Implementierung bleibt als dokumentierter Proof of Concept erhalten.

---

## Architekturentscheidung für pyVmomi

Die historische Performance-Auswertung ist der fachliche Kern des Projekts.

VMware stellt diese Daten primär über den sogenannten:

```text
PerformanceManager
```

bereit.

Dieser ist Bestandteil der VMware Web Services API und wird in Python über:

```text
pyVmomi
```

angesprochen.

### Gründe für pyVmomi

- Zugriff auf historische Performance-Daten
- Zugriff auf den offiziellen `PerformanceManager`
- vollständiger Zugriff auf VMware-Objekte
- etablierte VMware-Standardbibliothek
- bessere Abdeckung der benötigten Funktionen
- keine Mischung verschiedener API-Welten im Kernworkflow

---

## PyVmomiClient

Die Datei:

```text
app/vcenter/pyvmomi_client.py
```

kapselt die Kommunikation mit der VMware Web Services API.

### Aktuell implementierte Funktionen

| Funktion | Zweck |
| --- | --- |
| `connect()` | Verbindung zu vCenter herstellen |
| `disconnect()` | Session sauber schließen |
| `get_content()` | Zugriff auf das zentrale Inventory-Objekt |
| `get_all_vms()` | alle VMs abrufen |
| `get_vm_inventory()` | normalisierte Inventardaten erzeugen |

---

## Besonderheiten von pyVmomi

### Objektorientierte VMware-API

Im Gegensatz zur REST API arbeitet pyVmomi nicht primär mit JSON-Antworten.

Stattdessen werden VMware-Objekte bereitgestellt:

```python
vim.VirtualMachine
vim.HostSystem
vim.Datastore
```

Dadurch erfolgt der Zugriff typischerweise über Attribute:

```python
vm.name
vm.runtime.powerState
vm.config.hardware.numCPU
```

statt über Dictionary-Zugriffe.

---

## ServiceInstanceContent

Nach erfolgreicher Verbindung liefert:

```python
client.get_content()
```

das zentrale VMware-Inventory-Objekt:

```text
vim.ServiceInstanceContent
```

Dieses enthält Zugriff auf zentrale VMware-Manager:

| Manager | Zweck |
| --- | --- |
| `viewManager` | Inventory-Durchsuchung |
| `perfManager` | historische Performance-Daten |
| `searchIndex` | Suche nach Objekten |
| `eventManager` | Events |
| `taskManager` | Tasks |

---

## Bedeutung des PerformanceManager

Der:

```text
perfManager
```

ist die wichtigste Komponente für das eigentliche Projektziel.

Über ihn können später historische Leistungsdaten abgefragt werden:

- CPU-Auslastung
- RAM-Auslastung
- Storage-Performance
- Netzwerkmetriken
- Zeitreihen historischer Werte

Damit bildet `PerformanceManager` die Grundlage für:

```text
MetricRecords
→ MonthlyAggregates
→ EvaluationResults
→ Reports
```

---

## SSL-Behandlung in pyVmomi

Das verwendete interne vCenter nutzt kein öffentlich vertrauenswürdiges Zertifikat.

Deshalb wird in der Entwicklungsumgebung ein unsicherer SSL-Context verwendet:

```python
ssl._create_unverified_context()
```

### Zweck

Dadurch kann pyVmomi HTTPS-Verbindungen ohne Zertifikatsprüfung aufbauen.

### Hinweis

Für produktive Umgebungen sollte die Zertifikatsprüfung aktiviert und das Zertifikat sauber eingebunden werden.

---

## CreateContainerView

Zum Durchsuchen des VMware-Inventars wird verwendet:

```python
CreateContainerView(...)
```

### Beispiel

```python
content.viewManager.CreateContainerView(
    content.rootFolder,
    [vim.VirtualMachine],
    True,
)
```

### Bedeutung der Parameter

| Parameter | Bedeutung |
| --- | --- |
| `content.rootFolder` | Startpunkt der Suche |
| `[vim.VirtualMachine]` | nur VM-Objekte suchen |
| `True` | rekursive Suche |

---

## Normalisierung der pyVmomi-Daten

Die pyVmomi-Objekte werden in ein internes Standardformat überführt.

### Beispiel

Internes Inventory-Format:

```python
{
    "moid": "vm-87656",
    "name": "FILE-1",
    "power_state": "poweredOn",
    "cpu_count": 4,
    "memory_size_mib": 10240,
}
```

### Vorteile

- restliche Anwendung bleibt unabhängig von pyVmomi
- bessere Testbarkeit
- konsistente interne Datenstrukturen
- geringere Kopplung

---

## Bedeutung der moid

Die VMware-`moid` ist die technische Identität einer VM.

Beispiele:

```text
vm-87656
vm-101003
```

### Eigenschaften

- eindeutig innerhalb von vCenter
- stabil über Umbenennungen hinweg
- ideal als technische Referenz

Die Anwendung verwendet die `moid`, um:

- VMs eindeutig zu identifizieren
- Umbenennungen zu erkennen
- doppelte Datensätze zu vermeiden

---

## Create-or-Update-Verhalten für VirtualMachine

Die Funktion:

```python
create_or_update_vm()
```

implementiert die Synchronisationslogik zwischen vCenter und lokaler Datenbank.

### Verhalten

```text
moid unbekannt
→ VM anlegen

moid bekannt
→ bestehende VM aktualisieren
```

Dadurch bleibt das lokale Inventar mit vCenter synchron.

---

## Konfigurationsverwaltung über .env

Sensible Zugangsdaten werden nicht im Quellcode gespeichert.

Die Anwendung verwendet stattdessen:

```text
.env
```

### Enthaltene Werte

| Variable | Zweck |
| --- | --- |
| `VCENTER_HOST` | vCenter-Hostname |
| `VCENTER_PORT` | HTTPS-Port |
| `VCENTER_USERNAME` | Benutzername |
| `VCENTER_PASSWORD` | Passwort |
| `VCENTER_VERIFY_SSL` | SSL-Verifikation |
| `DATABASE_URL` | Datenbankpfad |

---

## settings.py

Die Datei:

```text
app/config/settings.py
```

lädt zentral alle Umgebungsvariablen.

### Vorteile

- zentrale Konfigurationsverwaltung
- saubere Trennung von Code und Konfiguration
- bessere Wartbarkeit
- einfache Erweiterbarkeit

---

## Factory-Pattern für den vCenter-Client

Die Datei:

```text
app/vcenter/factory.py
```

stellt eine zentrale Erzeugungsfunktion bereit:

```python
create_vcenter_client()
```

### Vorteile

- Konfiguration bleibt zentralisiert
- geringere Kopplung
- bessere Testbarkeit
- einfache Austauschbarkeit der Implementierung

---

## Aktueller collect-Workflow

Der CLI-Befehl:

```powershell
python -m app.main collect
```

führt aktuell folgenden Ablauf aus:

```text
vCenter-Verbindung aufbauen
→ VM-Inventar laden
→ Daten normalisieren
→ VirtualMachine create/update
→ Speicherung in SQLite
→ Verbindung sauber schließen
```

### Aktueller Status

Der Workflow wurde erfolgreich gegen ein echtes VMware-vCenter-System getestet.

Dabei konnten:

- pyVmomi-Verbindungen aufgebaut
- VMware-Inventory geladen
- 114 VMs synchronisiert
- VM-Stammdaten aktualisiert

werden.

---

## Aktueller Architekturstand

Der aktuelle Anwendungskern umfasst:

```text
VMware vCenter
        ↓
pyVmomi / Web Services API
        ↓
PyVmomiClient
        ↓
Normalisierung
        ↓
Repository-Schicht
        ↓
SQLite-Datenbank
        ↓
Aggregation
        ↓
Bewertung
        ↓
CLI-Workflows
        ↓
automatisierte Tests
```

---

## Nächste geplante Schritte

Die nächsten Entwicklungsschritte konzentrieren sich auf den:

```text
PerformanceManager
```

Geplant sind:

- Abruf historischer CPU-Metriken
- Abruf historischer RAM-Metriken
- Abruf historischer Storage-Metriken
- Speicherung als `MetricRecord`
- vollständiger automatisierter Collect-Workflow

---

## Zusammenfassung

Die aktuelle Teststrategie verfolgt das Ziel, den fachlichen Kernprozess der Anwendung automatisiert und reproduzierbar zu überprüfen.

Im Mittelpunkt stehen:

```text
Rohdaten
→ Aggregation
→ Bewertung
→ Speicherung
→ vCenter-Integration
```

Durch die automatisierten Tests und die klare Architekturtrennung kann die Anwendung schrittweise erweitert werden, ohne bestehende Kernfunktionalitäten unbeabsichtigt zu beschädigen.