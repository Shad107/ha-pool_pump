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
)

from .const import (
    CONF_BREAK_HOURS,
    CONF_ELECTROLYZER_POST_START_DELAY,
    CONF_ELECTROLYZER_PRE_STOP_DELAY,
    CONF_ELECTROLYZER_SWITCH,
    CONF_FORECAST_SENSOR,
    CONF_HEATWAVE_THRESHOLD,
    CONF_MAX_HOURS,
    CONF_MIN_HOURS,
    CONF_PIVOT_HOUR,
    CONF_PUMP_SWITCH,
    CONF_TEMPERATURE_SENSOR,
    CONF_WATER_LEVEL_CRITICAL,
    DEFAULT_BREAK_HOURS,
    DEFAULT_ELECTROLYZER_POST_START_DELAY,
    DEFAULT_ELECTROLYZER_PRE_STOP_DELAY,
    DEFAULT_HEATWAVE_THRESHOLD,
    DEFAULT_MAX_HOURS,
    DEFAULT_MIN_HOURS,
    DEFAULT_PIVOT_HOUR,
    DOMAIN,
    NAME,
)


def _required_schema() -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_PUMP_SWITCH): EntitySelector(
                EntitySelectorConfig(domain="switch")
            ),
            vol.Required(CONF_TEMPERATURE_SENSOR): EntitySelector(
                EntitySelectorConfig(domain=["sensor", "input_number"])
            ),
        }
    )


def _options_schema(current: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
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
                CONF_WATER_LEVEL_CRITICAL,
                description={"suggested_value": current.get(CONF_WATER_LEVEL_CRITICAL)},
            ): EntitySelector(EntitySelectorConfig(domain="binary_sensor")),
        }
    )


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
        return self.async_show_form(step_id="user", data_schema=_required_schema())

    async def async_step_options(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            data = {**self._base, **{k: v for k, v in user_input.items() if v is not None}}
            return self.async_create_entry(title=NAME, data=data)
        return self.async_show_form(
            step_id="options", data_schema=_options_schema({})
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
