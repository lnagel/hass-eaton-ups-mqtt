"""Shared fixtures for Eaton UPS MQTT tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.eaton_ups_mqtt.const import DOMAIN

if TYPE_CHECKING:
    from collections.abc import Generator

# Register pytest-homeassistant-custom-component plugin
pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for all tests."""
    return


# Path to fixtures directory
FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def ups_5px_g2_data() -> dict[str, Any]:
    """Load 5PX G2 fixture data (just the MQTT data portion)."""
    fixture_path = FIXTURES_DIR / "mqtt_data_5px_g2.json"
    with fixture_path.open() as f:
        return json.load(f)["data"]


@pytest.fixture
def ups_5px_g2_full() -> dict[str, Any]:
    """Load full 5PX G2 fixture including metadata."""
    fixture_path = FIXTURES_DIR / "mqtt_data_5px_g2.json"
    with fixture_path.open() as f:
        return json.load(f)


@pytest.fixture
def mock_mqtt_client() -> Generator[MagicMock]:
    """Mock paho MQTT client."""
    with patch("paho.mqtt.client.Client") as mock_client_class:
        mock_instance = MagicMock()
        mock_instance.connect_async = MagicMock()
        mock_instance.loop_start = MagicMock()
        mock_instance.loop_stop = MagicMock()
        mock_instance.disconnect = MagicMock()
        mock_instance.subscribe = MagicMock()
        mock_instance.tls_set = MagicMock()
        mock_instance.tls_insecure_set = MagicMock()
        mock_instance.reconnect_delay_set = MagicMock()
        mock_client_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_config_entry() -> MagicMock:
    """Create a mock config entry."""
    entry = MagicMock()
    entry.entry_id = "test_entry_id"
    entry.domain = DOMAIN
    entry.title = "Test UPS"
    entry.data = {
        "host": "ups.example.local",
        "port": "8883",
        "server_cert": "-----BEGIN CERTIFICATE-----\ntest\n-----END CERTIFICATE-----",
        "client_cert": "-----BEGIN CERTIFICATE-----\ntest\n-----END CERTIFICATE-----",
        "client_key": "-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----",
    }
    entry.options = {}
    entry.unique_id = "test_unique_id"
    return entry


@pytest.fixture
def mock_api_client(ups_5px_g2_data: dict[str, Any]) -> MagicMock:
    """Create a mock API client with pre-loaded data."""
    client = MagicMock()
    client._mqtt_data = ups_5px_g2_data
    client._mqtt_connected = True
    client.async_setup = AsyncMock()
    client.async_disconnect = AsyncMock()
    client.async_get_data = AsyncMock(return_value=ups_5px_g2_data)
    client.subscribe_to_updates = MagicMock(return_value=MagicMock())
    return client
