"""Custom types for eaton_ups."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol

from homeassistant.config_entries import ConfigEntry

if TYPE_CHECKING:
    from homeassistant.loader import Integration
    from .api import EatonUpsMqttClient
    from .coordinator import EatonUPSDataUpdateCoordinator


# Use Protocol to avoid circular imports
class EatonUpsConfigEntry(ConfigEntry):
    """Blueprint ConfigEntry with runtime data."""

    runtime_data: "EatonUpsData"


@dataclass
class EatonUpsData:
    """Data for the Blueprint integration."""

    client: "EatonUpsMqttClient"
    coordinator: "EatonUPSDataUpdateCoordinator"
    integration: "Integration"
