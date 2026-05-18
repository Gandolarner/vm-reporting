# Projektkonzept – VM-Reporting vCenter

## Projektübersicht

Im Rahmen des Abschlussprojekts für die Umschulung zum Fachinformatiker für Anwendungsentwicklung wird eine Python-Anwendung zur automatisierten Auswertung der Ressourcenauslastung virtueller Maschinen in einer VMware-vCenter-Umgebung entwickelt.

Die Anwendung soll VM-Metriken automatisiert erfassen, speichern, auswerten und in Form strukturierter Reports bereitstellen.

---

## Fachliches Projektziel

Ziel des Projekts ist die Entwicklung einer modular aufgebauten Anwendung zur:

- automatisierten Datenerfassung aus VMware vCenter
- Speicherung historischer VM-Metriken
- Aggregation und Bewertung der Daten
- Erzeugung strukturierter Monatsreports

Die Anwendung soll insbesondere Administratoren dabei unterstützen, Über- oder Unterauslastungen virtueller Maschinen zu erkennen und Ressourcen besser bewerten zu können.

---

## Anforderungen an die Datenerfassung

Die Anwendung soll VM-Metriken aus einem VMware vCenter abrufen.

Erfasst werden insbesondere:

- CPU-Auslastung
- RAM-Auslastung
- Storage-Auslastung

Die Daten sollen regelmäßig automatisiert für ein bestimmtes Zeitfenster abgerufen und als Rohdaten gespeichert werden.

---

## Anforderungen an die Datenhaltung

Die Anwendung speichert:

- VM-Stammdaten
- historische Metrikdaten
- aggregierte Monatswerte
- Bewertungsergebnisse

Die Trennung zwischen Rohdaten und Aggregationen ermöglicht nachvollziehbare und reproduzierbare Auswertungen.

---

## Anforderungen an die Datenverarbeitung

Die gespeicherten Rohdaten sollen monatlich aggregiert werden.

Berechnet werden:

- Durchschnittswerte
- Minimalwerte
- Maximalwerte

Zusätzlich erfolgt eine Bewertung anhand definierter Schwellenwerte.

---

## Anforderungen an das Reporting

Die Anwendung erzeugt strukturierte Reports mit:

- Übersicht aller VMs
- aggregierten Monatswerten
- Top-N-Auswertungen
- auffälligen Systemen
- optionalen Diagrammen

Die primäre Ausgabe erfolgt als HTML-Report.

Optional können später weitere Exportformate ergänzt werden:

- PDF
- Excel

---

## Eingesetzte Technologien

Die Anwendung wird in Python entwickelt.

Verwendete Hauptbibliotheken:

| Bibliothek | Zweck |
| --- | --- |
| pyVmomi | Zugriff auf VMware vCenter |
| SQLAlchemy | Datenbankzugriff |
| pandas | Datenaggregation |
| jinja2 | HTML-Templates |
| typer | CLI |
| rich | formatierte Konsolenausgabe |

---

## Aufbau der Systemarchitektur

Die Anwendung wird als modulare CLI-Anwendung umgesetzt.

Die Steuerung erfolgt über Kommandozeilenbefehle.

Beispiel:

```bash
python -m app.main collect
python -m app.main aggregate --month 2026-05
python -m app.main report --month 2026-05
```

---

## Entscheidung für eine modulare Projektstruktur

Die Anwendung wird in fachlich getrennte Module aufgeteilt:

```text
app/
├── cli/
├── config/
├── database/
├── processing/
├── reporting/
├── vcenter/
└── utils/
```

### Gründe für die Aufteilung

- bessere Wartbarkeit
- klare Verantwortlichkeiten
- bessere Testbarkeit
- spätere Erweiterbarkeit

---

## Entscheidung zur Trennung von Rohdaten und Aggregationen

Die Anwendung speichert zunächst Rohdaten und berechnet daraus anschließend Monatsaggregationen.

### Vorteile dieses Ansatzes

- Reports bleiben reproduzierbar
- Aggregationen können neu berechnet werden
- historische Daten bleiben erhalten
- verschiedene Auswertungen werden möglich

---

## Entscheidung für eine CLI-Anwendung

Die Anwendung wird bewusst als CLI-Anwendung umgesetzt.

### Gründe für die CLI-basierte Umsetzung

- Fokus auf Automatisierung
- geringere Komplexität
- einfache Integration in Aufgabenplanung
- Konzentration auf Backend-Logik

Die Anwendung benötigt kein interaktives Webfrontend.

---

## Entscheidung zur Datenbankabstraktion

Der Datenbankzugriff erfolgt über SQLAlchemy.

Dadurch kann die konkrete Datenbanktechnologie ausgetauscht werden.

