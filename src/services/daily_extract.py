"""
Daily Extraction Service.

Extracts chart entries (Karteikarteneintrag) with patient, insurance,
and service information for a target date.

This is the core implementation of the challenge requirement:
"Daily update/data transfer when users make chart entries."
"""

import csv
import json
import logging
from datetime import date, datetime, timedelta
from pathlib import Path

from src.adapters.database import DatabaseAdapter
from src.models.chart_entry import ChartEntry

logger = logging.getLogger(__name__)


class DailyExtractService:
    """
    Daily extraction pipeline for Ivoris chart entries.

    Extracts:
    - Datum (Date)
    - Pat-ID (Patient ID)
    - Versicherungsstatus (Insurance Status)
    - Karteikarteneintrag (Chart Entry)
    - Leistungen (Service Codes)
    """

    def __init__(self, db: DatabaseAdapter, output_dir: Path | str = None):
        self.db = db
        self.output_dir = Path(output_dir) if output_dir else Path("data/output")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def extract_for_date(self, target_date: date) -> list[ChartEntry]:
        """
        Extract all chart entries for a specific date.

        Joins KARTEI, PATIENT, KASSE, and LEISTUNG tables.
        """
        # Convert to Ivoris format (YYYYMMDD integer)
        ivoris_date = int(target_date.strftime("%Y%m%d"))

        logger.info(f"Extracting entries for {target_date.isoformat()}")

        # Query: Chart entries with patient and insurance
        # Schema: KARTEI.PATNR -> PATIENT.ID, PATKASSE.PATNR, KASSEN.ID
        query = """
            SELECT
                k.ID as KARTEI_ID,
                k.PATNR,
                k.DATUM,
                k.BEMERKUNG,
                ka.NAME as KASSE_NAME,
                ka.ART as KASSE_ART
            FROM ck.KARTEI k
            LEFT JOIN ck.PATIENT p ON k.PATNR = p.ID
            LEFT JOIN ck.PATKASSE pk ON k.PATNR = pk.PATNR
            LEFT JOIN ck.KASSEN ka ON pk.KASSENID = ka.ID
            WHERE k.DATUM = ?
            AND (k.DELKZ = 0 OR k.DELKZ IS NULL)
            ORDER BY k.PATNR, k.ID
        """

        rows = self.db.execute_query(query, (ivoris_date,))
        logger.info(f"Found {len(rows)} chart entries")

        if not rows:
            return []

        # Query: Service codes for the same date
        # Note: LEISTUNG.PATIENTID = PATIENT.ID = KARTEI.PATNR
        services_query = """
            SELECT PATIENTID, LEISTUNG
            FROM ck.LEISTUNG
            WHERE DATUM = ?
            AND (DELKZ = 0 OR DELKZ IS NULL)
            ORDER BY PATIENTID, ID
        """

        services_rows = self.db.execute_query(services_query, (ivoris_date,))

        # Group services by patient (LEISTUNG.PATIENTID = KARTEI.PATNR)
        services_by_patient: dict[int, list[str]] = {}
        for svc in services_rows:
            pid = svc.get("PATIENTID")
            code = svc.get("LEISTUNG")
            if pid and code:
                if pid not in services_by_patient:
                    services_by_patient[pid] = []
                if code not in services_by_patient[pid]:
                    services_by_patient[pid].append(code)

        # Build ChartEntry objects
        entries = []
        for row in rows:
            patient_id = row.get("PATNR")
            services = services_by_patient.get(patient_id, [])
            entry = ChartEntry.from_ivoris_row(row, services)
            entries.append(entry)

        return entries

    def export_to_csv(self, entries: list[ChartEntry], target_date: date) -> Path:
        """Export entries to CSV file."""
        filename = f"daily_extract_{target_date.isoformat()}.csv"
        filepath = self.output_dir / filename

        fieldnames = [
            "date", "patient_id", "insurance_status",
            "insurance_name", "chart_entry", "service_codes"
        ]

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for entry in entries:
                writer.writerow(entry.to_csv_row())

        logger.info(f"Created: {filepath}")
        return filepath

    def export_to_json(self, entries: list[ChartEntry], target_date: date) -> Path:
        """Export entries to JSON file."""
        filename = f"daily_extract_{target_date.isoformat()}.json"
        filepath = self.output_dir / filename

        output = {
            "extraction_timestamp": datetime.now().isoformat(),
            "target_date": target_date.isoformat(),
            "record_count": len(entries),
            "entries": [entry.to_dict() for entry in entries]
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        logger.info(f"Created: {filepath}")
        return filepath

    def run(self, target_date: date = None, output_format: str = "both") -> dict:
        """
        Run the daily extraction pipeline.

        Args:
            target_date: Date to extract (default: yesterday)
            output_format: "csv", "json", or "both"

        Returns:
            Dict with extraction results
        """
        if target_date is None:
            target_date = date.today() - timedelta(days=1)

        # Extract
        entries = self.extract_for_date(target_date)

        result = {
            "target_date": target_date.isoformat(),
            "extraction_timestamp": datetime.now().isoformat(),
            "record_count": len(entries),
            "output_files": {}
        }

        # Export
        if output_format in ("csv", "both"):
            csv_path = self.export_to_csv(entries, target_date)
            result["output_files"]["csv"] = str(csv_path)

        if output_format in ("json", "both"):
            json_path = self.export_to_json(entries, target_date)
            result["output_files"]["json"] = str(json_path)

        logger.info(f"Extraction complete: {len(entries)} entries")

        return result
