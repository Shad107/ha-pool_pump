"""Pool Pump Manager integration setup."""
from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, VERSION
from .coordinator import PoolPumpCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR, Platform.SELECT, Platform.BINARY_SENSOR]

FRONTEND_URL_BASE = "/pool_pump_card_assets"
FRONTEND_DIR = Path(__file__).parent / "frontend"
CARD_FILE = "pool-pump-card.js"


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """One-shot setup: register the bundled Lovelace card with the frontend.

    Must run in async_setup (not async_setup_entry) so the static path and
    extra JS URL are registered exactly once, regardless of how many
    config entries the user creates.
    """
    if FRONTEND_DIR.is_dir() and (FRONTEND_DIR / CARD_FILE).exists():
        await hass.http.async_register_static_paths(
            [StaticPathConfig(FRONTEND_URL_BASE, str(FRONTEND_DIR), True)]
        )
        add_extra_js_url(hass, f"{FRONTEND_URL_BASE}/{CARD_FILE}?v={VERSION}")
        _LOGGER.debug("Pool Pump Card registered at %s/%s", FRONTEND_URL_BASE, CARD_FILE)
    else:
        _LOGGER.debug(
            "Frontend assets not found at %s; the bundled card will not be available",
            FRONTEND_DIR,
        )
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
