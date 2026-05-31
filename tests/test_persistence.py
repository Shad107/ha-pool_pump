"""Verify that accumulated state survives a HA restart in water mode.

Bug repro for v0.12.2: when the integration was configured in water-probe
mode (temperature_mode == "water"), `_async_save_model` was only called
inside the air-model branch, so the Store never received an update. At
the next restart, `mode_time_today`, energy counters, cell hours, and
all calibration history were lost.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.pool_pump.const import (
    DOMAIN,
    MODE_AUTO,
    MODE_ON,
)


async def _setup_entry(hass, base_config):
    """Helper: register the integration with the given config and wait for setup."""
    entry = MockConfigEntry(domain=DOMAIN, data=base_config, options={})
    entry.add_to_hass(hass)
    # Provide the fake source entities the coordinator reads.
    hass.states.async_set("switch.fake_pump", "off")
    hass.states.async_set(
        "sensor.fake_water_probe", "24.5",
        {"unit_of_measurement": "°C", "device_class": "temperature"},
    )
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


@pytest.mark.asyncio
async def test_save_called_in_water_mode(hass, base_config, monkeypatch):
    """`_async_save_model` must be called at least once per coordinator tick.

    Regression for v0.12.2 — in water mode, the air-model branch is
    skipped, so the save call placed there was dead code from the
    perspective of users with a real probe.
    """
    entry = await _setup_entry(hass, base_config)
    coord = hass.data[DOMAIN][entry.entry_id]

    save_count = 0

    original_save = coord._async_save_model

    async def counting_save():
        nonlocal save_count
        save_count += 1
        await original_save()

    monkeypatch.setattr(coord, "_async_save_model", counting_save)

    # Trigger a refresh tick.
    await coord.async_refresh()
    await hass.async_block_till_done()

    assert save_count >= 1, (
        "save was never called in water mode — persistence bug back"
    )


@pytest.mark.asyncio
async def test_mode_time_today_roundtrip(hass, base_config):
    """Accumulate time in a mode, save, reload — value must be preserved."""
    entry = await _setup_entry(hass, base_config)
    coord = hass.data[DOMAIN][entry.entry_id]

    # Simulate a previous tick 90 seconds ago in MODE_ON.
    coord.mode = MODE_ON
    coord._last_mode_tick = datetime.now(timezone.utc) - timedelta(seconds=90)
    coord._mode_time_date = datetime.now(timezone.utc).date().isoformat()
    coord._mode_time_today = {}

    await coord.async_refresh()
    await hass.async_block_till_done()

    accumulated = coord._mode_time_today.get(MODE_ON, 0.0)
    assert accumulated > 0, "mode_time_today did not accumulate at all"

    # Now force a fresh load from Store and check the value persists.
    stored_snapshot = await coord._store.async_load()
    assert stored_snapshot is not None, "Store returned None — save didn't happen"
    assert stored_snapshot.get("mode_time_today", {}).get(MODE_ON, 0.0) == pytest.approx(
        accumulated
    ), "mode_time_today not in saved snapshot"
