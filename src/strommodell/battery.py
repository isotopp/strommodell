"""Four-hour battery dispatch for a residual-load profile."""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class BatteryDispatch:
    """Observable battery dispatch results for every input interval."""

    state_of_charge_gwh: tuple[float, ...]
    charge_gw: tuple[float, ...]
    discharge_gw: tuple[float, ...]
    curtailment_gw: tuple[float, ...]
    remaining_residual_gw: tuple[float, ...]
    energy_capacity_gwh: float
    power_gw: float
    duration_hours: float
    initial_soc_gwh: float
    final_soc_gwh: float
    throughput_gwh: float


def dispatch_battery(
    residual_load: Sequence[float],
    *,
    power_gw: float,
    duration_hours: float = 4.0,
    initial_soc_gwh: float | None = None,
    charge_efficiency: float = 0.9,
    discharge_efficiency: float = 0.9,
    step_hours: float = 1.0,
) -> BatteryDispatch:
    """Dispatch a battery against signed residual load in GW."""
    _validate_positive("power_gw", power_gw)
    _validate_positive("duration_hours", duration_hours)
    _validate_positive("step_hours", step_hours)
    _validate_efficiency("charge_efficiency", charge_efficiency)
    _validate_efficiency("discharge_efficiency", discharge_efficiency)
    residual = tuple(float(value) for value in residual_load)
    if not residual:
        raise ValueError("Residual-load profile must contain at least one value")
    if any(not math.isfinite(value) for value in residual):
        raise ValueError("Residual-load profile must contain finite values")

    energy_capacity = power_gw * duration_hours
    initial = energy_capacity / 2 if initial_soc_gwh is None else initial_soc_gwh
    if not math.isfinite(initial) or not 0 <= initial <= energy_capacity:
        raise ValueError("Initial state of charge must be within battery capacity")

    soc = initial
    state_of_charge: list[float] = []
    charge: list[float] = []
    discharge: list[float] = []
    curtailment: list[float] = []
    remaining_residual: list[float] = []
    throughput = 0.0

    for value in residual:
        charged_gw = 0.0
        discharged_gw = 0.0
        curtailed_gw = 0.0
        remaining_gw = 0.0
        if value < 0:
            surplus_gw = -value
            charged_gw = min(power_gw, surplus_gw)
            capacity_limited_charge = (energy_capacity - soc) / (
                charge_efficiency * step_hours
            )
            charged_gw = min(charged_gw, max(capacity_limited_charge, 0.0))
            soc += charged_gw * step_hours * charge_efficiency
            curtailed_gw = surplus_gw - charged_gw
        else:
            available_discharge = soc * discharge_efficiency / step_hours
            discharged_gw = min(power_gw, value, available_discharge)
            soc -= discharged_gw * step_hours / discharge_efficiency
            remaining_gw = value - discharged_gw
        soc = min(max(soc, 0.0), energy_capacity)
        state_of_charge.append(soc)
        charge.append(charged_gw)
        discharge.append(discharged_gw)
        curtailment.append(curtailed_gw)
        remaining_residual.append(remaining_gw)
        throughput += (charged_gw + discharged_gw) * step_hours

    return BatteryDispatch(
        state_of_charge_gwh=tuple(state_of_charge),
        charge_gw=tuple(charge),
        discharge_gw=tuple(discharge),
        curtailment_gw=tuple(curtailment),
        remaining_residual_gw=tuple(remaining_residual),
        energy_capacity_gwh=energy_capacity,
        power_gw=power_gw,
        duration_hours=duration_hours,
        initial_soc_gwh=initial,
        final_soc_gwh=soc,
        throughput_gwh=throughput,
    )


def _validate_positive(name: str, value: float) -> None:
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be positive")


def _validate_efficiency(name: str, value: float) -> None:
    if not math.isfinite(value) or not 0 < value <= 1:
        raise ValueError(f"{name} must be greater than zero and at most one")
