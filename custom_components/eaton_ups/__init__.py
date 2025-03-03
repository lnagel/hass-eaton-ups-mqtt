"""
Custom integration to integrate Eaton UPS with Home Assistant.

For more details about this integration, please refer to
https://github.com/lnagel/hass-eaton-ups
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.loader import async_get_loaded_integration

from .api import EatonUpsMqttClient, EatonUpsMqttConfig
from .const import CONF_CLIENT_CERT, CONF_CLIENT_KEY, CONF_SERVER_CERT, DOMAIN, LOGGER
from .coordinator import EatonUPSDataUpdateCoordinator
from .data import EatonUpsData

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import EatonUpsConfigEntry

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
]


# https://developers.home-assistant.io/docs/config_entries_index/#setting-up-an-entry
async def async_setup_entry(
    hass: HomeAssistant,
    entry: EatonUpsConfigEntry,
) -> bool:
    """Set up this integration using UI."""
    coordinator = EatonUPSDataUpdateCoordinator(
        hass=hass,
        logger=LOGGER,
        name=DOMAIN,
    )
    config = EatonUpsMqttConfig(
        host=entry.data[CONF_HOST],
        port=entry.data[CONF_PORT],
        server_cert=entry.data[CONF_SERVER_CERT],
        client_cert=entry.data[CONF_CLIENT_CERT],
        client_key=entry.data[CONF_CLIENT_KEY],
    )
    entry.runtime_data = EatonUpsData(
        client=EatonUpsMqttClient(config=config, session=async_get_clientsession(hass)),
        integration=async_get_loaded_integration(hass, entry.domain),
        coordinator=coordinator,
    )

    # Store coordinator in hass.data
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # Use the standard refresh method
    await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: EatonUpsConfigEntry,
) -> bool:
    """Handle removal of an entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(
    hass: HomeAssistant,
    entry: EatonUpsConfigEntry,
) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
