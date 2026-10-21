"""Custom types for eaton_ups_mqtt."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.loader import Integration

    from .api import EatonUpsMqttClient
    from .coordinator import EatonUPSDataUpdateCoordinator


@dataclass
class EatonUpsData:
    """Data for the Eaton UPS integration."""

    client: EatonUpsMqttClient
    coordinator: EatonUPSDataUpdateCoordinator
    integration: Integration
    config_data: dict[str, Any]


type EatonUpsConfigEntry = ConfigEntry[EatonUpsData]
