"""DataUpdateCoordinator for eaton_ups_mqtt."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

from homeassistant.core import callback
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.debounce import Debouncer
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    EatonUpsClientAuthenticationError,
    EatonUpsClientError,
)
from .const import DEFAULT_DEBOUNCE_INTERVAL, LOGGER, MQTT_MEASURES_SUFFIX

if TYPE_CHECKING:
    from .data import EatonUpsConfigEntry


class EatonUPSDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage updates from the MQTT API."""

    config_entry: EatonUpsConfigEntry

    def __init__(
        self,
        *args: Any,
        debounce_interval: float = DEFAULT_DEBOUNCE_INTERVAL,
        **kwargs: Any,
    ) -> None:
        """Initialize the coordinator."""
        # Use a very long update interval since we'll rely on push updates
        kwargs["update_interval"] = None  # Disable polling
        super().__init__(*args, **kwargs)
        self._unsubscribe_callback: Callable[[], None] | None = None
        self._setup_done = False
        # immediate=True writes the first update of a burst, then the last one
        self._debouncer: Debouncer[None] = Debouncer(
            self.hass,
            LOGGER,
            cooldown=debounce_interval,
            immediate=True,
            function=self._async_write_data,
        )

    @property
    def debounce_interval(self) -> float:
        """Return the minimum seconds between measurement state writes."""
        return self._debouncer.cooldown

    @debounce_interval.setter
    def debounce_interval(self, value: float) -> None:
        """Update the debounce interval in place, without a reconnect."""
        self._debouncer.cooldown = value

    @callback
    def _async_write_data(self) -> None:
        """Push the latest snapshot from the client to the entities."""
        self.async_set_updated_data(self.config_entry.runtime_data.client.data)

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
            def handle_mqtt_update(data: dict[str, Any], key: str) -> None:
                """
                Handle MQTT data updates.

                Measurement topics are rate limited by the debounce interval.
                Status, alarm and identification topics are written through
                immediately so alarm conditions are never delayed.
                """
                if self.debounce_interval and key.endswith(MQTT_MEASURES_SUFFIX):
                    self._debouncer.async_schedule_call()
                    return

                self._debouncer.async_cancel()
                self.async_set_updated_data(data)

            # Store the callback reference for later cleanup
            self._unsubscribe_callback = client.subscribe_to_updates(handle_mqtt_update)
            self._setup_done = True

        except EatonUpsClientAuthenticationError as exception:
            self.logger.exception("Authentication failed for UPS")
            raise ConfigEntryAuthFailed(exception) from exception
        except EatonUpsClientError as exception:
            self.logger.exception("Connection failed for UPS")
            raise UpdateFailed(exception) from exception

    async def async_shutdown(self) -> None:
        """Shutdown the coordinator and disconnect MQTT."""
        # Cancel any pending debounced write and release the function reference
        self._debouncer.async_shutdown()

        # Unsubscribe from MQTT updates if callback exists
        if self._unsubscribe_callback is not None:
            self._unsubscribe_callback()
            self._unsubscribe_callback = None

        # Disconnect MQTT client
        if self.config_entry.runtime_data.client:
            await self.config_entry.runtime_data.client.async_disconnect()
        await super().async_shutdown()
