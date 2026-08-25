"""Config flow for Pool Pump Manager."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import (
    CONF_AUTOTUNE_ENABLED,
    CONF_BREAK_HOURS,
    CONF_CHEMISTRY_ENABLED,
    CONF_CUSTOM_POOL_DEPTH,
    CONF_CUSTOM_POOL_INGROUND,
    CONF_CUSTOM_POOL_LENGTH,
    CONF_CUSTOM_POOL_SHAPE,
    CONF_CUSTOM_POOL_WIDTH,
    CONF_DURATION_AT_5C,
    CONF_DURATION_AT_10C,
    CONF_DURATION_AT_15C,
    CONF_DURATION_AT_20C,
    CONF_DURATION_AT_25C,
    CONF_DURATION_AT_30C,
    CONF_DURATION_AT_35C,
    CONF_DURATION_CURVE_ENABLED,
    CONF_EARLIEST_START_HOUR,
    CONF_FILTRATION_MULTIPLIER,
    CONF_LATEST_END_HOUR,
    CONF_SHOW_ILLUSTRATION,
    CONF_WINTERIZATION_OVERRIDE,
    CONF_ELECTROLYZER_MAX_TEMP,
    CONF_ELECTROLYZER_MIN_TEMP,
    CONF_ELECTROLYZER_POST_START_DELAY,
    CONF_ELECTROLYZER_PRE_STOP_DELAY,
    CONF_ELECTROLYZER_SWITCH,
    CONF_PAC_MIN_TEMP,
    CONF_PAC_POST_START_DELAY,
    CONF_PAC_POWER_SENSOR,
    CONF_PAC_PRE_STOP_DELAY,
    CONF_PAC_SWITCH,
    CONF_FORECAST_SENSOR,
    CONF_HEATWAVE_THRESHOLD,
    CONF_MAX_HOURS,
    CONF_MIN_HOURS,
    CONF_PIVOT_HOUR,
    CONF_BACKWASH_DURATION_MINUTES,
    CONF_ELECTROLYZER_POWER_SENSOR,
    CONF_POOL_HAS_COVER,
    CONF_POOL_IMAGE_URL,
    CONF_POOL_PRESET,
    CONF_PUMP_POWER_SENSOR,
    CONF_PUMP_SHORT_CYCLE_THRESHOLD,
    CONF_PUMP_SWITCH,
    CONF_SMOOTHING_WINDOW_HOURS,
    CONF_SOLAR_COEFFICIENT,
    CONF_SOLAR_INSTALLED_WATTS,
    CONF_SOLAR_PEAK_SENSOR,
    CONF_SOLAR_POWER_SENSOR,
    CONF_TAU_HOURS,
    CONF_TEMPERATURE_MODE,
    CONF_TEMPERATURE_OFFSET,
    CONF_TEMPERATURE_SENSOR,
    CONF_WATER_LEVEL_CRITICAL,
    CONF_WEATHER_ENTITY,
    CONF_WINTERIZATION_END_MONTH,
    CONF_WINTERIZATION_START_MONTH,
    DEFAULT_AUTOTUNE_ENABLED,
    DEFAULT_BACKWASH_DURATION_MINUTES,
    DEFAULT_CHEMISTRY_ENABLED,
    DEFAULT_CUSTOM_POOL_INGROUND,
    DEFAULT_CUSTOM_POOL_SHAPE,
    DEFAULT_DURATION_AT_5C,
    DEFAULT_DURATION_AT_10C,
    DEFAULT_DURATION_AT_15C,
    DEFAULT_DURATION_AT_20C,
    DEFAULT_DURATION_AT_25C,
    DEFAULT_DURATION_AT_30C,
    DEFAULT_DURATION_AT_35C,
    DEFAULT_DURATION_CURVE_ENABLED,
    DEFAULT_EARLIEST_START_HOUR,
    DEFAULT_FILTRATION_MULTIPLIER,
    DEFAULT_LATEST_END_HOUR,
    DEFAULT_SHOW_ILLUSTRATION,
    DEFAULT_WINTERIZATION_OVERRIDE,
    WINTERIZATION_OVERRIDE_OPTIONS,
    DEFAULT_BREAK_HOURS,
    DEFAULT_ELECTROLYZER_MAX_TEMP,
    DEFAULT_ELECTROLYZER_MIN_TEMP,
    DEFAULT_ELECTROLYZER_POST_START_DELAY,
    DEFAULT_ELECTROLYZER_PRE_STOP_DELAY,
    DEFAULT_PAC_MIN_TEMP,
    DEFAULT_PAC_POST_START_DELAY,
    DEFAULT_PAC_PRE_STOP_DELAY,
    DEFAULT_HEATWAVE_THRESHOLD,
    DEFAULT_MAX_HOURS,
    DEFAULT_MIN_HOURS,
    DEFAULT_PIVOT_HOUR,
    DEFAULT_PUMP_SHORT_CYCLE_THRESHOLD,
    DEFAULT_SMOOTHING_WINDOW_HOURS,
    DEFAULT_SOLAR_COEFFICIENT,
    DEFAULT_TAU_HOURS,
    DEFAULT_TEMPERATURE_MODE,
    DEFAULT_TEMPERATURE_OFFSET,
    DOMAIN,
    NAME,
    TEMP_MODE_AIR_MODEL,
    TEMP_MODE_OPTIONS,
    TEMP_MODE_WATER,
)
from .presets import POOL_PRESETS, PRESET_CUSTOM


def _temperature_mode_selector() -> SelectSelector:
    return SelectSelector(
        SelectSelectorConfig(
            options=list(TEMP_MODE_OPTIONS),
            mode=SelectSelectorMode.LIST,
            translation_key="temperature_mode",
        )
    )


def _preset_selector() -> SelectSelector:
    options = [{"value": p["slug"], "label": p["name"]} for p in POOL_PRESETS]
    options.append({"value": PRESET_CUSTOM, "label": "Personnalisé (sans preset)"})
    # No translation_key: with 43 presets, providing translations for each
    # via strings.json is impractical. Without translations, HA can fall
    # back to rendering options as "[object Object]" because the
    # translation_key takes precedence over the inline `label`. Keeping
    # only the inline label avoids that.
    return SelectSelector(
        SelectSelectorConfig(
            options=options,
            mode=SelectSelectorMode.DROPDOWN,
            custom_value=False,
        )
    )


def _required_schema(current: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_PUMP_SWITCH): EntitySelector(
                EntitySelectorConfig(domain="switch")
            ),
            vol.Required(
                CONF_TEMPERATURE_MODE,
                default=current.get(CONF_TEMPERATURE_MODE, DEFAULT_TEMPERATURE_MODE),
            ): _temperature_mode_selector(),
            vol.Required(CONF_TEMPERATURE_SENSOR): EntitySelector(
                EntitySelectorConfig(domain=["sensor", "input_number"])
            ),
        }
    )


def _detect_solar_sensors(hass) -> tuple[str | None, str | None]:
    """Scan hass.states for likely solar power sensors.

    Returns (instant_power_entity_id, peak_today_entity_id) or (None, None)
    if no obvious candidate. Heuristic: device_class=power + entity_id /
    friendly_name contains solar/pv/mptt/victron, with "peak"/"max"/"today"
    flagging the peak candidate vs the instantaneous one.
    """
    if hass is None:
        return None, None
    instant = None
    peak = None
    for state in hass.states.async_all("sensor"):
        a = state.attributes
        if a.get("device_class") != "power":
            continue
        eid = state.entity_id.lower()
        fn = (a.get("friendly_name", "") or "").lower()
        text = eid + " " + fn
        is_solar = any(k in text for k in ("solar", "pv ", "_pv_", "mptt", "mppt", "solarcharger"))
        if not is_solar:
            continue
        is_peak = any(k in text for k in ("max_power", "maxpower", "peak", "max power"))
        if is_peak and peak is None:
            peak = state.entity_id
        elif not is_peak and instant is None:
            # Prefer the simplest "victron_solar_power" or "gx_device_pv_power"
            # over the tracker-* subsensors that are usually 0.
            if "tracker_" in text and "_pv_power" in text:
                continue
            instant = state.entity_id
    return instant, peak


def _detect_power_sensor_for_switch(hass, switch_entity_id: str | None) -> str | None:
    """Find a power sensor associated with a switch entity (by name prefix)."""
    if not switch_entity_id or hass is None:
        return None
    base = switch_entity_id.split(".", 1)[1] if "." in switch_entity_id else switch_entity_id
    for state in hass.states.async_all("sensor"):
        if state.attributes.get("device_class") != "power":
            continue
        if base in state.entity_id:
            return state.entity_id
    return None


def _options_schema(current: dict[str, Any], hass=None) -> vol.Schema:
    mode = current.get(CONF_TEMPERATURE_MODE, DEFAULT_TEMPERATURE_MODE)
    schema: dict[Any, Any] = {}

    # Auto-detected suggestions for sensors the user hasn't explicitly set
    detected_solar_instant, detected_solar_peak = _detect_solar_sensors(hass)
    detected_pump_power = _detect_power_sensor_for_switch(
        hass, current.get(CONF_PUMP_SWITCH)
    )
    detected_elec_power = _detect_power_sensor_for_switch(
        hass, current.get(CONF_ELECTROLYZER_SWITCH)
    )
    detected_pac_power = _detect_power_sensor_for_switch(
        hass, current.get(CONF_PAC_SWITCH)
    )

    # Core temperature source — exposed in options too so users can
    # switch between air model / water probe after install (e.g., when
    # they finally install a Sonoff WTS01 + thermowell).
    schema[
        vol.Required(
            CONF_TEMPERATURE_MODE,
            default=mode,
        )
    ] = _temperature_mode_selector()
    schema[
        vol.Required(
            CONF_TEMPERATURE_SENSOR,
            description={"suggested_value": current.get(CONF_TEMPERATURE_SENSOR)},
        )
    ] = EntitySelector(
        EntitySelectorConfig(domain=["sensor", "input_number"])
    )

    # Preset selector is always shown — it drives the dashboard SVG and,
    # in air_model mode, the default tau.
    schema[
        vol.Optional(
            CONF_POOL_PRESET,
            description={"suggested_value": current.get(CONF_POOL_PRESET, PRESET_CUSTOM)},
        )
    ] = _preset_selector()
    schema[
        vol.Optional(
            CONF_POOL_HAS_COVER,
            default=bool(current.get(CONF_POOL_HAS_COVER, False)),
        )
    ] = bool

    # Custom-preset dimensions: always shown but only USED when the
    # selected preset is "custom" (otherwise these values are ignored).
    # Keeping them visible avoids a multi-step config flow just for
    # users with unsupported pool models.
    schema[
        vol.Optional(
            CONF_CUSTOM_POOL_SHAPE,
            default=current.get(CONF_CUSTOM_POOL_SHAPE, DEFAULT_CUSTOM_POOL_SHAPE),
        )
    ] = SelectSelector(
        SelectSelectorConfig(
            options=[
                {"value": "rect", "label": "Rectangulaire"},
                {"value": "round", "label": "Ronde"},
            ],
            mode=SelectSelectorMode.LIST,
        )
    )
    schema[
        vol.Optional(
            CONF_CUSTOM_POOL_LENGTH,
            description={"suggested_value": current.get(CONF_CUSTOM_POOL_LENGTH)},
        )
    ] = NumberSelector(
        NumberSelectorConfig(min=50, max=2500, step=1, mode=NumberSelectorMode.BOX,
                             unit_of_measurement="cm")
    )
    schema[
        vol.Optional(
            CONF_CUSTOM_POOL_WIDTH,
            description={"suggested_value": current.get(CONF_CUSTOM_POOL_WIDTH)},
        )
    ] = NumberSelector(
        NumberSelectorConfig(min=50, max=2500, step=1, mode=NumberSelectorMode.BOX,
                             unit_of_measurement="cm")
    )
    schema[
        vol.Optional(
            CONF_CUSTOM_POOL_DEPTH,
            description={"suggested_value": current.get(CONF_CUSTOM_POOL_DEPTH)},
        )
    ] = NumberSelector(
        NumberSelectorConfig(min=30, max=400, step=1, mode=NumberSelectorMode.BOX,
                             unit_of_measurement="cm")
    )
    schema[
        vol.Optional(
            CONF_CUSTOM_POOL_INGROUND,
            default=bool(
                current.get(CONF_CUSTOM_POOL_INGROUND, DEFAULT_CUSTOM_POOL_INGROUND)
            ),
        )
    ] = bool

    if mode == TEMP_MODE_AIR_MODEL:
        # Tau optional: empty = derive from preset (if any) or DEFAULT_TAU_HOURS.
        schema[
            vol.Optional(
                CONF_TAU_HOURS,
                description={
                    "suggested_value": current.get(CONF_TAU_HOURS, DEFAULT_TAU_HOURS)
                },
            )
        ] = NumberSelector(
            NumberSelectorConfig(min=1, max=240, step=1, mode=NumberSelectorMode.BOX)
        )
        schema[
            vol.Optional(
                CONF_TEMPERATURE_OFFSET,
                default=current.get(
                    CONF_TEMPERATURE_OFFSET, DEFAULT_TEMPERATURE_OFFSET
                ),
            )
        ] = NumberSelector(
            NumberSelectorConfig(min=-10, max=10, step=0.5, mode=NumberSelectorMode.BOX)
        )
        schema[
            vol.Optional(
                CONF_SMOOTHING_WINDOW_HOURS,
                default=current.get(
                    CONF_SMOOTHING_WINDOW_HOURS, DEFAULT_SMOOTHING_WINDOW_HOURS
                ),
            )
        ] = NumberSelector(
            NumberSelectorConfig(min=1, max=168, step=1, mode=NumberSelectorMode.BOX)
        )
        schema[
            vol.Optional(
                CONF_SOLAR_POWER_SENSOR,
                description={
                    "suggested_value": current.get(CONF_SOLAR_POWER_SENSOR)
                    or detected_solar_instant
                },
            )
        ] = EntitySelector(
            EntitySelectorConfig(domain="sensor", device_class="power")
        )
        schema[
            vol.Optional(
                CONF_SOLAR_INSTALLED_WATTS,
                description={
                    "suggested_value": current.get(CONF_SOLAR_INSTALLED_WATTS)
                },
            )
        ] = NumberSelector(
            NumberSelectorConfig(min=0, max=30000, step=50, mode=NumberSelectorMode.BOX)
        )
        schema[
            vol.Optional(
                CONF_SOLAR_PEAK_SENSOR,
                description={
                    "suggested_value": current.get(CONF_SOLAR_PEAK_SENSOR)
                    or detected_solar_peak
                },
            )
        ] = EntitySelector(
            EntitySelectorConfig(domain="sensor", device_class="power")
        )
        schema[
            vol.Optional(
                CONF_SOLAR_COEFFICIENT,
                # `suggested_value` (not `default`) so blank stays blank
                # and the coordinator can auto-derive from preset.
                description={"suggested_value": current.get(CONF_SOLAR_COEFFICIENT)},
            )
        ] = NumberSelector(
            NumberSelectorConfig(min=0, max=3, step=0.1, mode=NumberSelectorMode.BOX)
        )

    schema.update(
        {
            vol.Optional(
                CONF_MIN_HOURS,
                default=current.get(CONF_MIN_HOURS, DEFAULT_MIN_HOURS),
            ): NumberSelector(
                NumberSelectorConfig(min=0, max=24, step=0.5, mode=NumberSelectorMode.BOX)
            ),
            vol.Optional(
                CONF_MAX_HOURS,
                default=current.get(CONF_MAX_HOURS, DEFAULT_MAX_HOURS),
            ): NumberSelector(
                NumberSelectorConfig(min=1, max=24, step=0.5, mode=NumberSelectorMode.BOX)
            ),
            vol.Optional(
                CONF_BREAK_HOURS,
                default=current.get(CONF_BREAK_HOURS, DEFAULT_BREAK_HOURS),
            ): NumberSelector(
                NumberSelectorConfig(min=0, max=6, step=0.25, mode=NumberSelectorMode.BOX)
            ),
            vol.Optional(
                CONF_PIVOT_HOUR,
                default=current.get(CONF_PIVOT_HOUR, DEFAULT_PIVOT_HOUR),
            ): NumberSelector(
                NumberSelectorConfig(min=0, max=23, step=1, mode=NumberSelectorMode.BOX)
            ),
            vol.Optional(
                CONF_EARLIEST_START_HOUR,
                default=current.get(
                    CONF_EARLIEST_START_HOUR, DEFAULT_EARLIEST_START_HOUR
                ),
            ): NumberSelector(
                NumberSelectorConfig(min=0, max=24, step=1, mode=NumberSelectorMode.BOX)
            ),
            vol.Optional(
                CONF_LATEST_END_HOUR,
                default=current.get(
                    CONF_LATEST_END_HOUR, DEFAULT_LATEST_END_HOUR
                ),
            ): NumberSelector(
                NumberSelectorConfig(min=0, max=24, step=1, mode=NumberSelectorMode.BOX)
            ),
            vol.Optional(
                CONF_FILTRATION_MULTIPLIER,
                default=float(
                    current.get(
                        CONF_FILTRATION_MULTIPLIER, DEFAULT_FILTRATION_MULTIPLIER
                    )
                ),
            ): NumberSelector(
                NumberSelectorConfig(
                    min=0.3, max=3.0, step=0.05, mode=NumberSelectorMode.BOX
                )
            ),
            vol.Optional(
                CONF_DURATION_CURVE_ENABLED,
                default=bool(
                    current.get(
                        CONF_DURATION_CURVE_ENABLED, DEFAULT_DURATION_CURVE_ENABLED
                    )
                ),
            ): bool,
            vol.Optional(
                CONF_DURATION_AT_5C,
                default=float(
                    current.get(CONF_DURATION_AT_5C, DEFAULT_DURATION_AT_5C)
                ),
            ): NumberSelector(
                NumberSelectorConfig(min=0, max=24, step=0.25, mode=NumberSelectorMode.BOX,
                                     unit_of_measurement="h")
            ),
            vol.Optional(
                CONF_DURATION_AT_10C,
                default=float(
                    current.get(CONF_DURATION_AT_10C, DEFAULT_DURATION_AT_10C)
                ),
            ): NumberSelector(
                NumberSelectorConfig(min=0, max=24, step=0.25, mode=NumberSelectorMode.BOX,
                                     unit_of_measurement="h")
            ),
            vol.Optional(
                CONF_DURATION_AT_15C,
                default=float(
                    current.get(CONF_DURATION_AT_15C, DEFAULT_DURATION_AT_15C)
                ),
            ): NumberSelector(
                NumberSelectorConfig(min=0, max=24, step=0.25, mode=NumberSelectorMode.BOX,
                                     unit_of_measurement="h")
            ),
            vol.Optional(
                CONF_DURATION_AT_20C,
                default=float(
                    current.get(CONF_DURATION_AT_20C, DEFAULT_DURATION_AT_20C)
                ),
            ): NumberSelector(
                NumberSelectorConfig(min=0, max=24, step=0.25, mode=NumberSelectorMode.BOX,
                                     unit_of_measurement="h")
            ),
            vol.Optional(
                CONF_DURATION_AT_25C,
                default=float(
                    current.get(CONF_DURATION_AT_25C, DEFAULT_DURATION_AT_25C)
                ),
            ): NumberSelector(
                NumberSelectorConfig(min=0, max=24, step=0.25, mode=NumberSelectorMode.BOX,
                                     unit_of_measurement="h")
            ),
            vol.Optional(
                CONF_DURATION_AT_30C,
                default=float(
                    current.get(CONF_DURATION_AT_30C, DEFAULT_DURATION_AT_30C)
                ),
            ): NumberSelector(
                NumberSelectorConfig(min=0, max=24, step=0.25, mode=NumberSelectorMode.BOX,
                                     unit_of_measurement="h")
            ),
            vol.Optional(
                CONF_DURATION_AT_35C,
                default=float(
                    current.get(CONF_DURATION_AT_35C, DEFAULT_DURATION_AT_35C)
                ),
            ): NumberSelector(
                NumberSelectorConfig(min=0, max=24, step=0.25, mode=NumberSelectorMode.BOX,
                                     unit_of_measurement="h")
            ),
            vol.Optional(
                CONF_WINTERIZATION_OVERRIDE,
                default=current.get(
                    CONF_WINTERIZATION_OVERRIDE, DEFAULT_WINTERIZATION_OVERRIDE
                ),
            ): SelectSelector(
                SelectSelectorConfig(
                    options=list(WINTERIZATION_OVERRIDE_OPTIONS),
                    mode=SelectSelectorMode.LIST,
                    translation_key="winterization_override",
                )
            ),
            vol.Optional(
                CONF_FORECAST_SENSOR,
                description={"suggested_value": current.get(CONF_FORECAST_SENSOR)},
            ): EntitySelector(EntitySelectorConfig(domain="sensor")),
            vol.Optional(
                CONF_WEATHER_ENTITY,
                description={"suggested_value": current.get(CONF_WEATHER_ENTITY)},
            ): EntitySelector(EntitySelectorConfig(domain="weather")),
            vol.Optional(
                CONF_HEATWAVE_THRESHOLD,
                default=current.get(
                    CONF_HEATWAVE_THRESHOLD, DEFAULT_HEATWAVE_THRESHOLD
                ),
            ): NumberSelector(
                NumberSelectorConfig(min=20, max=45, step=0.5, mode=NumberSelectorMode.BOX)
            ),
            vol.Optional(
                CONF_ELECTROLYZER_SWITCH,
                description={
                    "suggested_value": current.get(CONF_ELECTROLYZER_SWITCH)
                },
            ): EntitySelector(EntitySelectorConfig(domain="switch")),
            vol.Optional(
                CONF_ELECTROLYZER_POST_START_DELAY,
                default=current.get(
                    CONF_ELECTROLYZER_POST_START_DELAY,
                    DEFAULT_ELECTROLYZER_POST_START_DELAY,
                ),
            ): NumberSelector(
                NumberSelectorConfig(min=0, max=900, step=10, mode=NumberSelectorMode.BOX)
            ),
            vol.Optional(
                CONF_ELECTROLYZER_PRE_STOP_DELAY,
                default=current.get(
                    CONF_ELECTROLYZER_PRE_STOP_DELAY,
                    DEFAULT_ELECTROLYZER_PRE_STOP_DELAY,
                ),
            ): NumberSelector(
                NumberSelectorConfig(min=0, max=900, step=10, mode=NumberSelectorMode.BOX)
            ),
            vol.Optional(
                CONF_ELECTROLYZER_MIN_TEMP,
                default=current.get(
                    CONF_ELECTROLYZER_MIN_TEMP, DEFAULT_ELECTROLYZER_MIN_TEMP
                ),
            ): NumberSelector(
                NumberSelectorConfig(min=0, max=25, step=0.5, mode=NumberSelectorMode.BOX)
            ),
            vol.Optional(
                CONF_ELECTROLYZER_MAX_TEMP,
                default=current.get(
                    CONF_ELECTROLYZER_MAX_TEMP, DEFAULT_ELECTROLYZER_MAX_TEMP
                ),
            ): NumberSelector(
                NumberSelectorConfig(min=25, max=50, step=0.5, mode=NumberSelectorMode.BOX)
            ),
            vol.Optional(
                CONF_PAC_SWITCH,
                description={"suggested_value": current.get(CONF_PAC_SWITCH)},
            ): EntitySelector(EntitySelectorConfig(domain="switch")),
            vol.Optional(
                CONF_PAC_POST_START_DELAY,
                default=current.get(
                    CONF_PAC_POST_START_DELAY, DEFAULT_PAC_POST_START_DELAY
                ),
            ): NumberSelector(
                NumberSelectorConfig(min=0, max=900, step=10, mode=NumberSelectorMode.BOX)
            ),
            vol.Optional(
                CONF_PAC_PRE_STOP_DELAY,
                default=current.get(
                    CONF_PAC_PRE_STOP_DELAY, DEFAULT_PAC_PRE_STOP_DELAY
                ),
            ): NumberSelector(
                NumberSelectorConfig(min=0, max=1800, step=10, mode=NumberSelectorMode.BOX)
            ),
            vol.Optional(
                CONF_PAC_MIN_TEMP,
                default=current.get(CONF_PAC_MIN_TEMP, DEFAULT_PAC_MIN_TEMP),
            ): NumberSelector(
                NumberSelectorConfig(min=0, max=30, step=0.5, mode=NumberSelectorMode.BOX)
            ),
            vol.Optional(
                CONF_WATER_LEVEL_CRITICAL,
                description={"suggested_value": current.get(CONF_WATER_LEVEL_CRITICAL)},
            ): EntitySelector(EntitySelectorConfig(domain="binary_sensor")),
            vol.Optional(
                CONF_PUMP_POWER_SENSOR,
                description={
                    "suggested_value": current.get(CONF_PUMP_POWER_SENSOR)
                    or detected_pump_power
                },
            ): EntitySelector(
                EntitySelectorConfig(domain="sensor", device_class="power")
            ),
            vol.Optional(
                CONF_ELECTROLYZER_POWER_SENSOR,
                description={
                    "suggested_value": current.get(CONF_ELECTROLYZER_POWER_SENSOR)
                    or detected_elec_power
                },
            ): EntitySelector(
                EntitySelectorConfig(domain="sensor", device_class="power")
            ),
            vol.Optional(
                CONF_PAC_POWER_SENSOR,
                description={
                    "suggested_value": current.get(CONF_PAC_POWER_SENSOR)
                    or detected_pac_power
                },
            ): EntitySelector(
                EntitySelectorConfig(domain="sensor", device_class="power")
            ),
            vol.Optional(
                CONF_WINTERIZATION_START_MONTH,
                default=current.get(CONF_WINTERIZATION_START_MONTH, 0),
            ): NumberSelector(
                NumberSelectorConfig(min=0, max=12, step=1, mode=NumberSelectorMode.BOX)
            ),
            vol.Optional(
                CONF_WINTERIZATION_END_MONTH,
                default=current.get(CONF_WINTERIZATION_END_MONTH, 0),
            ): NumberSelector(
                NumberSelectorConfig(min=0, max=12, step=1, mode=NumberSelectorMode.BOX)
            ),
            vol.Optional(
                CONF_BACKWASH_DURATION_MINUTES,
                default=current.get(
                    CONF_BACKWASH_DURATION_MINUTES, DEFAULT_BACKWASH_DURATION_MINUTES
                ),
            ): NumberSelector(
                NumberSelectorConfig(min=1, max=60, step=1, mode=NumberSelectorMode.BOX)
            ),
            vol.Optional(
                CONF_PUMP_SHORT_CYCLE_THRESHOLD,
                default=current.get(
                    CONF_PUMP_SHORT_CYCLE_THRESHOLD, DEFAULT_PUMP_SHORT_CYCLE_THRESHOLD
                ),
            ): NumberSelector(
                NumberSelectorConfig(min=0, max=300, step=5, mode=NumberSelectorMode.BOX)
            ),
            vol.Optional(
                CONF_POOL_IMAGE_URL,
                description={"suggested_value": current.get(CONF_POOL_IMAGE_URL)},
            ): str,
            vol.Optional(
                CONF_AUTOTUNE_ENABLED,
                default=bool(
                    current.get(CONF_AUTOTUNE_ENABLED, DEFAULT_AUTOTUNE_ENABLED)
                ),
            ): bool,
            vol.Optional(
                CONF_SHOW_ILLUSTRATION,
                default=bool(
                    current.get(CONF_SHOW_ILLUSTRATION, DEFAULT_SHOW_ILLUSTRATION)
                ),
            ): bool,
            vol.Optional(
                CONF_CHEMISTRY_ENABLED,
                default=bool(
                    current.get(CONF_CHEMISTRY_ENABLED, DEFAULT_CHEMISTRY_ENABLED)
                ),
            ): bool,
        }
    )
    return vol.Schema(schema)


class PoolPumpConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Initial setup flow."""

    VERSION = 1

    def __init__(self) -> None:
        self._base: dict[str, Any] = {}

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_PUMP_SWITCH])
            self._abort_if_unique_id_configured()
            self._base = user_input
            return await self.async_step_options()
        return self.async_show_form(step_id="user", data_schema=_required_schema({}))

    async def async_step_options(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            data = {
                **self._base,
                **{k: v for k, v in user_input.items() if v is not None},
            }
            return self.async_create_entry(title=NAME, data=data)
        return self.async_show_form(
            step_id="options", data_schema=_options_schema(self._base, hass=self.hass)
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        entry: config_entries.ConfigEntry,
    ) -> "PoolPumpOptionsFlow":
        return PoolPumpOptionsFlow(entry)


class PoolPumpOptionsFlow(config_entries.OptionsFlow):
    """Re-edit options after install."""

    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        self.entry = entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            return self.async_create_entry(
                title="",
                data={k: v for k, v in user_input.items() if v is not None},
            )
        current = {**self.entry.data, **self.entry.options}
        return self.async_show_form(
            step_id="init", data_schema=_options_schema(current, hass=self.hass)
        )
