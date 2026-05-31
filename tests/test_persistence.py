"""Verify that the coordinator's save/load round-trips correctly.

These tests sidestep the full `_async_update_data` tick (which depends
on many integration-level details) and directly exercise the
persistence layer that the v0.12.2 bug touched.

Why this matters: the v0.12.2 bug was that `_async_save_model` was
called inside the `air_model` branch only. Even though we can't easily
replay a tick in CI, we can at least verify that:
  1. `_async_save_model` produces a dict the Store accepts
  2. `async_load_persisted` reads that dict back into the same shape

If either of those silently dropped a field (which is the v0.12.0
class of bug), this test fails.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from custom_components.pool_pump.const import (
    CONF_PUMP_SWITCH,
    CONF_TEMPERATURE_MODE,
    CONF_TEMPERATURE_SENSOR,
    MODE_AUTO,
    MODE_ON,
)
from custom_components.pool_pump.coordinator import PoolPumpCoordinator


def _build_coordinator(hass, entry_id: str = "test_entry"):
    """Build a coordinator pointing at fake source entities."""
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


@pytest.mark.asyncio
async def test_save_produces_non_empty_snapshot(hass):
    """`_async_save_model` must write a dict containing the new v0.11.2 keys."""
    coord = _build_coordinator(hass)
    coord._mode_time_today = {MODE_ON: 42.0}
    coord._mode_time_date = "2026-05-31"
    coord._last_mode_tick = datetime.now(timezone.utc)

    await coord._async_save_model()

    snapshot = await coord._store.async_load()
    assert snapshot is not None
    # The v0.11.2 keys must round-trip — earlier they were silently
    # dropped if the air-model branch was skipped.
    assert "mode_time_today" in snapshot
    assert snapshot["mode_time_today"] == {MODE_ON: 42.0}
    assert snapshot.get("mode_time_date") == "2026-05-31"


@pytest.mark.asyncio
async def test_mode_time_today_roundtrip(hass):
    """Save in one coordinator, load in a fresh one — values must come back."""
    src = _build_coordinator(hass, entry_id="roundtrip_test")
    src._mode_time_today = {MODE_ON: 295.2, MODE_AUTO: 14400.0}
    src._mode_time_date = "2026-05-31"
    src._last_mode_tick = datetime.now(timezone.utc)
    src._learned_offset = -0.4
    src._cell_hours_total = 178.5
    src._energy_today_kwh = 4.55
    await src._async_save_model()

    dst = _build_coordinator(hass, entry_id="roundtrip_test")
    await dst.async_load_persisted()

    assert dst._mode_time_today.get(MODE_ON) == pytest.approx(295.2)
    assert dst._mode_time_today.get(MODE_AUTO) == pytest.approx(14400.0)
    assert dst._mode_time_date == "2026-05-31"
    assert dst._learned_offset == pytest.approx(-0.4)
    assert dst._cell_hours_total == pytest.approx(178.5)
    assert dst._energy_today_kwh == pytest.approx(4.55)


@pytest.mark.asyncio
async def test_calibrations_persist(hass):
    """Calibration history must survive a reload."""
    src = _build_coordinator(hass, entry_id="cal_test")
    now = datetime.now(timezone.utc)
    src._calibrations = [
        (now - timedelta(days=2), -0.3),
        (now - timedelta(days=1), -0.5),
    ]
    src._learned_offset = -0.4
    await src._async_save_model()

    dst = _build_coordinator(hass, entry_id="cal_test")
    await dst.async_load_persisted()

    assert len(dst._calibrations) == 2
    assert dst._calibrations[0][1] == pytest.approx(-0.3)
    assert dst._calibrations[1][1] == pytest.approx(-0.5)
