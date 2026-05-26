"""Pool Pump Manager binary sensors."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_ELECTROLYZER_SWITCH, DOMAIN
from .coordinator import PoolPumpCoordinator
from .entity import PoolPumpEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: PoolPumpCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[BinarySensorEntity] = [
        PumpTargetSensor(coordinator, entry),
        HeatwaveSensor(coordinator, entry),
    ]
    if coordinator.options.get(CONF_ELECTROLYZER_SWITCH):
        entities.append(ElectrolyzerTargetSensor(coordinator, entry))
    async_add_entities(entities)


class PumpTargetSensor(PoolPumpEntity, BinarySensorEntity):
    _attr_translation_key = "pump_target"
    _attr_device_class = BinarySensorDeviceClass.RUNNING
    _attr_icon = "mdi:water-pump"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{self._unique_prefix}_pump_target"

    @property
    def is_on(self) -> bool:
        d = self.coordinator.data
        return bool(d and d.pump_should_be_on)


class ElectrolyzerTargetSensor(PoolPumpEntity, BinarySensorEntity):
    _attr_translation_key = "electrolyzer_target"
    _attr_device_class = BinarySensorDeviceClass.RUNNING
    _attr_icon = "mdi:flash"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{self._unique_prefix}_electrolyzer_target"

    @property
    def is_on(self) -> bool:
        d = self.coordinator.data
        return bool(d and d.electrolyzer_should_be_on)


class HeatwaveSensor(PoolPumpEntity, BinarySensorEntity):
    _attr_translation_key = "heatwave"
    _attr_icon = "mdi:weather-sunny-alert"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{self._unique_prefix}_heatwave"

    @property
    def is_on(self) -> bool:
        d = self.coordinator.data
        return bool(d and d.heatwave_active)
