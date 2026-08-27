"""Behavioral tests for demand scaling."""

from __future__ import annotations

import pytest

from strommodell.demand import scale_demand


def test_scale_demand_preserves_shape_and_hits_annual_target() -> None:
    demand = scale_demand((1.0, 2.0), annual_twh=0.003, step_hours=1.0)

    assert demand.load_gw == (1.0, 2.0)
    assert demand.annual_twh == pytest.approx(0.003)
    assert demand.mean_gw == pytest.approx(1.5)
    assert demand.peak_gw == pytest.approx(2.0)
