# Ivoris Daily Extraction Pipeline

**Clinero Coding Challenge** | Jean-Francois Desjardins | January 2026

---

## Challenge

> **Extraction-Pipeline für Ivoris bauen**
>
> Anforderung: Wenn User einen Karteikarteneintrag machen, soll täglich ein Update/Datenübertrag vorgenommen werden.

Build a daily extraction pipeline for Ivoris dental practice management system. When users create chart entries (Karteikarteneintrag), extract and transfer the data daily.

---

## Required Data

| Field (German) | Field (English) | Description |
|----------------|-----------------|-------------|
| Datum | Date | Entry date |
| Pat-ID | Patient ID | Patient identifier |
| Versicherungsstatus | Insurance Status | GKV/PKV/Selbstzahler |
| Karteikarteneintrag | Chart Entry | Medical record text |
| Leistungen (Ziffern) | Services | Treatment codes |

**Output Format:** CSV and JSON

---

## Quick Start

```bash
# 1. Clone and setup
cd ivoris-pipeline
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Install ODBC drivers (macOS)
brew install unixodbc
brew tap microsoft/mssql-release
HOMEBREW_ACCEPT_EULA=Y brew install msodbcsql18

# 3. Start database
docker-compose up -d

# 4. Restore database
./scripts/restore-database.sh

# 5. Run extraction
python src/main.py --daily-extract
```

---

## Usage

```bash
# Extract yesterday's chart entries (default)
python src/main.py --daily-extract

# Extract specific date
python src/main.py --daily-extract --date 2026-01-12

# Output format
python src/main.py --daily-extract --format csv
python src/main.py --daily-extract --format json

# Test database connection
python src/main.py --test-connection
```

---

## Output Example

### CSV
```csv
date,patient_id,insurance_status,insurance_name,chart_entry,service_codes
2026-01-12,1,GKV,AOK Bayern,"Kontrolle, Befund unauffällig","01,Ä1"
```

### JSON
```json
{
  "extraction_timestamp": "2026-01-13T06:00:00",
  "target_date": "2026-01-12",
  "record_count": 1,
  "entries": [
    {
      "date": "2026-01-12",
      "patient_id": 1,
      "insurance_status": "GKV",
      "insurance_name": "AOK Bayern",
      "chart_entry": "Kontrolle, Befund unauffällig",
      "service_codes": ["01", "Ä1"]
    }
  ]
}
```

---

## Project Structure

```
ivoris-pipeline/
├── README.md                 # This file
├── CHALLENGE.md              # Challenge requirements
├── ACCEPTANCE.md             # Acceptance criteria (Gherkin)
├── SESSION_LOG.md            # Development history
├── requirements.txt          # Python dependencies
├── docker-compose.yml        # SQL Server container
├── src/
│   ├── main.py               # CLI entry point
│   ├── adapters/
│   │   └── database.py       # SQL Server connection
│   ├── models/
│   │   └── chart_entry.py    # ChartEntry dataclass
│   └── services/
│       └── daily_extract.py  # Extraction logic
├── scripts/
│   └── restore-database.sh   # Database restore
├── config/
│   ├── settings.py           # Configuration
│   └── .env.example          # Environment template
└── data/
    ├── input/                # Source files
    └── output/               # Extracted data
```

---

## Technical Stack

| Component | Technology |
|-----------|------------|
| Database | SQL Server 2019 (Docker) |
| Language | Python 3.11 |
| Driver | pyodbc + ODBC Driver 18 |
| Container | Docker with Rosetta (Apple Silicon) |

---

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│   Ivoris    │────▶│  Extraction  │────▶│  CSV / JSON     │
│   DentalDB  │     │   Service    │     │  Output Files   │
└─────────────┘     └──────────────┘     └─────────────────┘
      │                    │
      │                    │
      ▼                    ▼
┌─────────────┐     ┌──────────────┐
│  Tables:    │     │  Combines:   │
│  • KARTEI   │     │  • Date      │
│  • PATIENT  │     │  • Patient   │
│  • PATKASSE │     │  • Insurance │
│  • KASSEN   │     │  • Entry     │
│  • LEISTUNG │     │  • Services  │
└─────────────┘     └──────────────┘
```

---

## Scheduling (Production)

```bash
# Cron job - runs daily at 6:00 AM
0 6 * * * cd /path/to/ivoris-pipeline && .venv/bin/python src/main.py --daily-extract
```

---

## Documentation

- [CHALLENGE.md](./CHALLENGE.md) - Challenge requirements
- [ACCEPTANCE.md](./ACCEPTANCE.md) - Acceptance criteria
- [SESSION_LOG.md](./SESSION_LOG.md) - Development history

---

## Author

Jean-Francois Desjardins
Clinero Coding Challenge - January 2026
