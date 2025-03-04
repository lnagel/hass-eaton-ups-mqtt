"""Diagnostics support for Eaton UPS."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.diagnostics import async_redact_data

from . import CONF_CLIENT_CERT, CONF_CLIENT_KEY, CONF_SERVER_CERT
from .const import MQTT_PREFIX

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from . import EatonUpsConfigEntry
    from .coordinator import EatonUPSDataUpdateCoordinator

CONF_TO_REDACT = {CONF_SERVER_CERT, CONF_CLIENT_KEY, CONF_CLIENT_CERT}
DATA_TO_REDACT = {"serialNumber"}


async def async_get_config_entry_diagnostics(
    _hass: HomeAssistant,
    config_entry: EatonUpsConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator: EatonUPSDataUpdateCoordinator = config_entry.runtime_data.coordinator

    return {
        "config_entry": async_redact_data(config_entry.as_dict(), CONF_TO_REDACT),
        "mqtt_prefix": MQTT_PREFIX,
        "coordinator_data": async_redact_data(coordinator.data, DATA_TO_REDACT),
    }
