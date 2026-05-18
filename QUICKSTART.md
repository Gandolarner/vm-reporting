# VM Reporting Quickstart

## Voraussetzungen

- Python 3.12 installiert
- Git installiert

## Regulärer Modus mit VCenter-Verbindung

### Virtuelle Umgebung aktivieren

```powershell
.venv\Scripts\Activate.ps1
```

### Datenbank initialisieren

```powershell
python -m app.main init-db
```

### Metriken sammeln

```powershell
python -m app.main collect-metrics
```

### Monatsaggregation

```powershell
python -m app.main aggregate 2026-05
```

### Report erzeugen

```powershell
python -m app.main report 2026-05
```

### Daily Workflow

```powershell
python -m app.main daily-workflow
```

### Monthly Workflow

```powershell
python -m app.main monthly-workflow
```

---

## Demo-Modus

### Aktivieren

```powershell
$env:APP_ENV="demo"
```

### Demo-Datenbank neu erzeugen

```powershell
Remove-Item .\data\demo_vm_reporting.db -ErrorAction SilentlyContinue
```

### Demo-Daten erzeugen

```powershell
python -m app.main init-db
python -m app.main seed-demo-data 2026-05
```

### Demo-Report erzeugen

```powershell
python -m app.main aggregate 2026-05
python -m app.main report 2026-05
```

### Demo-Modus verlassen

```powershell
Remove-Item Env:APP_ENV
```
