"""Composition of demand, generation, storage and gas dispatch."""

from __future__ import annotations

import math
from dataclasses import dataclass

from .battery import BatteryDispatch, dispatch_battery
from .demand import ScaledDemand, scale_demand
from .generation import ScaledGeneration, scale_generation
from .reference import ReferenceYear


@dataclass(frozen=True)
class Scenario:
    """Installed capacities and dispatch assumptions for one scenario."""

    name: str
    pv_gw: float
    wind_onshore_gw: float
    wind_offshore_gw: float
    battery_power_gw: float
    annual_demand_twh: float = 1100.0
    battery_duration_hours: float = 4.0
    initial_soc_gwh: float | None = None
    charge_efficiency: float = 0.9
    discharge_efficiency: float = 0.9


@dataclass(frozen=True)
class ScenarioResult:
    """Observable outputs of a complete scenario dispatch."""

    scenario: Scenario
    generation: ScaledGeneration
    demand: ScaledDemand
    battery: BatteryDispatch
    residual_load_gw: tuple[float, ...]
    gas_residual_gw: tuple[float, ...]
    gas_power_gw: float
    gas_work_twh: float
    curtailment_twh: float
    unserved_load_twh: float


def run_scenario(reference: ReferenceYear, scenario: Scenario) -> ScenarioResult:
    """Run one scenario with gas covering all residual positive load."""
    generation = scale_generation(
        reference,
        pv_gw=scenario.pv_gw,
        wind_onshore_gw=scenario.wind_onshore_gw,
        wind_offshore_gw=scenario.wind_offshore_gw,
    )
    demand = scale_demand(
        reference.load_gw,
        annual_twh=scenario.annual_demand_twh,
        step_hours=reference.step_hours,
    )
    residual = tuple(
        load - produced
        for load, produced in zip(demand.load_gw, generation.renewable_gw, strict=True)
    )
    battery = dispatch_battery(
        residual,
        power_gw=scenario.battery_power_gw,
        duration_hours=scenario.battery_duration_hours,
        initial_soc_gwh=scenario.initial_soc_gwh,
        charge_efficiency=scenario.charge_efficiency,
        discharge_efficiency=scenario.discharge_efficiency,
        step_hours=reference.step_hours,
    )
    gas_residual = battery.remaining_residual_gw
    return ScenarioResult(
        scenario=scenario,
        generation=generation,
        demand=demand,
        battery=battery,
        residual_load_gw=residual,
        gas_residual_gw=gas_residual,
        gas_power_gw=max(gas_residual),
        gas_work_twh=math.fsum(gas_residual) * reference.step_hours / 1000,
        curtailment_twh=(
            math.fsum(battery.curtailment_gw) * reference.step_hours / 1000
        ),
        unserved_load_twh=0.0,
    )
