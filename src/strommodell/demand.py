"""Demand-profile scaling for the electrified-system scenario."""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class ScaledDemand:
    """A scaled load profile and its observable summary metrics."""

    load_gw: tuple[float, ...]
    annual_twh: float
    mean_gw: float
    peak_gw: float
    step_hours: float


def scale_demand(
    load_gw: Sequence[float],
    annual_twh: float = 1100,
    *,
    step_hours: float = 1.0,
) -> ScaledDemand:
    """Scale a load profile to a target annual electrical work."""
    if not math.isfinite(annual_twh) or annual_twh <= 0:
        raise ValueError(f"Annual demand must be positive: {annual_twh}")
    if not math.isfinite(step_hours) or step_hours <= 0:
        raise ValueError(f"Step duration must be positive: {step_hours}")
    values = tuple(float(value) for value in load_gw)
    if not values:
        raise ValueError("Load profile must contain at least one value")
    if any(not math.isfinite(value) or value < 0 for value in values):
        raise ValueError("Load profile must contain finite non-negative values")
    input_work_gwh = math.fsum(values) * step_hours
    if input_work_gwh <= 0:
        raise ValueError("Load profile must contain positive work")

    factor = annual_twh * 1000 / input_work_gwh
    scaled = tuple(value * factor for value in values)
    return ScaledDemand(
        load_gw=scaled,
        annual_twh=math.fsum(scaled) * step_hours / 1000,
        mean_gw=math.fsum(scaled) / len(scaled),
        peak_gw=max(scaled),
        step_hours=step_hours,
    )
