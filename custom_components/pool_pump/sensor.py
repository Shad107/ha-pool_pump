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
    ROUTINES,
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
        attrs = {
            "mode": d.mode,
            "heatwave_active": d.heatwave_active,
            "forecast_value": d.forecast_value,
            "temperature_mode": d.temperature_mode,
            "pump_available": d.pump_available,
            # v0.14 UI flags the card reads to decide what to render
            "has_electrolyzer": d.has_electrolyzer,
            "show_illustration": d.show_illustration,
            "chemistry_enabled": d.chemistry_enabled,
            "air_temperature_raw": d.air_temperature_raw,
            "air_temperature_smoothed": d.air_temperature_smoothed,
            "solar_power_w": d.solar_power_w,
            "solar_peak_w": d.solar_peak_w,
            "solar_fraction": round(d.solar_fraction, 3) if d.solar_fraction else 0,
            "solar_coefficient_effective": d.solar_coefficient_effective,
            "tau_hours_effective": round(d.tau_hours_effective, 2) if d.tau_hours_effective else 0,
            "water_modeled_raw": (
                round(d.water_modeled_raw, 2)
                if d.water_modeled_raw is not None
                else None
            ),
            "learned_temperature_offset": round(d.learned_temperature_offset, 3),
            "calibration_points": d.calibration_points,
            "forecast_temperature_max_24h": d.forecast_temperature_max_24h,
            "forecast_condition": d.forecast_condition,
            "forecast_preheat_active": d.forecast_preheat_active,
            "maintenance_active": d.maintenance_active,
            "maintenance_ends_at": (
                d.maintenance_ends_at.isoformat() if d.maintenance_ends_at else None
            ),
            "chemistry": [
                {
                    "key": r.key, "label": r.label, "unit": r.unit,
                    "value": r.value, "target": r.target,
                    "target_low": r.target_low, "target_high": r.target_high,
                    "status": r.status,
                }
                for r in d.chemistry
            ],
            "mode_time_today": d.mode_time_today,
            "active_routine": d.active_routine,
            "available_routines": [
                {
                    "key": r[0], "label": r[1], "icon": r[2],
                    "mode": r[3], "default_min": r[4],
                    "smart": bool(r[5]), "favorite": r[6],
                }
                for r in ROUTINES
            ],
            "chemistry_recommendations": [
                {
                    "issue_key": r.issue_key, "severity": r.severity,
                    "title": r.title, "product": r.product,
                    "dose_g": r.dose_g, "dose_ml": r.dose_ml,
                    "pump_action": r.pump_action,
                    "pump_duration_min": r.pump_duration_min,
                    "notes": r.notes,
                }
                for r in d.chemistry_recommendations
            ],
            "runs": [
                {"start": r.start.isoformat(), "end": r.end.isoformat()}
                for r in d.runs
            ],
        }
        # Hide cell-only fields when no electrolyzer is configured —
        # avoids polluting the attribute panel and signals to the card
        # to drop the related UI.
        if d.has_electrolyzer:
            attrs["electrolyzer_block_reason"] = d.electrolyzer_block_reason
            attrs["electrolyzer_available"] = d.electrolyzer_available
        if not d.chemistry_enabled:
            attrs.pop("chemistry", None)
            attrs.pop("chemistry_recommendations", None)
        return attrs


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
            "image_url": d.pool_image_url,
            "bundled_url": d.pool_bundled_url,
            "has_backwash": d.has_backwash,
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
