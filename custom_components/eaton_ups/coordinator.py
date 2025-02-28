"""DataUpdateCoordinator for eaton_ups."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable
import asyncio

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.core import callback

from .api import (
    EatonUpsClientAuthenticationError,
    EatonUpsClientError,
)
from .const import LOGGER

if TYPE_CHECKING:
    from .data import EatonUpsConfigEntry


class EatonUPSDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage updates from the MQTT API."""

    config_entry: EatonUpsConfigEntry

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the coordinator."""
        # Use a very long update interval since we'll rely on push updates
        kwargs["update_interval"] = None  # Disable polling
        super().__init__(*args, **kwargs)
        self._unsubscribe_callback: Callable[[], None] | None = None
        self._setup_done = False

    async def _async_update_data(self) -> dict[str, Any]:
        """Get data from API."""
        if not self._setup_done:
            await self._async_setup()
        
        # Just return the current data, actual updates come from MQTT callbacks
        if self.config_entry.runtime_data.client:
            return await self.config_entry.runtime_data.client.async_get_data()
        return {}

    async def _async_setup(self) -> None:
        """Set up the coordinator."""
        try:
            client = self.config_entry.runtime_data.client
            
            # Set up MQTT connection
            await client.async_setup()
            
            # Register callback for MQTT updates
            @callback
            def handle_mqtt_update(data: dict[str, Any]) -> None:
                """Handle MQTT data updates."""
                # Use async_set_updated_data which is safe to call from any thread
                # as it will schedule the update on the event loop
                self.async_set_updated_data(data)
            
            # Store the callback reference for later cleanup
            self._unsubscribe_callback = client.subscribe_to_updates(handle_mqtt_update)
            self._setup_done = True
            
        except EatonUpsClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except EatonUpsClientError as exception:
            raise UpdateFailed(exception) from exception

    async def async_shutdown(self) -> None:
        """Shutdown the coordinator and disconnect MQTT."""
        # Unsubscribe from MQTT updates if callback exists
        if self._unsubscribe_callback is not None:
            self._unsubscribe_callback()
            self._unsubscribe_callback = None
            
        # Disconnect MQTT client
        if self.config_entry.runtime_data.client:
            await self.config_entry.runtime_data.client.async_disconnect()
        await super().async_shutdown()
