"""Custom types for eaton_ups."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol

from homeassistant.config_entries import ConfigEntry

if TYPE_CHECKING:
    from homeassistant.loader import Integration
    from .api import IntegrationBlueprintApiClient
    from .coordinator import BlueprintDataUpdateCoordinator


# Use Protocol to avoid circular imports
class IntegrationBlueprintConfigEntry(ConfigEntry):
    """Blueprint ConfigEntry with runtime data."""

    runtime_data: "IntegrationBlueprintData"


@dataclass
class IntegrationBlueprintData:
    """Data for the Blueprint integration."""

    client: "IntegrationBlueprintApiClient"
    coordinator: "BlueprintDataUpdateCoordinator"
    integration: "Integration"