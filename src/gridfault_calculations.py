"""Fault-current and protection-coordination calculations.

The equations here intentionally stay transparent enough for a portfolio
project: three-phase RMS symmetrical current is calculated from per-unit
source/transformer plus feeder impedance, with simple fault-type multipliers
when sequence network data is not available.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt


FAULT_MULTIPLIERS = {
    "three_phase": 1.0,
    "line_to_line": 0.866,
    "single_line_ground": 0.65,
}


@dataclass(frozen=True)
class FaultStudyInput:
    source_voltage_kv: float
    transformer_mva: float
    transformer_impedance_percent: float
    feeder_length_km: float
    conductor_r_ohm_per_km: float
    conductor_x_ohm_per_km: float
    fault_location_percent: float
    fault_type: str
    relay_pickup_a: float = 800.0


@dataclass(frozen=True)
class ProtectionDevice:
    name: str
    device_type: str
    location_km: float
    pickup_a: float
    time_dial: float


@dataclass(frozen=True)
class FaultStudyResult:
    base_current_a: float
    base_impedance_ohm: float
    feeder_impedance_ohm: float
    total_impedance_pu: float
    three_phase_fault_current_a: float
    fault_current_a: float
    fault_mva: float
    per_unit_voltage_at_fault: float
    xr_ratio: float
    severity: str
    primary_device: str
    primary_trip_time_s: float
    backup_device: str
    backup_trip_time_s: float


def validate_input(study: FaultStudyInput) -> None:
    numeric_fields = {
        "source_voltage_kv": study.source_voltage_kv,
        "transformer_mva": study.transformer_mva,
        "transformer_impedance_percent": study.transformer_impedance_percent,
        "feeder_length_km": study.feeder_length_km,
        "conductor_r_ohm_per_km": study.conductor_r_ohm_per_km,
        "conductor_x_ohm_per_km": study.conductor_x_ohm_per_km,
        "relay_pickup_a": study.relay_pickup_a,
    }
    for name, value in numeric_fields.items():
        if value <= 0:
            raise ValueError(f"{name} must be greater than zero")
    if not 0 <= study.fault_location_percent <= 100:
        raise ValueError("fault_location_percent must be between 0 and 100")
    if study.fault_type not in FAULT_MULTIPLIERS:
        allowed = ", ".join(sorted(FAULT_MULTIPLIERS))
        raise ValueError(f"fault_type must be one of: {allowed}")


def inverse_time_trip_seconds(current_a: float, pickup_a: float, time_dial: float) -> float:
    """IEC-style standard inverse approximation, clamped for display."""
    if current_a <= pickup_a:
        return 999.0
    multiple = current_a / pickup_a
    trip_time = time_dial * 0.14 / ((multiple**0.02) - 1)
    return max(0.03, min(999.0, trip_time))


def default_devices(feeder_length_km: float, relay_pickup_a: float) -> list[ProtectionDevice]:
    midpoint = feeder_length_km * 0.45
    downstream = feeder_length_km * 0.78
    return [
        ProtectionDevice("Fuse-2", "Fuse", downstream, 1500.0, 0.055),
        ProtectionDevice("Fuse-1", "Fuse", midpoint, 1800.0, 0.095),
        ProtectionDevice("CB-2 Relay", "Circuit Breaker", 0.15, relay_pickup_a, 0.80),
        ProtectionDevice("CB-1 Source", "Circuit Breaker", 0.0, relay_pickup_a, 1.20),
    ]


def calculate_fault_study(study: FaultStudyInput) -> FaultStudyResult:
    validate_input(study)

    base_current_a = study.transformer_mva * 1_000_000 / (
        sqrt(3) * study.source_voltage_kv * 1_000
    )
    base_impedance_ohm = (study.source_voltage_kv * 1_000) ** 2 / (
        study.transformer_mva * 1_000_000
    )
    distance_to_fault_km = study.feeder_length_km * study.fault_location_percent / 100
    feeder_r = distance_to_fault_km * study.conductor_r_ohm_per_km
    feeder_x = distance_to_fault_km * study.conductor_x_ohm_per_km
    feeder_impedance_ohm = sqrt(feeder_r**2 + feeder_x**2)
    source_impedance_pu = study.transformer_impedance_percent / 100
    feeder_impedance_pu = feeder_impedance_ohm / base_impedance_ohm
    total_impedance_pu = source_impedance_pu + feeder_impedance_pu

    three_phase_fault_current_a = base_current_a / total_impedance_pu
    fault_current_a = three_phase_fault_current_a * FAULT_MULTIPLIERS[study.fault_type]
    fault_mva = sqrt(3) * study.source_voltage_kv * fault_current_a / 1000
    per_unit_voltage_at_fault = min(1.0, max(0.0, feeder_impedance_pu / total_impedance_pu))
    xr_ratio = feeder_x / feeder_r if feeder_r else 999.0

    devices = default_devices(study.feeder_length_km, study.relay_pickup_a)
    downstream_devices = [
        device for device in devices if device.location_km <= distance_to_fault_km + 0.001
    ]
    candidates = downstream_devices or devices
    ranked = sorted(candidates, key=lambda device: device.location_km, reverse=True)
    primary = ranked[0]
    backup = ranked[1] if len(ranked) > 1 else ranked[0]
    primary_time = inverse_time_trip_seconds(
        fault_current_a, primary.pickup_a, primary.time_dial
    )
    backup_time = inverse_time_trip_seconds(
        fault_current_a, backup.pickup_a, backup.time_dial
    )

    if fault_current_a >= 10_000:
        severity = "critical"
    elif fault_current_a >= 5_000:
        severity = "high"
    elif fault_current_a >= 2_000:
        severity = "elevated"
    else:
        severity = "normal"

    return FaultStudyResult(
        base_current_a=base_current_a,
        base_impedance_ohm=base_impedance_ohm,
        feeder_impedance_ohm=feeder_impedance_ohm,
        total_impedance_pu=total_impedance_pu,
        three_phase_fault_current_a=three_phase_fault_current_a,
        fault_current_a=fault_current_a,
        fault_mva=fault_mva,
        per_unit_voltage_at_fault=per_unit_voltage_at_fault,
        xr_ratio=xr_ratio,
        severity=severity,
        primary_device=primary.name,
        primary_trip_time_s=primary_time,
        backup_device=backup.name,
        backup_trip_time_s=backup_time,
    )


def result_as_dict(result: FaultStudyResult) -> dict[str, float | str]:
    return {
        "base_current_a": round(result.base_current_a, 2),
        "base_impedance_ohm": round(result.base_impedance_ohm, 4),
        "feeder_impedance_ohm": round(result.feeder_impedance_ohm, 4),
        "total_impedance_pu": round(result.total_impedance_pu, 4),
        "three_phase_fault_current_a": round(result.three_phase_fault_current_a, 2),
        "fault_current_a": round(result.fault_current_a, 2),
        "fault_mva": round(result.fault_mva, 2),
        "per_unit_voltage_at_fault": round(result.per_unit_voltage_at_fault, 3),
        "xr_ratio": round(result.xr_ratio, 2),
        "severity": result.severity,
        "primary_device": result.primary_device,
        "primary_trip_time_s": round(result.primary_trip_time_s, 3),
        "backup_device": result.backup_device,
        "backup_trip_time_s": round(result.backup_trip_time_s, 3),
    }
