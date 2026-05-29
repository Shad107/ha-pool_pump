"""Pool Pump Manager number entities for manual chemistry readings.

Each chemistry parameter (pH, free chlorine, TAC, etc.) is exposed as a
NumberEntity the user can set via the UI, automation, or our card popup.
If the user has an auto-measuring device, they can point the integration
at that sensor in the options; the number entity remains available as a
manual override / fallback.

Setting the value via HA's standard `number.set_value` service updates
the entity, persists to storage, records to HA recorder for history,
and triggers a coordinator refresh so the diagnosis recomputes.
"""
from __future__ import annotations

import logging

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import CHEM_PARAMS, DOMAIN
from .coordinator import PoolPumpCoordinator
from .entity import PoolPumpEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: PoolPumpCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [
        ChemistryNumber(coordinator, entry, *params) for params in CHEM_PARAMS
    ]
    async_add_entities(entities)


class ChemistryNumber(PoolPumpEntity, NumberEntity, RestoreEntity):
    """A user-editable numeric chemistry reading (pH, chlorine, etc.).

    Disabled by default for the less-common parameters (TH, CYA, salt, ORP)
    so the entity list stays clean for users who don't measure them.
    """

    _attr_mode = NumberMode.BOX

    def __init__(
        self,
        coordinator: PoolPumpCoordinator,
        entry: ConfigEntry,
        key: str,
        label: str,
        unit: str,
        vmin: float,
        vmax: float,
        step: float,
        target: float,
        low: float,
        high: float,
        enabled_default: bool,
    ) -> None:
        super().__init__(coordinator, entry)
        self._key = key
        self._attr_unique_id = f"{self._unique_prefix}_chem_{key}"
        self._attr_translation_key = f"chem_{key}"
        self._attr_native_min_value = vmin
        self._attr_native_max_value = vmax
        self._attr_native_step = step
        self._attr_native_unit_of_measurement = unit
        self._attr_entity_registry_enabled_default = enabled_default
        self._attr_icon = {
            "ph": "mdi:ph",
            "free_chlorine": "mdi:chemical-weapon",
            "total_chlorine": "mdi:chemical-weapon",
            "tac": "mdi:flask",
            "th": "mdi:water-percent",
            "cya": "mdi:shield-sun",
            "salt": "mdi:shaker-outline",
            "orp": "mdi:flash",
        }.get(key, "mdi:chemical-weapon")
        self._value: float | None = None
        self._default_target = target

    async def async_added_to_hass(self) -> None:
        """Restore the last value from HA's recorder after restart."""
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state and last_state.state not in (None, "unknown", "unavailable"):
            try:
                self._value = float(last_state.state)
            except (TypeError, ValueError):
                self._value = None
        # Register ourselves with the coordinator so it can read us.
        self.coordinator.register_chemistry_number(self._key, self)

    @property
    def native_value(self) -> float | None:
        return self._value

    async def async_set_native_value(self, value: float) -> None:
        """User updated the value — store it and refresh diagnosis."""
        self._value = value
        self.async_write_ha_state()
        await self.coordinator.async_request_refresh()
