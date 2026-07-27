"""Integration tests for data update coordinator."""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import timedelta
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import UpdateFailed
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)

from custom_components.eaton_ups_mqtt.api import (
    EatonUpsClientAuthenticationError,
    EatonUpsClientError,
)
from custom_components.eaton_ups_mqtt.const import (
    CONF_CLIENT_CERT,
    CONF_CLIENT_KEY,
    CONF_DEBOUNCE_INTERVAL,
    CONF_SERVER_CERT,
    DEFAULT_DEBOUNCE_INTERVAL,
    DOMAIN,
)
from custom_components.eaton_ups_mqtt.coordinator import EatonUPSDataUpdateCoordinator

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Callable


@pytest.fixture
def mock_config_entry_data():
    """Return valid config entry data."""
    return {
        CONF_HOST: "ups.example.local",
        CONF_PORT: "8883",
        CONF_SERVER_CERT: "-----BEGIN CERTIFICATE-----\nSERVER\n-----END CERTIFICATE-----",
        CONF_CLIENT_CERT: "-----BEGIN CERTIFICATE-----\nCLIENT\n-----END CERTIFICATE-----",
        CONF_CLIENT_KEY: "-----BEGIN PRIVATE KEY-----\nKEY\n-----END PRIVATE KEY-----",
    }


