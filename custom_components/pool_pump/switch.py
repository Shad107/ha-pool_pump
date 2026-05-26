"""Pool Pump Manager — switch entities (electrolyzer enable, etc.)."""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import CONF_ELECTROLYZER_SWITCH, DOMAIN
from .coordinator import PoolPumpCoordinator
from .entity import PoolPumpEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: PoolPumpCoordinator = hass.data[DOMAIN][entry.entry_id]
    opts = {**entry.data, **entry.options}
    entities: list[SwitchEntity] = []
    if opts.get(CONF_ELECTROLYZER_SWITCH):
        entities.append(ElectrolyzerEnabledSwitch(coordinator, entry))
    if entities:
        async_add_entities(entities)


class ElectrolyzerEnabledSwitch(PoolPumpEntity, SwitchEntity, RestoreEntity):
    """User-controlled enable/disable for the electrolyzer.

    Off pendant un chlore choc, hivernage manuel ou maintenance cellule.
    Indépendant du mode pompe — la pompe continue selon son mode propre
    (Auto/On/Off).
    """

    _attr_translation_key = "electrolyzer_enabled"
    _attr_icon = "mdi:electric-switch"

    def __init__(self, coordinator: PoolPumpCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{self._unique_prefix}_electrolyzer_enabled"

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        # Storage in the coordinator is the source of truth; RestoreEntity
        # only patches if storage somehow returned the default True but
        # the user's last state was explicitly off.
        last = await self.async_get_last_state()
        if (
            last is not None
            and last.state == "off"
            and self.coordinator.electrolyzer_enabled
        ):
            self.coordinator.set_electrolyzer_enabled(False)

    @property
    def is_on(self) -> bool:
        return self.coordinator.electrolyzer_enabled

    async def async_turn_on(self, **_) -> None:
        self.coordinator.set_electrolyzer_enabled(True)
        self.async_write_ha_state()

    async def async_turn_off(self, **_) -> None:
        self.coordinator.set_electrolyzer_enabled(False)
        self.async_write_ha_state()
