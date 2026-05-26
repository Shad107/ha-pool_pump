"""Pool Pump Manager sensors."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy, UnitOfPower, UnitOfTemperature, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_ELECTROLYZER_POWER_SENSOR,
    CONF_ELECTROLYZER_SWITCH,
    CONF_PUMP_POWER_SENSOR,
    DOMAIN,
)
from .coordinator import PoolPumpCoordinator
from .entity import PoolPumpEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: PoolPumpCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = [
        StartTimeSensor(coordinator, entry),
        EndTimeSensor(coordinator, entry),
        DurationSensor(coordinator, entry),
        TemperatureUsedSensor(coordinator, entry),
        StatusSensor(coordinator, entry),
        PoolGeometrySensor(coordinator, entry),
    ]
    # Power/energy entities only when at least one power sensor is configured.
    opts = {**entry.data, **entry.options}
    if opts.get(CONF_PUMP_POWER_SENSOR) or opts.get(CONF_ELECTROLYZER_POWER_SENSOR):
        entities.extend([
            CurrentPowerSensor(coordinator, entry),
            EnergyTodaySensor(coordinator, entry),
            EnergyTotalSensor(coordinator, entry),
        ])
    if opts.get(CONF_ELECTROLYZER_SWITCH):
        entities.append(CellHoursSensor(coordinator, entry))
    async_add_entities(entities)


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
            "electrolyzer_block_reason": d.electrolyzer_block_reason,
            "temperature_mode": d.temperature_mode,
            "pump_available": d.pump_available,
            "electrolyzer_available": d.electrolyzer_available,
            "air_temperature_raw": d.air_temperature_raw,
            "air_temperature_smoothed": d.air_temperature_smoothed,
            "solar_power_w": d.solar_power_w,
            "solar_peak_w": d.solar_peak_w,
            "solar_fraction": round(d.solar_fraction, 3) if d.solar_fraction else 0,
            "solar_coefficient_effective": d.solar_coefficient_effective,
            "tau_hours_effective": round(d.tau_hours_effective, 2) if d.tau_hours_effective else 0,
            "runs": [
                {"start": r.start.isoformat(), "end": r.end.isoformat()}
                for r in d.runs
            ],
        }


class PoolGeometrySensor(PoolPumpEntity, SensorEntity):
    """Exposes pool model name + geometry + inline SVG for the dashboard card.

    The state is the friendly model name, with the SVG and the geometry in
    attributes so a Lovelace markdown card can render the visual via
    ``{{ state_attr('sensor.pool_pump_manager_pool', 'svg') }}``.
    """

    _attr_translation_key = "pool"
    _attr_icon = "mdi:pool"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{self._unique_prefix}_pool"

    @property
    def native_value(self):
        d = self.coordinator.data
        if not d or not d.pool_preset:
            return "custom"
        return d.pool_preset["name"]

    @property
    def extra_state_attributes(self):
        d = self.coordinator.data
        if not d:
            return None
        preset = d.pool_preset or {}
        return {
            "shape": preset.get("shape"),
            "volume_m3": preset.get("volume_m3"),
            "surface_m2": preset.get("surface_m2"),
            "depth_m": preset.get("depth_m"),
            "manufacturer": preset.get("manufacturer"),
            "svg": d.pool_svg or "",
        }


class CurrentPowerSensor(PoolPumpEntity, SensorEntity):
    _attr_translation_key = "current_power"
    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:flash"
    _attr_suggested_display_precision = 0

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{self._unique_prefix}_current_power"

    @property
    def native_value(self):
        d = self.coordinator.data
        return d.total_power_w if d else None

    @property
    def extra_state_attributes(self):
        d = self.coordinator.data
        if not d:
            return None
        return {
            "pump_power_w": d.pump_power_w,
            "electrolyzer_power_w": d.electrolyzer_power_w,
        }


class EnergyTodaySensor(PoolPumpEntity, SensorEntity):
    _attr_translation_key = "energy_today"
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_icon = "mdi:lightning-bolt"
    _attr_suggested_display_precision = 2

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{self._unique_prefix}_energy_today"

    @property
    def native_value(self):
        d = self.coordinator.data
        return round(d.energy_today_kwh, 3) if d else None


class EnergyTotalSensor(PoolPumpEntity, SensorEntity):
    _attr_translation_key = "energy_total"
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_icon = "mdi:counter"
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{self._unique_prefix}_energy_total"

    @property
    def native_value(self):
        d = self.coordinator.data
        return round(d.energy_total_kwh, 2) if d else None


class CellHoursSensor(PoolPumpEntity, SensorEntity):
    _attr_translation_key = "cell_hours"
    _attr_native_unit_of_measurement = UnitOfTime.HOURS
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_icon = "mdi:counter"
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{self._unique_prefix}_cell_hours"

    @property
    def native_value(self):
        d = self.coordinator.data
        return round(d.cell_hours_total, 2) if d else None
