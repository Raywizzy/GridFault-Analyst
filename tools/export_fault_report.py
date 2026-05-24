#!/usr/bin/env python3
"""Export the default GridFault Analyst study as CSV."""

from pathlib import Path

from src.gridfault_calculations import FaultStudyInput
from src.gridfault_reports import export_fault_study_csv


def main() -> None:
    study = FaultStudyInput(
        source_voltage_kv=11.0,
        transformer_mva=10.0,
        transformer_impedance_percent=5.75,
        feeder_length_km=4.2,
        conductor_r_ohm_per_km=0.306,
        conductor_x_ohm_per_km=0.386,
        fault_location_percent=62.0,
        fault_type="single_line_ground",
    )
    output = export_fault_study_csv(study, Path("reports/sample_fault_study.csv"))
    print(output)


if __name__ == "__main__":
    main()
