"""DataUpdateCoordinator for eaton_ups."""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    IntegrationBlueprintApiClientAuthenticationError,
    IntegrationBlueprintApiClientError,
)

if TYPE_CHECKING:
    from .data import IntegrationBlueprintConfigEntry


class BlueprintDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching data from the API."""

    config_entry: IntegrationBlueprintConfigEntry

    async def _async_update_data(self) -> Any:
        """Update data via library."""
        try:
            # Ensure MQTT connection is established
            client = self.config_entry.runtime_data.client
            if not hasattr(client, '_mqtt_connected') or not client._mqtt_connected:
                await client.async_setup()

            # Get the current data from the MQTT client
            return await client.async_get_data()
        except IntegrationBlueprintApiClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except IntegrationBlueprintApiClientError as exception:
            raise UpdateFailed(exception) from exception

    async def async_shutdown(self) -> None:
        """Shutdown the coordinator and disconnect MQTT."""
        await self.config_entry.runtime_data.client.async_disconnect()
        await super().async_shutdown()