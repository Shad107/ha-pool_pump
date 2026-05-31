"""Pytest fixtures for the pool_pump test suite.

We use pytest-homeassistant-custom-component which provides a real
HomeAssistant instance and the common fixtures (hass, mock_config_entry,
…). The `enable_custom_integrations` autouse fixture lets HA pick up
the custom_components/pool_pump module from the repo.
"""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Make `custom_components/pool_pump` discoverable by HA in every test."""
    yield


@pytest.fixture
def base_config() -> dict:
    """Minimal config entry data for the integration.

    Points at a fake switch (no real device needed) and a water-mode
    temperature sensor — that combination exercises the path where the
    persistence bug from v0.12.2 was hiding.
    """
    return {
        "pump_switch": "switch.fake_pump",
        "temperature_mode": "water",
        "temperature_sensor": "sensor.fake_water_probe",
    }
