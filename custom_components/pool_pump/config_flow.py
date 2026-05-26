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
    CONF_BREAK_HOURS,
    CONF_ELECTROLYZER_MAX_TEMP,
    CONF_ELECTROLYZER_MIN_TEMP,
    CONF_ELECTROLYZER_POST_START_DELAY,
    CONF_ELECTROLYZER_PRE_STOP_DELAY,
    CONF_ELECTROLYZER_SWITCH,
    CONF_FORECAST_SENSOR,
    CONF_HEATWAVE_THRESHOLD,
    CONF_MAX_HOURS,
    CONF_MIN_HOURS,
    CONF_PIVOT_HOUR,
    CONF_POOL_HAS_COVER,
    CONF_POOL_PRESET,
    CONF_PUMP_SWITCH,
    CONF_SMOOTHING_WINDOW_HOURS,
    CONF_SOLAR_COEFFICIENT,
    CONF_SOLAR_PEAK_SENSOR,
    CONF_SOLAR_POWER_SENSOR,
    CONF_TAU_HOURS,
    CONF_TEMPERATURE_MODE,
    CONF_TEMPERATURE_OFFSET,
    CONF_TEMPERATURE_SENSOR,
    CONF_WATER_LEVEL_CRITICAL,
    DEFAULT_BREAK_HOURS,
    DEFAULT_ELECTROLYZER_MAX_TEMP,
    DEFAULT_ELECTROLYZER_MIN_TEMP,
    DEFAULT_ELECTROLYZER_POST_START_DELAY,
    DEFAULT_ELECTROLYZER_PRE_STOP_DELAY,
    DEFAULT_HEATWAVE_THRESHOLD,
    DEFAULT_MAX_HOURS,
    DEFAULT_MIN_HOURS,
    DEFAULT_PIVOT_HOUR,
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


def _options_schema(current: dict[str, Any]) -> vol.Schema:
    mode = current.get(CONF_TEMPERATURE_MODE, DEFAULT_TEMPERATURE_MODE)
    schema: dict[Any, Any] = {}

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
                description={"suggested_value": current.get(CONF_SOLAR_POWER_SENSOR)},
            )
        ] = EntitySelector(
            EntitySelectorConfig(domain="sensor", device_class="power")
        )
        schema[
            vol.Optional(
                CONF_SOLAR_PEAK_SENSOR,
                description={"suggested_value": current.get(CONF_SOLAR_PEAK_SENSOR)},
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
                CONF_FORECAST_SENSOR,
                description={"suggested_value": current.get(CONF_FORECAST_SENSOR)},
            ): EntitySelector(EntitySelectorConfig(domain="sensor")),
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
                CONF_WATER_LEVEL_CRITICAL,
                description={"suggested_value": current.get(CONF_WATER_LEVEL_CRITICAL)},
            ): EntitySelector(EntitySelectorConfig(domain="binary_sensor")),
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
            step_id="options", data_schema=_options_schema(self._base)
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
            step_id="init", data_schema=_options_schema(current)
        )