@pytest.fixture
def mock_entry(mock_config_entry_data):
    """Create a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Test UPS",
        data=mock_config_entry_data,
        entry_id="test_entry_id",
        unique_id="test_unique_id",
    )


class TestCoordinatorSetup:
    """Tests for coordinator setup and data fetching."""

    async def test_coordinator_init(self, hass: HomeAssistant):
        """Test coordinator initializes with correct defaults."""
        coordinator = EatonUPSDataUpdateCoordinator(
            hass=hass,
            logger=MagicMock(),
            name=DOMAIN,
        )

        assert coordinator.update_interval is None
        assert coordinator._setup_done is False

    async def test_coordinator_data_callback(
        self, hass: HomeAssistant, mock_entry, ups_5px_g2_data
    ):
        """Test that MQTT data callback updates coordinator data."""
        mock_entry.add_to_hass(hass)

        with patch(
            "custom_components.eaton_ups_mqtt.EatonUpsMqttClient"
        ) as mock_client_class:
            mock_client = MagicMock()
            mock_client.async_setup = AsyncMock()
            mock_client.async_disconnect = AsyncMock()
            mock_client.async_get_data = AsyncMock(return_value=ups_5px_g2_data)

            # Capture the callback when subscribe_to_updates is called
            callback_holder = {}

            def capture_callback(cb):
                callback_holder["callback"] = cb
                return lambda: None

            mock_client.subscribe_to_updates = MagicMock(side_effect=capture_callback)
            mock_client_class.return_value = mock_client

            await hass.config_entries.async_setup(mock_entry.entry_id)
            await hass.async_block_till_done()

            # Verify callback was registered
            assert "callback" in callback_holder

            # Simulate MQTT update via callback
            new_data = {"test": "new_data"}
            callback_holder["callback"](new_data, "powerDistributions/1/status")
            await hass.async_block_till_done()

            # Verify coordinator received the data
            coordinator = mock_entry.runtime_data.coordinator
            assert coordinator.data == new_data


class TestCoordinatorErrorHandling:
    """Tests for coordinator error handling."""

    @pytest.mark.parametrize(
        ("exception", "expected_exception"),
        [
            (EatonUpsClientAuthenticationError("Auth failed"), ConfigEntryAuthFailed),
            (EatonUpsClientError("Client error"), UpdateFailed),
        ],
    )
    async def test_setup_error_handling(
        self, hass: HomeAssistant, mock_entry, exception, expected_exception
    ):
        """Test coordinator handles setup errors correctly."""
        mock_entry.add_to_hass(hass)

        with patch(
            "custom_components.eaton_ups_mqtt.EatonUpsMqttClient"
        ) as mock_client_class:
            mock_client = MagicMock()
            mock_client.async_setup = AsyncMock(side_effect=exception)
            mock_client.async_disconnect = AsyncMock()
            mock_client_class.return_value = mock_client

            # Setup will fail due to the exception - entry goes to SETUP_RETRY
            await hass.config_entries.async_setup(mock_entry.entry_id)
            await hass.async_block_till_done()

            # Verify async_setup was called and raised
            mock_client.async_setup.assert_called()


class TestCoordinatorShutdown:
    """Tests for coordinator shutdown."""

    async def test_coordinator_shutdown_unsubscribes(
        self, hass: HomeAssistant, mock_entry, ups_5px_g2_data
    ):
        """Test that shutdown unsubscribes from updates."""
        mock_entry.add_to_hass(hass)

        unsubscribe_called = {"value": False}

        def mock_unsubscribe():
            unsubscribe_called["value"] = True

        with patch(
            "custom_components.eaton_ups_mqtt.EatonUpsMqttClient"
        ) as mock_client_class:
            mock_client = MagicMock()
            mock_client.async_setup = AsyncMock()
            mock_client.async_disconnect = AsyncMock()
            mock_client.async_get_data = AsyncMock(return_value=ups_5px_g2_data)
            mock_client.subscribe_to_updates = MagicMock(return_value=mock_unsubscribe)
            mock_client_class.return_value = mock_client

            await hass.config_entries.async_setup(mock_entry.entry_id)
            await hass.async_block_till_done()

            coordinator = mock_entry.runtime_data.coordinator

            # Call shutdown
            await coordinator.async_shutdown()

            # Verify unsubscribe was called
            assert unsubscribe_called["value"] is True
            mock_client.async_disconnect.assert_called()

    async def test_coordinator_shutdown_handles_no_callback(
        self, hass: HomeAssistant, mock_entry, ups_5px_g2_data
    ):
        """Test shutdown handles case where no callback was registered."""
        mock_entry.add_to_hass(hass)

        with patch(
            "custom_components.eaton_ups_mqtt.EatonUpsMqttClient"
        ) as mock_client_class:
            mock_client = MagicMock()
            mock_client.async_setup = AsyncMock()
            mock_client.async_disconnect = AsyncMock()
            mock_client.async_get_data = AsyncMock(return_value=ups_5px_g2_data)
            mock_client.subscribe_to_updates = MagicMock(return_value=None)
            mock_client_class.return_value = mock_client

            await hass.config_entries.async_setup(mock_entry.entry_id)
            await hass.async_block_till_done()

            coordinator = mock_entry.runtime_data.coordinator
            coordinator._unsubscribe_callback = None

            # Should not raise
            await coordinator.async_shutdown()
            mock_client.async_disconnect.assert_called()


MEASURES_KEY = "powerDistributions/1/outputs/1/measures"
STATUS_KEY = "powerDistributions/1/status"


@asynccontextmanager
async def _debounced_coordinator(
    hass: HomeAssistant,
    entry: MockConfigEntry,
    data: dict,
) -> AsyncGenerator[tuple[EatonUPSDataUpdateCoordinator, Callable, MagicMock]]:
    """Set up the entry with a mocked client and yield the update callback."""
    entry.add_to_hass(hass)

    with patch(
        "custom_components.eaton_ups_mqtt.EatonUpsMqttClient"
    ) as mock_client_class:
        mock_client = MagicMock()
        mock_client.async_setup = AsyncMock()
        mock_client.async_disconnect = AsyncMock()
        mock_client.async_get_data = AsyncMock(return_value=data)
        mock_client.data = data

        captured = {}

        def capture_callback(cb):
            captured["callback"] = cb
            return lambda: None

        mock_client.subscribe_to_updates = MagicMock(side_effect=capture_callback)
        mock_client_class.return_value = mock_client

        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        yield entry.runtime_data.coordinator, captured["callback"], mock_client


def _entry_with_interval(
    mock_config_entry_data: dict, interval: int
) -> MockConfigEntry:
    """Build a config entry with the given debounce interval."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Test UPS",
        data=mock_config_entry_data,
        options={CONF_DEBOUNCE_INTERVAL: interval},
        entry_id="test_entry_id",
        unique_id="test_unique_id",
    )


