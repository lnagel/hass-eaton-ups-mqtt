"""DataUpdateCoordinator for eaton_ups."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import PushUpdateCoordinator, UpdateFailed
from homeassistant.core import callback

from .api import (
    EatonUpsClientAuthenticationError,
    EatonUpsClientError,
)
from .const import LOGGER

if TYPE_CHECKING:
    from .data import EatonUpsConfigEntry


class EatonUPSDataUpdateCoordinator(PushUpdateCoordinator[dict[str, Any]]):
    """Class to manage push updates from the MQTT API."""

    config_entry: EatonUpsConfigEntry

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the coordinator."""
        super().__init__(*args, **kwargs)
        self._unsubscribe_callback: Callable[[], None] | None = None

    async def async_setup(self) -> None:
        """Set up the coordinator."""
        try:
            client = self.config_entry.runtime_data.client
            
            # Set up MQTT connection
            await client.async_setup()
            
            # Register callback for MQTT updates
            @callback
            def handle_mqtt_update(data: dict[str, Any]) -> None:
                """Handle MQTT data updates."""
                self.async_set_updated_data(data)
            
            # Store the callback reference for later cleanup
            self._unsubscribe_callback = client.subscribe_to_updates(handle_mqtt_update)
            
            # Get initial data
            data = await client.async_get_data()
            self.async_set_updated_data(data)
            
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
        await self.config_entry.runtime_data.client.async_disconnect()
        await super().async_shutdown()
