"""Shared base entity for Pool Pump Manager."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, NAME, VERSION
from .coordinator import PoolPumpCoordinator


class PoolPumpEntity(CoordinatorEntity[PoolPumpCoordinator]):
    """Base entity with shared device info."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: PoolPumpCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=NAME,
            manufacturer="Shad107",
            model="Pool Pump Manager",
            sw_version=VERSION,
            configuration_url="https://github.com/Shad107/ha-pool_pump",
        )

    @property
    def _unique_prefix(self) -> str:
        return f"{self._entry.entry_id}"
