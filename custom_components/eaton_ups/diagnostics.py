"""Diagnostics support for Eaton UPS."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from . import EatonUpsConfigEntry
    from .coordinator import EatonUPSDataUpdateCoordinator


async def async_get_config_entry_diagnostics(
    _hass: HomeAssistant,
    config_entry: EatonUpsConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator: EatonUPSDataUpdateCoordinator = config_entry.runtime_data.coordinator

    return {
        "coordinator_data": coordinator.data, # MQTT topics with data from the coordinator (without version prefix)
    }
