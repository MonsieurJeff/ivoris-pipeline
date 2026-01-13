# Acceptance Criteria

**Ivoris Daily Extraction Pipeline** | Gherkin Format

---

## Feature: Daily Chart Entry Extraction

As a dental practice administrator,
I want to extract daily chart entries with patient and insurance information,
So that I can transfer data to external systems automatically.

---

### Scenario 1: Extract chart entries for a specific date ✅

```gherkin
Given the Ivoris database is connected
And chart entries exist for date "2026-01-12"
When I run the daily extraction for "2026-01-12"
Then the output should contain all chart entries from that date
And each entry should include:
  | Field            | Description                    |
  | date             | Entry date (ISO 8601)          |
  | patient_id       | Patient identifier             |
  | insurance_status | GKV/PKV/Selbstzahler           |
  | chart_entry      | Medical record text            |
  | service_codes    | Treatment codes                |
```

---

### Scenario 2: Output to CSV format ✅

```gherkin
Given chart entries exist for the target date
When I run extraction with "--format csv"
Then a CSV file should be created at "data/output/ivoris_chart_entries_YYYY-MM-DD.csv"
And the CSV should have headers:
  | date | patient_id | insurance_status | insurance_name | chart_entry | service_codes |
And German characters (ä, ö, ü, ß) should be encoded as UTF-8
```

---

### Scenario 3: Output to JSON format ✅

```gherkin
Given chart entries exist for the target date
When I run extraction with "--format json"
Then a JSON file should be created at "data/output/ivoris_chart_entries_YYYY-MM-DD.json"
And the JSON should have structure:
  {
    "extraction_timestamp": "...",
    "target_date": "2026-01-12",
    "record_count": N,
    "entries": [...]
  }
And service_codes should be an array of strings
```

---

### Scenario 4: Insurance status mapping ✅

```gherkin
Given a patient has KASSE.TYP = "G"
Then insurance_status should be "GKV"

Given a patient has KASSE.TYP = "P"
Then insurance_status should be "PKV"

Given a patient has no insurance reference (KASSEID is NULL)
Then insurance_status should be "Selbstzahler"
```

---

### Scenario 5: Link services to chart entries ✅

```gherkin
Given a chart entry exists for patient 1 on date "2026-01-12"
And treatments exist in LEISTUNG for patient 1 on date "2026-01-12":
  | LEISTUNG |
  | 01       |
  | Ä1       |
  | 2060     |
When the daily extraction runs
Then the entry should have service_codes = ["01", "Ä1", "2060"]
```

---

### Scenario 6: Handle empty results ✅

```gherkin
Given no chart entries exist for date "2026-12-25"
When I run the daily extraction for "2026-12-25"
Then the output file should be created
And it should contain zero entries
And the extraction should complete successfully (exit code 0)
```

---

### Scenario 7: Default to yesterday ✅

```gherkin
Given today is "2026-01-13"
When I run extraction without specifying a date
Then the extraction should target "2026-01-12" (yesterday)
```

---

## Acceptance Summary

| # | Scenario | Priority | Status |
|---|----------|----------|--------|
| 1 | Extract chart entries for date | P0 | ✅ |
| 2 | CSV output format | P0 | ✅ |
| 3 | JSON output format | P0 | ✅ |
| 4 | Insurance status mapping | P0 | ✅ |
| 5 | Link services to entries | P0 | ✅ |
| 6 | Handle empty results | P1 | ✅ |
| 7 | Default to yesterday | P1 | ✅ |

**Legend:**
- P0 = Must have (core requirement)
- P1 = Should have (production readiness)

---

## Definition of Done

The challenge is complete when:

- [x] All P0 scenarios pass
- [x] CLI command `--daily-extract` works
- [x] CSV output file is correct
- [x] JSON output file is correct
- [x] Insurance status is properly resolved
- [x] Service codes are linked to chart entries
- [x] Code is documented

---

## Test Commands

```bash
# Test database connection
python src/main.py --test-connection

# Run extraction
python src/main.py --daily-extract --date 2026-01-12

# Verify output
cat data/output/ivoris_chart_entries_2026-01-12.csv
cat data/output/ivoris_chart_entries_2026-01-12.json
```
