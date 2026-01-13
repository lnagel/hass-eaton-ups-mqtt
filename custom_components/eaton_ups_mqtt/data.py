"""Custom types for eaton_ups_mqtt."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

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


type EatonUpsConfigEntry = ConfigEntry[EatonUpsData]
