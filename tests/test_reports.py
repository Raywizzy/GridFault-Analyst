import csv
import unittest

from src.gridfault_calculations import FaultStudyInput
from src.gridfault_reports import export_fault_study_csv


class ReportTests(unittest.TestCase):
    def test_export_fault_study_csv(self):
        from tempfile import TemporaryDirectory
        from pathlib import Path

        with TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "fault-study.csv"
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

            export_fault_study_csv(study, output)

            with output.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["fault_type"], "single_line_ground")
            self.assertEqual(rows[0]["primary_device"], "Fuse-1")


if __name__ == "__main__":
    unittest.main()
