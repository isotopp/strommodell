"""Technology-specific scenario scaling."""

from __future__ import annotations

import math
from dataclasses import dataclass

from .reference import ReferenceDataError, ReferenceYear


@dataclass(frozen=True)
class ScaledGeneration:
    """Wind and PV generation after applying scenario capacities in GW."""

    timestamps_utc: tuple
    pv_gw: tuple[float, ...]
    wind_onshore_gw: tuple[float, ...]
    wind_offshore_gw: tuple[float, ...]
    step_hours: float

    @property
    def renewable_gw(self) -> tuple[float, ...]:
        """Return the sum of the three independently scaled technologies."""
        return tuple(
            pv + onshore + offshore
            for pv, onshore, offshore in zip(
                self.pv_gw,
                self.wind_onshore_gw,
                self.wind_offshore_gw,
                strict=True,
            )
        )


def scale_generation(
    reference: ReferenceYear,
    *,
    pv_gw: float,
    wind_onshore_gw: float,
    wind_offshore_gw: float,
) -> ScaledGeneration:
    """Scale each observed generation profile to a scenario capacity."""
    scenario_capacities = {
        "pv": pv_gw,
        "wind_onshore": wind_onshore_gw,
        "wind_offshore": wind_offshore_gw,
    }
    for technology, capacity in scenario_capacities.items():
        if not math.isfinite(capacity) or capacity < 0:
            raise ValueError(f"Invalid scenario capacity for {technology}: {capacity}")
        reference_capacity = reference.reference_capacity_gw.get(technology)
        if reference_capacity is None or not math.isfinite(reference_capacity):
            raise ReferenceDataError(f"Missing reference capacity for {technology}")
        if reference_capacity <= 0:
            raise ReferenceDataError(
                f"Reference capacity must be positive for {technology}"
            )

    def scaled(values: tuple[float, ...], technology: str) -> tuple[float, ...]:
        factor = (
            scenario_capacities[technology]
            / reference.reference_capacity_gw[technology]
        )
        return tuple(value * factor for value in values)

    return ScaledGeneration(
        timestamps_utc=reference.timestamps_utc,
        pv_gw=scaled(reference.pv_gw, "pv"),
        wind_onshore_gw=scaled(reference.wind_onshore_gw, "wind_onshore"),
        wind_offshore_gw=scaled(reference.wind_offshore_gw, "wind_offshore"),
        step_hours=reference.step_hours,
    )
