"""Tests for v0.17.0: PAC (heat pump) decision + extended winter duration curve.

- The duration curve gained 5°C and 10°C anchors so the sub-15°C
  (active-wintering) range is configurable instead of clamped.
- `_decide_pac` mirrors the electrolyzer decision: PAC only inside the
  pump window, cut before the pump stops (pre_stop), guarded by a min
  water temperature.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from custom_components.pool_pump.const import (
    CONF_PAC_SWITCH,
    CONF_PUMP_SWITCH,
    CONF_TEMPERATURE_MODE,
    CONF_TEMPERATURE_SENSOR,
    MODE_AUTO,
    PAC_BLOCK_NONE,
    PAC_BLOCK_PUMP_OFF,
    PAC_BLOCK_TEMP_LOW,
)
from custom_components.pool_pump.coordinator import (
    PoolPumpCoordinator,
    PoolPumpData,
    Run,
    compute_duration,
    compute_duration_from_curve,
)

# Default 7-anchor curve shipped in v0.17.0 (5/10°C added).
CURVE = [
    (5.0, 1.7),
    (10.0, 3.3),
    (15.0, 7.5),
    (20.0, 10.0),
    (25.0, 12.5),
    (30.0, 15.0),
    (35.0, 17.5),
]


# ---- Duration curve (pure functions) ----

def test_curve_interpolates_in_cold_range():
    # 7.5°C is halfway between 5°C (1.7h) and 10°C (3.3h) → 2.5h.
    assert compute_duration_from_curve(7.5, CURVE) == pytest.approx(2.5)


def test_curve_clamps_below_lowest_anchor():
    # Below 5°C reuses the 5°C anchor (no extrapolation to negative hours).
    assert compute_duration_from_curve(2.0, CURVE) == pytest.approx(1.7)


def test_curve_matches_anchor_values():
    assert compute_duration_from_curve(15.0, CURVE) == pytest.approx(7.5)
    assert compute_duration_from_curve(35.0, CURVE) == pytest.approx(17.5)


def test_compute_duration_curve_pulls_down_in_cold_water():
    # The whole point of the feature: cold water yields a short duration
    # via the curve (old behaviour clamped at the 15°C value = 7.5h).
    dur, heatwave = compute_duration(
        8.0,
        min_hours=0,
        max_hours=24,
        forecast_value=None,
        heatwave_threshold=99.0,
        curve_anchors=CURVE,
    )
    # 8°C between 5(1.7) and 10(3.3): 1.7 + 0.6*(3.3-1.7) = 2.66h.
    assert dur == pytest.approx(2.66)
    assert heatwave is False
    assert dur < 7.5  # strictly below the old 15°C floor


# ---- PAC decision ----

def _coord(hass, *, pump_state: str = "on") -> PoolPumpCoordinator:
    hass.states.async_set("switch.fake_pump", pump_state)
    hass.states.async_set("switch.fake_pac", "off")
    hass.states.async_set(
        "sensor.fake_water", "24.0",
        {"unit_of_measurement": "°C", "device_class": "temperature"},
    )
    options = {
        CONF_PUMP_SWITCH: "switch.fake_pump",
        CONF_PAC_SWITCH: "switch.fake_pac",
        CONF_TEMPERATURE_MODE: "water",
        CONF_TEMPERATURE_SENSOR: "sensor.fake_water",
    }
    coord = PoolPumpCoordinator(hass, entry_id="pac_test", options=options)
    coord.mode = MODE_AUTO
    return coord


@pytest.mark.asyncio
async def test_pac_off_when_pump_off(hass):
    coord = _coord(hass, pump_state="off")
    now = datetime.now(timezone.utc)
    data = PoolPumpData(temperature_used=24.0)
    target, block = coord._decide_pac(
        now, data, post_start=120, pre_stop=180, pac_min=10.0, short_cycle_threshold=30
    )
    assert target is False
    assert block == PAC_BLOCK_PUMP_OFF


@pytest.mark.asyncio
async def test_pac_off_when_water_too_cold(hass):
    coord = _coord(hass, pump_state="on")
    now = datetime.now(timezone.utc)
    data = PoolPumpData(temperature_used=8.0)  # below pac_min=10
    target, block = coord._decide_pac(
        now, data, post_start=120, pre_stop=180, pac_min=10.0, short_cycle_threshold=30
    )
    assert target is False
    assert block == PAC_BLOCK_TEMP_LOW


@pytest.mark.asyncio
async def test_pac_on_inside_window(hass):
    coord = _coord(hass, pump_state="on")
    now = datetime.now(timezone.utc)
    # Pump has been on continuously longer than post_start → margin satisfied.
    coord._pump_continuous_on_since = now - timedelta(seconds=300)
    data = PoolPumpData(
        temperature_used=24.0,
        runs=[Run(start=now - timedelta(hours=1), end=now + timedelta(hours=1))],
    )
    target, block = coord._decide_pac(
        now, data, post_start=120, pre_stop=180, pac_min=10.0, short_cycle_threshold=30
    )
    assert target is True
    assert block == PAC_BLOCK_NONE


@pytest.mark.asyncio
async def test_pac_off_in_pre_stop_margin(hass):
    """Within pre_stop seconds of the pump stop, the PAC is cut early."""
    coord = _coord(hass, pump_state="on")
    now = datetime.now(timezone.utc)
    coord._pump_continuous_on_since = now - timedelta(seconds=3600)
    # Run ends in 60s but pre_stop is 180s → now is inside the pre-stop margin.
    data = PoolPumpData(
        temperature_used=24.0,
        runs=[Run(start=now - timedelta(hours=2), end=now + timedelta(seconds=60))],
    )
    target, _block = coord._decide_pac(
        now, data, post_start=120, pre_stop=180, pac_min=10.0, short_cycle_threshold=30
    )
    assert target is False
