"""Integration tests for component setup and lifecycle."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.eaton_ups_mqtt.const import (
    CONF_CLIENT_CERT,
    CONF_CLIENT_KEY,
    CONF_SERVER_CERT,
    DOMAIN,
)


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


@pytest.fixture
def mock_mqtt_setup(ups_5px_g2_data):
    """Mock the MQTT client to prevent actual network connections."""
    with patch(
        "custom_components.eaton_ups_mqtt.EatonUpsMqttClient"
    ) as mock_client_class:
        mock_client = MagicMock()
        mock_client.async_setup = AsyncMock()
        mock_client.async_disconnect = AsyncMock()
        mock_client.async_get_data = AsyncMock(return_value=ups_5px_g2_data)
        mock_client.subscribe_to_updates = MagicMock(return_value=lambda: None)
        mock_client_class.return_value = mock_client

        yield mock_client


class TestSetupEntry:
    """Tests for async_setup_entry."""

    async def test_setup_entry_success(
        self,
        hass: HomeAssistant,
        mock_entry,
        mock_mqtt_setup,
    ):
        """Test successful setup of config entry."""
        mock_entry.add_to_hass(hass)

        await hass.config_entries.async_setup(mock_entry.entry_id)
        await hass.async_block_till_done()

        assert mock_entry.state == ConfigEntryState.LOADED
        mock_mqtt_setup.async_setup.assert_called()

    async def test_setup_creates_runtime_data(
        self,
        hass: HomeAssistant,
        mock_entry,
        mock_mqtt_setup,
    ):
        """Test that setup creates runtime_data with client and coordinator."""
        mock_entry.add_to_hass(hass)

        await hass.config_entries.async_setup(mock_entry.entry_id)
        await hass.async_block_till_done()

        assert mock_entry.state == ConfigEntryState.LOADED
        assert mock_entry.runtime_data is not None
        assert mock_entry.runtime_data.coordinator is not None


class TestUnloadEntry:
    """Tests for async_unload_entry."""

    async def test_unload_entry_success(
        self,
        hass: HomeAssistant,
        mock_entry,
        mock_mqtt_setup,
    ):
        """Test successful unload of config entry."""
        mock_entry.add_to_hass(hass)

        await hass.config_entries.async_setup(mock_entry.entry_id)
        await hass.async_block_till_done()

        assert mock_entry.state == ConfigEntryState.LOADED

        await hass.config_entries.async_unload(mock_entry.entry_id)
        await hass.async_block_till_done()

        assert mock_entry.state == ConfigEntryState.NOT_LOADED


class TestReloadEntry:
    """Tests for async_reload_entry."""

    async def test_reload_entry(
        self,
        hass: HomeAssistant,
        mock_entry,
        mock_mqtt_setup,
    ):
        """Test reloading a config entry."""
        mock_entry.add_to_hass(hass)

        await hass.config_entries.async_setup(mock_entry.entry_id)
        await hass.async_block_till_done()

        assert mock_entry.state == ConfigEntryState.LOADED

        # Reload
        await hass.config_entries.async_reload(mock_entry.entry_id)
        await hass.async_block_till_done()

        assert mock_entry.state == ConfigEntryState.LOADED
