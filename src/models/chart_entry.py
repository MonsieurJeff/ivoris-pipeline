"""
Chart Entry (Karteikarteneintrag) data model.

Represents a daily chart entry with patient, insurance, and service information.
This is the core data structure for the extraction pipeline.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Any


def parse_ivoris_date(value: Any) -> date | None:
    """Parse Ivoris date format (YYYYMMDD integer)."""
    if value is None:
        return None
    try:
        date_str = str(value)
        if len(date_str) != 8:
            return None
        return date(
            year=int(date_str[:4]),
            month=int(date_str[4:6]),
            day=int(date_str[6:8])
        )
    except (ValueError, TypeError):
        return None


@dataclass
class ChartEntry:
    """
    Daily chart entry for extraction.

    Required fields (from challenge):
    - Datum (date)
    - Pat-ID (patient_id)
    - Versicherungsstatus (insurance_status)
    - Karteikarteneintrag (chart_entry)
    - Leistungen/Ziffern (service_codes)
    """

    # Required fields
    date: date
    patient_id: int
    insurance_status: str          # GKV / PKV / Selbstzahler
    insurance_name: str | None     # Provider name
    chart_entry: str               # Medical record text
    service_codes: list[str] = field(default_factory=list)

    # Optional metadata
    kartei_id: int | None = None

    @classmethod
    def from_ivoris_row(cls, row: dict, services: list[str] = None) -> "ChartEntry":
        """
        Create ChartEntry from database row.

        Maps Ivoris schema to clean field names:
        - PATNR -> patient_id
        - BEMERKUNG -> chart_entry
        - KASSE_ART -> insurance_status (P=PKV, others=GKV)
        """
        # Map KASSEN.ART to insurance status
        # 'P' = Private (PKV), numeric codes (1,4,6,8,9...) = Statutory (GKV)
        kasse_art = str(row.get("KASSE_ART", "") or "")
        if kasse_art.upper() == "P":
            insurance_status = "PKV"
        elif kasse_art:
            insurance_status = "GKV"
        else:
            insurance_status = "Selbstzahler"

        return cls(
            date=parse_ivoris_date(row.get("DATUM")),
            patient_id=row.get("PATNR"),
            insurance_status=insurance_status,
            insurance_name=row.get("KASSE_NAME"),
            chart_entry=row.get("BEMERKUNG") or "",
            service_codes=services or [],
            kartei_id=row.get("KARTEI_ID") or row.get("ID")
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON export."""
        return {
            "date": self.date.isoformat() if self.date else None,
            "patient_id": self.patient_id,
            "insurance_status": self.insurance_status,
            "insurance_name": self.insurance_name,
            "chart_entry": self.chart_entry,
            "service_codes": self.service_codes
        }

    def to_csv_row(self) -> dict:
        """Convert to dictionary for CSV export."""
        return {
            "date": self.date.isoformat() if self.date else "",
            "patient_id": self.patient_id,
            "insurance_status": self.insurance_status,
            "insurance_name": self.insurance_name or "",
            "chart_entry": self.chart_entry,
            "service_codes": ",".join(self.service_codes)
        }
