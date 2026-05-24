import unittest
from math import isclose

from src.gridfault_calculations import (
    FaultStudyInput,
    calculate_fault_study,
    inverse_time_trip_seconds,
    result_as_dict,
)


def sample_study(**overrides):
    values = {
        "source_voltage_kv": 11.0,
        "transformer_mva": 10.0,
        "transformer_impedance_percent": 5.75,
        "feeder_length_km": 4.2,
        "conductor_r_ohm_per_km": 0.306,
        "conductor_x_ohm_per_km": 0.386,
        "fault_location_percent": 62.0,
        "fault_type": "single_line_ground",
        "relay_pickup_a": 800.0,
    }
    values.update(overrides)
    return FaultStudyInput(**values)


class CalculationTests(unittest.TestCase):
    def test_fault_current_matches_reference_case(self):
        result = calculate_fault_study(sample_study())

        self.assertTrue(isclose(result.base_current_a, 524.86, rel_tol=0.002))
        self.assertTrue(isclose(result.fault_current_a, 2086.54, rel_tol=0.002))
        self.assertEqual(result.severity, "elevated")
        self.assertEqual(result.primary_device, "Fuse-1")
        self.assertEqual(result.backup_device, "CB-2 Relay")


    def test_three_phase_fault_has_larger_current_than_line_ground(self):
        slg = calculate_fault_study(sample_study(fault_type="single_line_ground"))
        three_phase = calculate_fault_study(sample_study(fault_type="three_phase"))

        self.assertGreater(three_phase.fault_current_a, slg.fault_current_a)
        self.assertTrue(
            isclose(
                slg.fault_current_a / three_phase.fault_current_a,
                0.65,
                rel_tol=0.001,
            )
        )


    def test_fault_location_changes_fault_current(self):
        close_fault = calculate_fault_study(sample_study(fault_location_percent=15))
        remote_fault = calculate_fault_study(sample_study(fault_location_percent=95))

        self.assertGreater(close_fault.fault_current_a, remote_fault.fault_current_a)


    def test_invalid_fault_type_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "fault_type"):
            calculate_fault_study(sample_study(fault_type="phase_to_cloud"))


    def test_inverse_time_slows_when_current_is_lower(self):
        fast = inverse_time_trip_seconds(6000, 800, 0.24)
        slow = inverse_time_trip_seconds(1800, 800, 0.24)

        self.assertLess(fast, slow)


    def test_result_dict_rounds_values(self):
        data = result_as_dict(calculate_fault_study(sample_study()))

        self.assertEqual(data["severity"], "elevated")
        self.assertIsInstance(data["fault_current_a"], float)
        self.assertGreater(data["primary_trip_time_s"], 0)


if __name__ == "__main__":
    unittest.main()
