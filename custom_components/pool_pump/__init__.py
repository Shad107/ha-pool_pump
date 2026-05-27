"""Pool Pump Manager integration setup."""
from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED, Platform
from homeassistant.core import CoreState, HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, URL_BASE, VERSION
from .coordinator import PoolPumpCoordinator
from .frontend_setup import JSModuleRegistration

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR, Platform.SELECT, Platform.BINARY_SENSOR]

FRONTEND_DIR = Path(__file__).parent / "frontend"
CARD_FILE = "pool-pump-card.js"


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """One-shot setup: register the bundled Lovelace card.

    For storage-mode dashboards, the card MUST be registered via the
    Lovelace resources collection; only then is it loaded in the scoped
    custom-element registry the picker uses for `whenDefined`. For
    YAML-mode dashboards, `add_extra_js_url` is sufficient. We register
    both, covering every user setup.
    """
    # YAML-mode fallback (kept for users with mode: yaml in lovelace).
    if FRONTEND_DIR.is_dir() and (FRONTEND_DIR / CARD_FILE).exists():
        try:
            await hass.http.async_register_static_paths(
                [StaticPathConfig(URL_BASE, str(FRONTEND_DIR), False)]
            )
        except RuntimeError:
            pass  # already registered
        add_extra_js_url(hass, f"{URL_BASE}/{CARD_FILE}?v={VERSION}")

    # Storage-mode primary path — Lovelace resource registration. May
    # need to wait until lovelace.resources.loaded becomes True.
    async def _register_resource(_event=None):
        try:
            await JSModuleRegistration(hass).async_register()
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning("Lovelace resource registration failed: %s", err)

    if hass.state == CoreState.running:
        await _register_resource()
    else:
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, _register_resource)

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Pool Pump Manager from a config entry."""
    options = {**entry.data, **entry.options}
    coordinator = PoolPumpCoordinator(hass, entry.entry_id, options)
    await coordinator.async_load_persisted()
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    if not hass.services.has_service(DOMAIN, "refresh"):
        async def _refresh(_call):
            for c in hass.data.get(DOMAIN, {}).values():
                await c.async_request_refresh()

        hass.services.async_register(DOMAIN, "refresh", _refresh)

    if not hass.services.has_service(DOMAIN, "backwash"):
        async def _backwash(call):
            duration = call.data.get("duration_minutes")
            for c in hass.data.get(DOMAIN, {}).values():
                c.trigger_backwash(duration)

        hass.services.async_register(DOMAIN, "backwash", _backwash)

    if not hass.services.has_service(DOMAIN, "cancel_backwash"):
        async def _cancel(_call):
            for c in hass.data.get(DOMAIN, {}).values():
                c.cancel_backwash()

        hass.services.async_register(DOMAIN, "cancel_backwash", _cancel)

    if not hass.services.has_service(DOMAIN, "reset_water_model"):
        async def _reset(call):
            value = call.data.get("water_temperature")
            for c in hass.data.get(DOMAIN, {}).values():
                c.reset_water_model(float(value) if value is not None else None)

        hass.services.async_register(DOMAIN, "reset_water_model", _reset)

    if not hass.services.has_service(DOMAIN, "clear_calibration"):
        async def _clear(_call):
            for c in hass.data.get(DOMAIN, {}).values():
                c.clear_calibration()

        hass.services.async_register(DOMAIN, "clear_calibration", _clear)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)
