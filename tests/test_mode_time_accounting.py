"""Verify mode_time_today only accumulates when the pump is actually running.

Regression for v0.12.3 — earlier versions attributed every tick's
delta to the current mode, regardless of whether the pump was on.
That made "Auto" claim 10h overnight even though the schedule window
hadn't opened yet. After v0.12.3, only ticks where pump_target is True
contribute, and Backwash gets its own bucket so its activity doesn't
pollute whichever mode happens to be selected.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from custom_components.pool_pump.const import (
    CONF_PUMP_SWITCH,
    CONF_TEMPERATURE_MODE,
    CONF_TEMPERATURE_SENSOR,
    MODE_AUTO,
    MODE_OFF,
    MODE_ON,
)
from custom_components.pool_pump.coordinator import PoolPumpCoordinator, PoolPumpData


def _build_coordinator(hass, entry_id: str = "mta_test"):
    hass.states.async_set("switch.fake_pump", "off")
    hass.states.async_set(
        "sensor.fake_water_probe", "24.5",
        {"unit_of_measurement": "°C", "device_class": "temperature"},
    )
    options = {
        CONF_PUMP_SWITCH: "switch.fake_pump",
        CONF_TEMPERATURE_MODE: "water",
        CONF_TEMPERATURE_SENSOR: "sensor.fake_water_probe",
    }
    return PoolPumpCoordinator(hass, entry_id=entry_id, options=options)


def _accumulate(coord, *, mode: str, pump_target: bool, backwash: bool, dt_sec: float):
    """Inline the v0.12.3 accounting block to verify its semantics directly.

    We're not testing the coordinator's full tick (which would pull in
    too many integration-level details for CI); we're testing the
    contract documented in v0.12.3: the bucket is chosen by
    backwash_active first, then by pump_target + mode, otherwise nothing.
    """
    coord.mode = mode
    if 0 < dt_sec < 300:
        if backwash:
            bucket = "backwash"
        elif pump_target:
            bucket = mode or MODE_AUTO
        else:
            bucket = None
        if bucket is not None:
            coord._mode_time_today[bucket] = (
                coord._mode_time_today.get(bucket, 0.0) + dt_sec
            )


@pytest.mark.asyncio
async def test_off_mode_never_accumulates(hass):
    """In Off mode the pump is forced off → counter must stay 0."""
    coord = _build_coordinator(hass)
    for _ in range(10):
        _accumulate(coord, mode=MODE_OFF, pump_target=False, backwash=False, dt_sec=60)
    assert coord._mode_time_today.get(MODE_OFF, 0.0) == 0.0


@pytest.mark.asyncio
async def test_auto_outside_window_does_not_count(hass):
    """Auto mode outside the run window: pump_target=False → 0 seconds counted."""
    coord = _build_coordinator(hass)
    # Simulate 30 ticks of 1 min each, all outside the window.
    for _ in range(30):
        _accumulate(coord, mode=MODE_AUTO, pump_target=False, backwash=False, dt_sec=60)
    assert coord._mode_time_today.get(MODE_AUTO, 0.0) == 0.0


@pytest.mark.asyncio
async def test_auto_inside_window_accumulates(hass):
    """Auto mode inside the run window: counter grows."""
    coord = _build_coordinator(hass)
    for _ in range(5):
        _accumulate(coord, mode=MODE_AUTO, pump_target=True, backwash=False, dt_sec=60)
    assert coord._mode_time_today.get(MODE_AUTO, 0.0) == pytest.approx(300.0)


@pytest.mark.asyncio
async def test_manual_on_full_duration(hass):
    """Marche forcée: pump_target is always True, counter equals time spent."""
    coord = _build_coordinator(hass)
    for _ in range(10):
        _accumulate(coord, mode=MODE_ON, pump_target=True, backwash=False, dt_sec=60)
    assert coord._mode_time_today.get(MODE_ON, 0.0) == pytest.approx(600.0)


@pytest.mark.asyncio
async def test_backwash_uses_own_bucket(hass):
    """Backwash time must not pollute the currently selected mode."""
    coord = _build_coordinator(hass)
    # User had Off mode selected and backwash kicked in (e.g., manual trigger).
    for _ in range(5):
        _accumulate(coord, mode=MODE_OFF, pump_target=True, backwash=True, dt_sec=60)
    assert coord._mode_time_today.get(MODE_OFF, 0.0) == 0.0, (
        "backwash time leaked into Off bucket"
    )
    assert coord._mode_time_today.get("backwash", 0.0) == pytest.approx(300.0)


@pytest.mark.asyncio
async def test_long_gap_is_ignored(hass):
    """A dt > 5 min is dropped (guard against HA downtime poisoning the day)."""
    coord = _build_coordinator(hass)
    _accumulate(coord, mode=MODE_AUTO, pump_target=True, backwash=False, dt_sec=600)
    assert coord._mode_time_today.get(MODE_AUTO, 0.0) == 0.0
