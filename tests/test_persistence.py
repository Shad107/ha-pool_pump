"""Verify that accumulated state survives a HA restart in water mode.

These are unit tests on the coordinator: we skip the full
`async_setup_entry` path (which pulls in the `frontend` / `http`
dependencies, not trivially available in CI) and instantiate the
coordinator directly. The persistence logic doesn't depend on the
platform machinery, so this is enough to catch the v0.12.2 regression
where `_async_save_model` stopped being called in water-probe mode.
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


def _build_coordinator(hass):
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
    return PoolPumpCoordinator(hass, entry_id="test_entry", options=options)


@pytest.mark.asyncio
async def test_save_called_in_water_mode(hass, monkeypatch):
    """Regression for v0.12.2 — save must fire on every tick, water mode included."""
    coord = _build_coordinator(hass)
    await coord.async_load_persisted()

    call_count = 0
    original = coord._async_save_model

    async def counting_save():
        nonlocal call_count
        call_count += 1
        await original()

    monkeypatch.setattr(coord, "_async_save_model", counting_save)
    await coord.async_refresh()
    await hass.async_block_till_done()

    assert call_count >= 1, (
        "save was never called in water mode — v0.12.2 regression"
    )


@pytest.mark.asyncio
async def test_mode_time_today_persists(hass):
    """Time accumulated in a mode must end up in the Store, then load back."""
    coord = _build_coordinator(hass)
    await coord.async_load_persisted()

    # Pretend the previous tick was 90 s ago and we were in MODE_ON.
    now = datetime.now(timezone.utc)
    coord.mode = MODE_ON
    coord._last_mode_tick = now - timedelta(seconds=90)
    coord._mode_time_date = now.date().isoformat()
    coord._mode_time_today = {}

    await coord.async_refresh()
    await hass.async_block_till_done()

    accumulated = coord._mode_time_today.get(MODE_ON, 0.0)
    assert accumulated > 0

    snapshot = await coord._store.async_load()
    assert snapshot is not None, "Store empty — save didn't reach disk"
    assert snapshot.get("mode_time_today", {}).get(MODE_ON, 0.0) == pytest.approx(
        accumulated
    )

    # Build a fresh coordinator and load — the value must come back.
    coord2 = _build_coordinator(hass)
    await coord2.async_load_persisted()
    restored = coord2._mode_time_today.get(MODE_ON, 0.0)
    assert restored == pytest.approx(accumulated), (
        f"mode_time_today not restored: expected {accumulated}, got {restored}"
    )
