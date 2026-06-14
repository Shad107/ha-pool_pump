"""Register the bundled Lovelace card with Home Assistant.

For storage-mode dashboards (the default), the picker uses
`customElements.whenDefined()` in a scoped registry that is only populated
by entries registered via `lovelace.resources`. A `<script>` injected by
`frontend.add_extra_js_url` only lands in the top-level document's native
registry, so the picker's `whenDefined` Promise never resolves and the
card preview spins forever.

This module mirrors the pattern used by KipK/marees_france and
AlexxIT/WebRTC — register a Lovelace resource (for storage mode) and a
static path. add_extra_js_url remains in __init__.py as a belt-and-braces
fallback for YAML-mode dashboards.
"""
from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Any

from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_call_later

from .const import JSMODULES, URL_BASE

_LOGGER = logging.getLogger(__name__)

FRONTEND_DIR = Path(__file__).parent / "frontend"


_HASH_CACHE: dict[str, str] = {}


def _read_content_hash(filepath: Path) -> str:
    """Synchronous SHA256 (8-char hex) of a file. Cached per HA process —
    JS bytes only change on integration upgrade, which forces a restart."""
    key = str(filepath)
    if key not in _HASH_CACHE:
        try:
            _HASH_CACHE[key] = hashlib.sha256(filepath.read_bytes()).hexdigest()[:8]
        except OSError:
            _HASH_CACHE[key] = "0"
    return _HASH_CACHE[key]


class JSModuleRegistration:
    """Register the bundled Lovelace card as a Lovelace resource."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self.lovelace = self.hass.data.get("lovelace")

    async def async_register(self) -> None:
        await self._async_register_path()
        if not self.lovelace:
            _LOGGER.debug("Lovelace data not available yet — skipping resource registration")
            return
        mode = getattr(
            self.lovelace, "mode", getattr(self.lovelace, "resource_mode", "yaml")
        )
        if mode == "storage":
            await self._async_wait_for_lovelace_resources()

    async def _async_register_path(self) -> None:
        try:
            await self.hass.http.async_register_static_paths(
                [StaticPathConfig(URL_BASE, str(FRONTEND_DIR), False)]
            )
            _LOGGER.debug("Static path registered: %s -> %s", URL_BASE, FRONTEND_DIR)
        except RuntimeError:
            _LOGGER.debug("Static path already registered: %s", URL_BASE)

    async def _async_wait_for_lovelace_resources(self) -> None:
        async def _check_loaded(_now: Any) -> None:
            if self.lovelace.resources.loaded:
                await self._async_register_modules()
            else:
                _LOGGER.debug("Lovelace resources not loaded yet, retrying in 5s")
                async_call_later(self.hass, 5, _check_loaded)

        await _check_loaded(0)

    async def _async_desired_url(self, module: dict) -> str:
        """Compose the resource URL using the JS file's content hash as a
        cache-bust token. Same bytes → same URL → browser cache hit. Changed
        bytes → new URL → forced refetch. The integration version is kept
        for human-readability. File I/O runs in an executor to avoid
        blocking the event loop."""
        path = f"{URL_BASE}/{module['filename']}"
        h = await self.hass.async_add_executor_job(
            _read_content_hash, FRONTEND_DIR / module["filename"]
        )
        return f"{path}?v={module['version']}&h={h}"

    async def _async_register_modules(self) -> None:
        existing_resources = [
            r for r in self.lovelace.resources.async_items()
            if r["url"].startswith(URL_BASE)
        ]

        for module in JSMODULES:
            url = f"{URL_BASE}/{module['filename']}"
            desired_url = await self._async_desired_url(module)
            registered = False

            for resource in existing_resources:
                if self._get_path(resource["url"]) == url:
                    registered = True
                    if resource["url"] != desired_url:
                        _LOGGER.info(
                            "Updating %s resource URL: %s -> %s",
                            module["name"], resource["url"], desired_url,
                        )
                        await self.lovelace.resources.async_update_item(
                            resource["id"],
                            {
                                "res_type": "module",
                                "url": desired_url,
                            },
                        )
                    break

            if not registered:
                _LOGGER.info(
                    "Registering Lovelace resource: %s v%s (%s)",
                    module["name"], module["version"], desired_url,
                )
                await self.lovelace.resources.async_create_item(
                    {
                        "res_type": "module",
                        "url": desired_url,
                    }
                )

    @staticmethod
    def _get_path(url: str) -> str:
        return url.split("?")[0]

    @staticmethod
    def _get_version(url: str) -> str:
        parts = url.split("?")
        if len(parts) > 1 and parts[1].startswith("v="):
            return parts[1].replace("v=", "")
        return "0"

    async def async_unregister(self) -> None:
        if not self.lovelace:
            return
        mode = getattr(
            self.lovelace, "mode", getattr(self.lovelace, "resource_mode", "yaml")
        )
        if mode != "storage":
            return
        for module in JSMODULES:
            url = f"{URL_BASE}/{module['filename']}"
            resources = [
                r for r in self.lovelace.resources.async_items()
                if r["url"].startswith(url)
            ]
            for resource in resources:
                await self.lovelace.resources.async_delete_item(resource["id"])
