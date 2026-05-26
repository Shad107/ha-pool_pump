"""Pool Pump Manager sensors."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import PoolPumpCoordinator
from .entity import PoolPumpEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: PoolPumpCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            StartTimeSensor(coordinator, entry),
            EndTimeSensor(coordinator, entry),
            DurationSensor(coordinator, entry),
            TemperatureUsedSensor(coordinator, entry),
            StatusSensor(coordinator, entry),
        ]
    )


class StartTimeSensor(PoolPumpEntity, SensorEntity):
    _attr_translation_key = "start_time"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:clock-start"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{self._unique_prefix}_start_time"

    @property
    def native_value(self):
        return self.coordinator.data.next_start if self.coordinator.data else None


class EndTimeSensor(PoolPumpEntity, SensorEntity):
    _attr_translation_key = "end_time"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:clock-end"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{self._unique_prefix}_end_time"

    @property
    def native_value(self):
        return self.coordinator.data.next_end if self.coordinator.data else None


class DurationSensor(PoolPumpEntity, SensorEntity):
    _attr_translation_key = "duration"
    _attr_native_unit_of_measurement = UnitOfTime.HOURS
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:timer-sand"
    _attr_suggested_display_precision = 2

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{self._unique_prefix}_duration"

    @property
    def native_value(self):
        d = self.coordinator.data
        return round(d.duration_hours, 2) if d else None


class TemperatureUsedSensor(PoolPumpEntity, SensorEntity):
    _attr_translation_key = "temperature_used"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{self._unique_prefix}_temperature_used"

    @property
    def native_value(self):
        d = self.coordinator.data
        return d.temperature_used if d else None


class StatusSensor(PoolPumpEntity, SensorEntity):
    _attr_translation_key = "status"
    _attr_icon = "mdi:water-pump"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{self._unique_prefix}_status"

    @property
    def native_value(self):
        d = self.coordinator.data
        return d.reason if d else None

    @property
    def extra_state_attributes(self):
        d = self.coordinator.data
        if not d:
            return None
        return {
            "mode": d.mode,
            "heatwave_active": d.heatwave_active,
            "forecast_value": d.forecast_value,
            "runs": [
                {"start": r.start.isoformat(), "end": r.end.isoformat()}
                for r in d.runs
            ],
        }