class TestCoordinatorDebounce:
    """Tests for debounced measurement updates."""

    async def test_default_interval_from_options(
        self, hass: HomeAssistant, mock_config_entry_data, ups_5px_g2_data
    ):
        """Test the debounce interval is read from the config entry options."""
        entry = _entry_with_interval(mock_config_entry_data, 30)

        async with _debounced_coordinator(hass, entry, ups_5px_g2_data) as (
            coordinator,
            _callback,
            _client,
        ):
            assert coordinator.debounce_interval == 30

    async def test_falls_back_to_default_without_options(
        self, hass: HomeAssistant, mock_entry, ups_5px_g2_data
    ):
        """Test the default interval applies when no option is stored."""
        async with _debounced_coordinator(hass, mock_entry, ups_5px_g2_data) as (
            coordinator,
            _callback,
            _client,
        ):
            assert coordinator.debounce_interval == DEFAULT_DEBOUNCE_INTERVAL

    async def test_first_measures_update_is_immediate(
        self, hass: HomeAssistant, mock_config_entry_data, ups_5px_g2_data
    ):
        """Test the first measurement update after a quiet period is written."""
        entry = _entry_with_interval(mock_config_entry_data, 10)

        async with _debounced_coordinator(hass, entry, ups_5px_g2_data) as (
            coordinator,
            callback,
            client,
        ):
            listener = MagicMock()
            coordinator.async_add_listener(listener)

            client.data = {"first": 1}
            callback(client.data, MEASURES_KEY)
            await hass.async_block_till_done()

            assert coordinator.data == {"first": 1}
            assert listener.call_count == 1

    async def test_measures_updates_are_coalesced(
        self, hass: HomeAssistant, mock_config_entry_data, ups_5px_g2_data
    ):
        """Test updates within the cooldown are coalesced into one write."""
        entry = _entry_with_interval(mock_config_entry_data, 10)

        async with _debounced_coordinator(hass, entry, ups_5px_g2_data) as (
            coordinator,
            callback,
            client,
        ):
            client.data = {"value": 1}
            callback(client.data, MEASURES_KEY)
            await hass.async_block_till_done()

            listener = MagicMock()
            coordinator.async_add_listener(listener)

            for value in (2, 3, 4):
                client.data = {"value": value}
                callback(client.data, MEASURES_KEY)
                await hass.async_block_till_done()

            # Still inside the cooldown, so nothing further was written
            assert listener.call_count == 0
            assert coordinator.data == {"value": 1}

            async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=15))
            await hass.async_block_till_done()

            # The final value of the burst is written when the cooldown ends
            assert listener.call_count == 1
            assert coordinator.data == {"value": 4}

    async def test_status_topic_bypasses_debounce(
        self, hass: HomeAssistant, mock_config_entry_data, ups_5px_g2_data
    ):
        """Test status topics are written immediately despite a pending burst."""
        entry = _entry_with_interval(mock_config_entry_data, 60)

        async with _debounced_coordinator(hass, entry, ups_5px_g2_data) as (
            coordinator,
            callback,
            client,
        ):
            client.data = {"value": 1}
            callback(client.data, MEASURES_KEY)
            await hass.async_block_till_done()

            client.data = {"value": 2}
            callback(client.data, MEASURES_KEY)
            await hass.async_block_till_done()
            assert coordinator.data == {"value": 1}

            alarm = {"alarm": True}
            callback(alarm, STATUS_KEY)
            await hass.async_block_till_done()

            assert coordinator.data == alarm

    async def test_zero_interval_disables_debounce(
        self, hass: HomeAssistant, mock_config_entry_data, ups_5px_g2_data
    ):
        """Test an interval of 0 writes every measurement update."""
        entry = _entry_with_interval(mock_config_entry_data, 0)

        async with _debounced_coordinator(hass, entry, ups_5px_g2_data) as (
            coordinator,
            callback,
            _client,
        ):
            listener = MagicMock()
            coordinator.async_add_listener(listener)

            for value in (1, 2, 3):
                data = {"value": value}
                callback(data, MEASURES_KEY)
                await hass.async_block_till_done()
                assert coordinator.data == data

            assert listener.call_count == 3

    async def test_interval_can_be_changed_at_runtime(
        self, hass: HomeAssistant, mock_config_entry_data, ups_5px_g2_data
    ):
        """Test the interval setter takes effect without a reconnect."""
        entry = _entry_with_interval(mock_config_entry_data, 10)

        async with _debounced_coordinator(hass, entry, ups_5px_g2_data) as (
            coordinator,
            callback,
            _client,
        ):
            coordinator.debounce_interval = 0
            assert coordinator.debounce_interval == 0

            for value in (1, 2):
                data = {"value": value}
                callback(data, MEASURES_KEY)
                await hass.async_block_till_done()
                assert coordinator.data == data

    async def test_shutdown_cancels_pending_write(
        self, hass: HomeAssistant, mock_config_entry_data, ups_5px_g2_data
    ):
        """Test a pending debounced write is dropped on shutdown."""
        entry = _entry_with_interval(mock_config_entry_data, 10)

        async with _debounced_coordinator(hass, entry, ups_5px_g2_data) as (
            coordinator,
            callback,
            client,
        ):
            client.data = {"value": 1}
            callback(client.data, MEASURES_KEY)
            await hass.async_block_till_done()

            client.data = {"value": 2}
            callback(client.data, MEASURES_KEY)
            await hass.async_block_till_done()

            await coordinator.async_shutdown()

            async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=15))
            await hass.async_block_till_done()

            assert coordinator.data == {"value": 1}
