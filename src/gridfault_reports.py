"""CSV reporting helpers for GridFault Analyst."""

from __future__ import annotations

import csv
from pathlib import Path

from .gridfault_calculations import FaultStudyInput, calculate_fault_study, result_as_dict


FIELDNAMES = [
    "source_voltage_kv",
    "transformer_mva",
    "transformer_impedance_percent",
    "feeder_length_km",
    "fault_location_percent",
    "fault_type",
    "fault_current_a",
    "fault_mva",
    "per_unit_voltage_at_fault",
    "severity",
    "primary_device",
    "primary_trip_time_s",
    "backup_device",
    "backup_trip_time_s",
]


def export_fault_study_csv(study: FaultStudyInput, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result = result_as_dict(calculate_fault_study(study))
    row = {
        "source_voltage_kv": study.source_voltage_kv,
        "transformer_mva": study.transformer_mva,
        "transformer_impedance_percent": study.transformer_impedance_percent,
        "feeder_length_km": study.feeder_length_km,
        "fault_location_percent": study.fault_location_percent,
        "fault_type": study.fault_type,
        **result,
    }
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerow({field: row[field] for field in FIELDNAMES})
    return output_path
