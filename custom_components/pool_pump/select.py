"""Pool Pump Manager mode selector (Auto/On/Off)."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN, MODE_AUTO, MODE_OPTIONS
from .coordinator import PoolPumpCoordinator
from .entity import PoolPumpEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: PoolPumpCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ModeSelect(coordinator, entry)])


class ModeSelect(PoolPumpEntity, SelectEntity, RestoreEntity):
    _attr_translation_key = "mode"
    _attr_options = list(MODE_OPTIONS)
    _attr_icon = "mdi:tune-vertical"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{self._unique_prefix}_mode"

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last and last.state in MODE_OPTIONS:
            self.coordinator.mode = last.state

    @property
    def current_option(self) -> str:
        return self.coordinator.mode or MODE_AUTO

    async def async_select_option(self, option: str) -> None:
        self.coordinator.set_mode(option)
        self.async_write_ha_state()
