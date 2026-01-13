# Challenge: Ivoris Daily Extraction Pipeline

## Original Requirement

> **Extraction-Pipeline für Ivoris bauen**
>
> Anforderung: Wenn User einen Karteikarteneintrag machen, soll täglich ein Update/Datenübertrag vorgenommen werden.
>
> Datenbedarf: Datum, Pat-ID, Versicherungsstatus, Karteikarteneintrag, Leistungen (Ziffern)
>
> Output: csv/json

---

## Interpretation

**Goal:** Build a data extraction pipeline that runs daily to transfer patient chart entries from Ivoris to external systems.

**Trigger:** Daily batch process (e.g., cron job at 6:00 AM)

**Scope:** Extract previous day's chart entries with related patient and billing information

---

## Data Requirements

### Required Fields

| # | German | English | Source | Description |
|---|--------|---------|--------|-------------|
| 1 | Datum | Date | KARTEI.DATUM | Date of chart entry |
| 2 | Pat-ID | Patient ID | KARTEI.PATIENTID | Patient identifier |
| 3 | Versicherungsstatus | Insurance Status | KASSE.TYP | GKV/PKV/Selbstzahler |
| 4 | Karteikarteneintrag | Chart Entry | KARTEI.EINTRAG | Medical record text |
| 5 | Leistungen (Ziffern) | Services | LEISTUNG.LEISTUNG | Treatment codes |

### Database Tables

```
KARTEI (Chart Entries)
├── ID            - Primary key
├── PATIENTID     - FK to PATIENT
├── DATUM         - Date (YYYYMMDD integer)
├── EINTRAG       - Entry text
└── DELKZ         - Deletion flag

PATIENT (Patients)
├── ID            - Primary key
├── KASSEID       - FK to KASSE
├── P_NAME        - Last name
└── P_VORNAME     - First name

KASSE (Insurance)
├── ID            - Primary key
├── BEZEICHNUNG   - Provider name
└── TYP           - Type (G=GKV, P=PKV)

LEISTUNG (Services)
├── ID            - Primary key
├── PATIENTID     - FK to PATIENT
├── DATUM         - Date (YYYYMMDD)
└── LEISTUNG      - Service code
```

---

## Solution Design

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Daily Extraction Pipeline                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  06:00 AM                                                    │
│     │                                                        │
│     ▼                                                        │
│  ┌──────────┐    ┌───────────────┐    ┌─────────────────┐   │
│  │  Ivoris  │───▶│  Python       │───▶│  Output Files   │   │
│  │  SQL DB  │    │  Extraction   │    │  (CSV/JSON)     │   │
│  └──────────┘    └───────────────┘    └─────────────────┘   │
│                         │                                    │
│                         ▼                                    │
│                  ┌───────────────┐                          │
│                  │  Data Model   │                          │
│                  │  ChartEntry   │                          │
│                  └───────────────┘                          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Input:** Target date (default: yesterday)
2. **Query:** Join KARTEI + PATIENT + KASSE + LEISTUNG
3. **Transform:** Map German columns to clean fields
4. **Output:** CSV and/or JSON files

### Insurance Status Mapping

| KASSE.TYP | Status | Description |
|-----------|--------|-------------|
| G | GKV | Gesetzliche Krankenversicherung (Public) |
| P | PKV | Private Krankenversicherung (Private) |
| NULL | Selbstzahler | Self-pay |

---

## Implementation

### CLI Interface

```bash
# Default: Extract yesterday's entries
python src/main.py --daily-extract

# Specific date
python src/main.py --daily-extract --date 2026-01-12

# Output format
python src/main.py --daily-extract --format csv
python src/main.py --daily-extract --format json
```

### Core Query

```sql
SELECT
    k.ID, k.PATIENTID, k.DATUM, k.EINTRAG,
    ka.BEZEICHNUNG AS insurance_name,
    ka.TYP AS insurance_type
FROM ck.KARTEI k
LEFT JOIN ck.PATIENT p ON k.PATIENTID = p.ID
LEFT JOIN ck.KASSE ka ON p.KASSEID = ka.ID
WHERE k.DATUM = ?
  AND (k.DELKZ = 0 OR k.DELKZ IS NULL)
```

### Output Schema

```python
@dataclass
class ChartEntry:
    date: date              # Datum
    patient_id: int         # Pat-ID
    insurance_status: str   # Versicherungsstatus
    insurance_name: str     # Provider name
    chart_entry: str        # Karteikarteneintrag
    service_codes: list     # Leistungen (Ziffern)
```

---

## Technical Decisions

| Decision | Rationale |
|----------|-----------|
| SQL Server in Docker | macOS cannot run SQL Server natively |
| pyodbc driver | Standard Microsoft ODBC driver support |
| Python dataclasses | Type-safe, clean data modeling |
| Default to yesterday | Standard ETL pattern for daily batches |
| UTF-8 encoding | German characters (ä, ö, ü, ß) |

---

## Success Criteria

1. ✅ All 5 required fields extracted
2. ✅ Insurance status correctly mapped (GKV/PKV/Selbstzahler)
3. ✅ Service codes linked to chart entries
4. ✅ CSV output with proper headers
5. ✅ JSON output with structured format
6. ✅ Handles empty results gracefully
7. ✅ Can be scheduled via cron