### Unterstützte Datenbanksysteme

- SQLite (primäre Entwicklungsdatenbank)
- PostgreSQL (optionale Erweiterung)

---

## Entscheidung für SQLite als Entwicklungsdatenbank

Für die lokale Entwicklung wird SQLite verwendet.

### Gründe für SQLite

- einfache Einrichtung
- keine Serverinstallation notwendig
- schnelle lokale Entwicklung
- ausreichend für Prototyping und Tests

---

## Vorbereitung einer optionalen PostgreSQL-Nutzung

Die Architektur wird so gestaltet, dass später PostgreSQL verwendet werden kann.

Die Anbindung soll optional über Docker Compose erfolgen.

### Ziel der Erweiterbarkeit

- realitätsnähere Testumgebung
- bessere Skalierbarkeit
- Vorbereitung auf produktionsähnliche Szenarien

### Details

Weitere technische Details zur Datenbankschicht sind in `docs/datenbankkonzept.md` dokumentiert.

---

## Entscheidung für konfigurierbare Schwellenwerte

Schwellenwerte werden nicht fest im Code hinterlegt, sondern über Konfigurationsdateien definiert.

Beispiel:

```yaml
cpu:
  warning_above: 75
  critical_above: 90
```

### Vorteile der Konfigurationsdatei

- einfache Anpassbarkeit
- Trennung von Fachlogik und Code
- bessere Wartbarkeit

---

## Kapselung des VMware-vCenter-Zugriffs

Der Zugriff auf VMware vCenter wird in eigenen Modulen gekapselt.

### Ziele der Kapselung

- Trennung externer API-Zugriffe
- bessere Testbarkeit
- geringere Kopplung
- einfachere Wartung

---

## Vorläufiges Datenmodell

Geplante Haupttabellen:

| Tabelle | Inhalt |
| --- | --- |
| virtual_machines | VM-Stammdaten |
| metric_records | Rohdaten |
| monthly_aggregates | Monatsaggregationen |
| evaluation_results | Bewertungsergebnisse |

---

## Geplanter Verarbeitungsablauf

```text
vCenter
   ↓
Datenerfassung
   ↓
Speicherung Rohdaten
   ↓
Monatsaggregation
   ↓
Bewertung
   ↓
Reportgenerierung
```

---

## Geplante Projektstruktur

```text
vm-reporting/
├── app/
├── tests/
├── docs/
├── data/
├── output/
├── logs/
├── requirements.txt
├── .env.example
└── README.md
```

---

## Konzept zur Konfigurationsverwaltung

Die Anwendung verwendet:

- `.env` für technische Konfiguration
- YAML-Dateien für fachliche Konfiguration

Beispiel:

```env
DATABASE_URL=sqlite:///data/vm_reporting.db
```

---

## Konzept für Logging und Laufprotokolle

Die Anwendung soll Laufprotokolle erzeugen.

Beispiele:

- Start und Ende von Sammelläufen
- Anzahl verarbeiteter VMs
- Fehler beim Abruf
- erfolgreiche Reportgenerierung

---

## Geplantes Testkonzept

Geplant sind insbesondere Tests für:

- Aggregationslogik
- Bewertungslogik
- Datenbankoperationen

Zusätzlich sollen Tests mit simulierten Beispieldaten möglich sein.

---

## Konzept zur Automatisierung

Die Anwendung soll unabhängig ausführbar sein.

Optional ist eine Automatisierung über die Windows-Aufgabenplanung vorgesehen.

Beispiele:

- tägliche Datensammlung
- monatliche Reportgenerierung

---

## Abgrenzung des Projektumfangs

Nicht Bestandteil des Projekts:

- vollständiges Webfrontend
- Echtzeit-Monitoring
- produktiver Rollout
- Benutzerverwaltung

---

## Mögliche spätere Erweiterungen

Mögliche spätere Erweiterungen:

- PostgreSQL als Hauptdatenbank
- PDF-Export
- Excel-Export
- Diagramme
- Apache-Airflow-Orchestrierung
- zusätzliche Metriken
- Weboberfläche

---

## Aktueller Entwicklungsstand

Bereits umgesetzt:

- grundlegende Projektstruktur
- Python-Umgebung
- CLI-Grundgerüst mit Typer
- Konfigurationsdateien
- Basisstruktur der Anwendung

Geplant als nächste Schritte:

1. zentrale Konfigurationsverwaltung --> done
2. SQLAlchemy-Datenbankanbindung --> done
3. Datenmodell --> done
4. SQLite-Initialisierung --> done
5. Testdaten
6. Aggregationslogik
7. Reporting
8. vCenter-Anbindung
