# Datenbankkonzept – VM-Reporting vCenter

## Zweck der Datenbankschicht

Die Datenbankschicht kapselt den Zugriff auf die relationale Datenbank der Anwendung.

Sie ist verantwortlich für:

- Aufbau der Datenbankverbindung
- Bereitstellung von Datenbanksessions
- Definition der SQLAlchemy-Basisklasse für Models
- spätere Initialisierung der Tabellenstruktur
- zentrale Trennung zwischen Anwendungscode und Datenbankzugriff

---

## Entscheidung für SQLAlchemy

Der Datenbankzugriff erfolgt über SQLAlchemy.

SQLAlchemy ermöglicht es, mit Python-Klassen zu arbeiten, die Datenbanktabellen repräsentieren. Dadurch kann der Anwendungscode weitgehend unabhängig von konkreten SQL-Anweisungen geschrieben werden.

Ein weiterer Vorteil ist, dass die verwendete Datenbank über eine Verbindungszeichenfolge konfiguriert werden kann.

Beispiele:

```env
DATABASE_URL=sqlite:///data/vm_reporting.db
```

oder später optional:

```env
DATABASE_URL=postgresql+psycopg://vm_user:vm_password@localhost:5432/vm_reporting
```

Dadurch kann die Anwendung zunächst mit SQLite entwickelt und später bei Bedarf auf PostgreSQL umgestellt werden.

---

## Zentrale Datenbankverbindung

Die Datei `app/database/connection.py` definiert die zentrale Datenbankanbindung.

Sie enthält:

- `engine`
- `SessionLocal`
- `Base`
- `init_db()`

---

## Engine

Die Engine ist die zentrale Schnittstelle zwischen SQLAlchemy und der Datenbank.

Sie wird mit der Datenbank-URL aus der zentralen Konfiguration erstellt:

```python
engine = create_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
)
```

Die Engine kennt dadurch die verwendete Datenbank und stellt die Grundlage für alle späteren Datenbankoperationen bereit.

---

## Datenbank-URL

Die konkrete Datenbank wird über `settings.DATABASE_URL` definiert.

Dadurch wird vermieden, dass Datenbankinformationen fest im Code hinterlegt werden.

Die Datenbank-URL wird zentral über `app/config/settings.py` aus der `.env`-Datei geladen.

---

## SQL-Ausgabe mit echo

Der Parameter `echo=False` verhindert, dass SQLAlchemy jede erzeugte SQL-Anweisung im Terminal ausgibt.

Für Debugging kann dieser Wert temporär auf `True` gesetzt werden.

Im regulären Betrieb bleibt `echo=False`, damit die Konsolenausgabe übersichtlich bleibt.

---

## SQLAlchemy-2.x-Verhalten

Der Parameter `future=True` aktiviert das moderne Verhalten von SQLAlchemy 2.x.

Dadurch wird die Anwendung direkt auf dem aktuellen empfohlenen SQLAlchemy-Stil aufgebaut.

---

## SessionLocal

`SessionLocal` ist eine Session-Factory.

Sie erzeugt bei Bedarf neue Datenbanksessions:

```python
db = SessionLocal()
```

Eine Session ist eine Arbeitseinheit mit der Datenbank. Über sie werden Daten gelesen, geändert und gespeichert.

---

## Eigenschaften der Session

Die Session wird folgendermaßen konfiguriert:

```python
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    future=True,
)
```

### Bindung an die Engine

```python
bind=engine
```

Dadurch verwenden alle erzeugten Sessions dieselbe zentrale Datenbankverbindung.

### Kein automatischer Flush

```python
autoflush=False
```

Änderungen werden nicht unkontrolliert automatisch an die Datenbank übertragen. Dadurch bleibt das Verhalten besser nachvollziehbar.

### Kein automatischer Commit

```python
autocommit=False
```

Änderungen werden erst dauerhaft gespeichert, wenn explizit `commit()` aufgerufen wird.

Beispiel:

```python
db.add(vm)
db.commit()
```

Das erhöht die Kontrolle über Datenbankoperationen.

---

## Base

`Base` ist die gemeinsame Basisklasse für alle SQLAlchemy-Models.

Sie wird so erzeugt:

```python
Base = declarative_base()
```

Alle Datenbankmodelle erben später von dieser Klasse.

Beispiel:

```python
class VirtualMachine(Base):
    ...
```

Dadurch erkennt SQLAlchemy, dass diese Klasse eine Datenbanktabelle beschreibt.

---

## Metadaten der Models

Alle Models, die von `Base` erben, werden in `Base.metadata` registriert.

Diese Metadaten enthalten Informationen über:

- Tabellenname
- Spalten
- Datentypen
- Beziehungen
- Fremdschlüssel

---

## Initialisierung der Datenbank

Die Funktion `init_db()` erzeugt die Datenbanktabellen anhand der definierten Models:

```python
def init_db() -> None:
    Base.metadata.create_all(bind=engine)
```

Wichtig: Tabellen können erst erzeugt werden, wenn Models definiert und importiert wurden.

---

## Rolle im Gesamtprojekt

Die Datei `connection.py` bildet die technische Grundlage für alle späteren Datenbankoperationen.

Geplanter Ablauf:

```text
.env
↓
settings.py
↓
connection.py
↓
models.py
↓
repositories.py
↓
processing/reporting
```

---

## Vorteile dieser Struktur

Die zentrale Datenbankschicht bietet folgende Vorteile:

- einheitliche Datenbankkonfiguration
- austauschbare Datenbanktechnologie
- bessere Wartbarkeit
- klare Trennung von Datenbankzugriff und Fachlogik
- bessere Testbarkeit
- saubere Grundlage für SQLite und PostgreSQL

---

## Aktueller Stand

Bereits umgesetzt:

- zentrale Konfiguration über `settings.py`
- SQLAlchemy-Engine
- Session-Factory `SessionLocal`
- gemeinsame Model-Basisklasse `Base`
- Initialisierungsfunktion `init_db()`

Noch offen:

- Definition der Datenbankmodelle
- Erstellung der Tabellen
- Repository-Klassen für Datenbankoperationen
- Testdaten
- Aggregationslogik
