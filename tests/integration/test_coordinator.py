"""Integration tests for data update coordinator."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import UpdateFailed
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.eaton_ups_mqtt.api import (
    EatonUpsClientAuthenticationError,
    EatonUpsClientError,
)
from custom_components.eaton_ups_mqtt.const import (
    CONF_CLIENT_CERT,
    CONF_CLIENT_KEY,
    CONF_SERVER_CERT,
    DOMAIN,
)
from custom_components.eaton_ups_mqtt.coordinator import EatonUPSDataUpdateCoordinator


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
            callback_holder["callback"](new_data)
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
