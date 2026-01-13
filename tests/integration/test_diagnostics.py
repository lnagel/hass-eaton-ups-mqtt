"""Integration tests for diagnostics."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.eaton_ups_mqtt.const import (
    CONF_CLIENT_CERT,
    CONF_CLIENT_KEY,
    CONF_SERVER_CERT,
    DOMAIN,
)
from custom_components.eaton_ups_mqtt.diagnostics import (
    async_get_config_entry_diagnostics,
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


async def test_diagnostics_returns_redacted_data(
    hass: HomeAssistant, mock_entry, ups_5px_g2_data
):
    """Test diagnostics returns properly redacted data."""
    mock_entry.add_to_hass(hass)

    with patch(
        "custom_components.eaton_ups_mqtt.EatonUpsMqttClient"
    ) as mock_client_class:
        mock_client = MagicMock()
        mock_client.async_setup = AsyncMock()
        mock_client.async_disconnect = AsyncMock()
        mock_client.async_get_data = AsyncMock(return_value=ups_5px_g2_data)
        mock_client.subscribe_to_updates = MagicMock(return_value=lambda: None)
        mock_client_class.return_value = mock_client

        await hass.config_entries.async_setup(mock_entry.entry_id)
        await hass.async_block_till_done()

        result = await async_get_config_entry_diagnostics(hass, mock_entry)

    # Check structure
    assert "config_entry" in result
    assert "mqtt_prefix" in result
    assert "coordinator_data" in result

    # Check config_entry has redacted certs
    config_data = result["config_entry"]["data"]
    assert config_data[CONF_SERVER_CERT] == "**REDACTED**"
    assert config_data[CONF_CLIENT_CERT] == "**REDACTED**"
    assert config_data[CONF_CLIENT_KEY] == "**REDACTED**"
    assert config_data[CONF_HOST] == "ups.example.local"  # Not redacted


async def test_diagnostics_redacts_serial_numbers(
    hass: HomeAssistant, mock_entry, ups_5px_g2_data
):
    """Test diagnostics redacts serial numbers in coordinator data."""
    mock_entry.add_to_hass(hass)

    with patch(
        "custom_components.eaton_ups_mqtt.EatonUpsMqttClient"
    ) as mock_client_class:
        mock_client = MagicMock()
        mock_client.async_setup = AsyncMock()
        mock_client.async_disconnect = AsyncMock()
        mock_client.async_get_data = AsyncMock(return_value=ups_5px_g2_data)
        mock_client.subscribe_to_updates = MagicMock(return_value=lambda: None)
        mock_client_class.return_value = mock_client

        await hass.config_entries.async_setup(mock_entry.entry_id)
        await hass.async_block_till_done()

        result = await async_get_config_entry_diagnostics(hass, mock_entry)

    # Check that serial numbers are redacted in coordinator data
    coord_data = result["coordinator_data"]
    if "managers/1/identification" in coord_data:
        assert coord_data["managers/1/identification"]["serialNumber"] == "**REDACTED**"
