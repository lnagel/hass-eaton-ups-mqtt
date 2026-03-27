"""Integration tests for component setup and lifecycle."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.issue_registry import async_get as async_get_issue_registry
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.eaton_ups_mqtt.api import EatonUpsClientCommunicationError
from custom_components.eaton_ups_mqtt.const import (
    CONF_CLIENT_CERT,
    CONF_CLIENT_KEY,
    CONF_SERVER_CERT,
    DOMAIN,
)

MOCK_SERVER_CERT = "-----BEGIN CERTIFICATE-----\nSERVER\n-----END CERTIFICATE-----"
MOCK_CLIENT_CERT = "-----BEGIN CERTIFICATE-----\nCLIENT\n-----END CERTIFICATE-----"
MOCK_CLIENT_KEY = "-----BEGIN PRIVATE KEY-----\nKEY\n-----END PRIVATE KEY-----"


@pytest.fixture
def mock_config_entry_data():
    """Return valid config entry data with certificates."""
    return {
        CONF_HOST: "ups.example.local",
        CONF_PORT: 8883,
        CONF_SERVER_CERT: MOCK_SERVER_CERT,
        CONF_CLIENT_CERT: MOCK_CLIENT_CERT,
        CONF_CLIENT_KEY: MOCK_CLIENT_KEY,
    }


@pytest.fixture
def mock_config_entry_data_no_certs():
    """Return config entry data without certificates."""
    return {
        CONF_HOST: "ups.example.local",
        CONF_PORT: 8883,
        CONF_SERVER_CERT: "",
        CONF_CLIENT_CERT: "",
        CONF_CLIENT_KEY: "",
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
def mock_entry_no_certs(mock_config_entry_data_no_certs):
    """Create a mock config entry without certificates."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Test UPS",
        data=mock_config_entry_data_no_certs,
        entry_id="test_entry_no_certs",
        unique_id="test_unique_id_no_certs",
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

    async def test_setup_auto_generates_certs(
        self,
        hass: HomeAssistant,
        mock_entry_no_certs,
        mock_mqtt_setup,
    ):
        """Test that setup auto-generates certificates when missing."""
        mock_entry_no_certs.add_to_hass(hass)

        generated_cert = "-----BEGIN CERTIFICATE-----\nGEN\n-----END CERTIFICATE-----"
        generated_key = (
            "-----BEGIN RSA PRIVATE KEY-----\nGEN\n-----END RSA PRIVATE KEY-----"
        )
        server_cert = "-----BEGIN CERTIFICATE-----\nFETCHED\n-----END CERTIFICATE-----"

        with (
            patch(
                "custom_components.eaton_ups_mqtt.async_fetch_server_certificate",
                return_value=server_cert,
            ),
            patch(
                "custom_components.eaton_ups_mqtt.async_generate_client_certificate",
                return_value=(generated_cert, generated_key),
            ),
        ):
            await hass.config_entries.async_setup(mock_entry_no_certs.entry_id)
            await hass.async_block_till_done()

        assert mock_entry_no_certs.state == ConfigEntryState.SETUP_RETRY
        assert mock_entry_no_certs.data[CONF_SERVER_CERT] == server_cert
        assert mock_entry_no_certs.data[CONF_CLIENT_CERT] == generated_cert
        assert mock_entry_no_certs.data[CONF_CLIENT_KEY] == generated_key

    async def test_setup_creates_repairs_issue_for_generated_certs(
        self,
        hass: HomeAssistant,
        mock_entry_no_certs,
        mock_mqtt_setup,
    ):
        """Test that a repairs issue is created when certs are auto-generated."""
        mock_entry_no_certs.add_to_hass(hass)

        generated_cert = "-----BEGIN CERTIFICATE-----\nGEN\n-----END CERTIFICATE-----"
        generated_key = (
            "-----BEGIN RSA PRIVATE KEY-----\nGEN\n-----END RSA PRIVATE KEY-----"
        )
        server_cert = "-----BEGIN CERTIFICATE-----\nFETCHED\n-----END CERTIFICATE-----"

        with (
            patch(
                "custom_components.eaton_ups_mqtt.async_fetch_server_certificate",
                return_value=server_cert,
            ),
            patch(
                "custom_components.eaton_ups_mqtt.async_generate_client_certificate",
                return_value=(generated_cert, generated_key),
            ),
        ):
            await hass.config_entries.async_setup(mock_entry_no_certs.entry_id)
            await hass.async_block_till_done()

        issue_registry = async_get_issue_registry(hass)
        issue_id = f"cert_upload_{mock_entry_no_certs.entry_id}"
        issue = issue_registry.async_get_issue(DOMAIN, issue_id)
        # Issue should exist — waiting for user to upload cert to UPS
        assert issue is not None
        assert issue.translation_key == "cert_upload_required"

    async def test_setup_no_repairs_issue_when_certs_exist(
        self,
        hass: HomeAssistant,
        mock_entry,
        mock_mqtt_setup,
    ):
        """Test that no repairs issue is created when certs already exist."""
        mock_entry.add_to_hass(hass)

        await hass.config_entries.async_setup(mock_entry.entry_id)
        await hass.async_block_till_done()

        issue_registry = async_get_issue_registry(hass)
        issue_id = f"cert_upload_{mock_entry.entry_id}"
        issue = issue_registry.async_get_issue(DOMAIN, issue_id)
        assert issue is None

    async def test_setup_cert_fetch_failure_raises_not_ready(
        self,
        hass: HomeAssistant,
        mock_entry_no_certs,
    ):
        """Test that server cert fetch failure raises ConfigEntryNotReady."""
        mock_entry_no_certs.add_to_hass(hass)

        with patch(
            "custom_components.eaton_ups_mqtt.async_fetch_server_certificate",
            side_effect=OSError("Connection refused"),
        ):
            await hass.config_entries.async_setup(mock_entry_no_certs.entry_id)
            await hass.async_block_till_done()

        assert mock_entry_no_certs.state == ConfigEntryState.SETUP_RETRY

    async def test_setup_mqtt_failure_raises_not_ready(
        self,
        hass: HomeAssistant,
        mock_entry,
    ):
        """Test that MQTT connection failure raises ConfigEntryNotReady."""
        mock_entry.add_to_hass(hass)

        with patch(
            "custom_components.eaton_ups_mqtt.EatonUpsMqttClient"
        ) as mock_client_class:
            mock_client = MagicMock()
            mock_client.async_setup = AsyncMock(
                side_effect=EatonUpsClientCommunicationError("Connection failed")
            )
            mock_client.async_disconnect = AsyncMock()
            mock_client.async_get_data = AsyncMock(
                side_effect=EatonUpsClientCommunicationError("Connection failed")
            )
            mock_client.subscribe_to_updates = MagicMock(return_value=lambda: None)
            mock_client_class.return_value = mock_client

            await hass.config_entries.async_setup(mock_entry.entry_id)
            await hass.async_block_till_done()

        assert mock_entry.state == ConfigEntryState.SETUP_RETRY


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

    async def test_update_listener_triggers_reload(
        self,
        hass: HomeAssistant,
        mock_entry,
        mock_mqtt_setup,
    ):
        """Test that updating entry data triggers a reload via the update listener."""
        mock_entry.add_to_hass(hass)

        await hass.config_entries.async_setup(mock_entry.entry_id)
        await hass.async_block_till_done()

        assert mock_entry.state == ConfigEntryState.LOADED

        # Update entry data to trigger the update listener
        hass.config_entries.async_update_entry(
            mock_entry, data={**mock_entry.data, CONF_HOST: "new-host.local"}
        )
        await hass.async_block_till_done()

        assert mock_entry.state == ConfigEntryState.LOADED


class TestClientCertFile:
    """Tests for client certificate file saving."""

    async def test_cert_file_saved_on_successful_setup(
        self,
        hass: HomeAssistant,
        mock_entry,
        mock_mqtt_setup,
    ):
        """Test that cert file is always saved to www/ during setup."""
        mock_entry.add_to_hass(hass)

        await hass.config_entries.async_setup(mock_entry.entry_id)
        await hass.async_block_till_done()

        cert_path = Path(
            hass.config.path(
                "www",
                DOMAIN,
                f"eaton_ups_client_{mock_entry.entry_id}.pem",
            )
        )
        assert cert_path.exists()
        assert cert_path.read_text() == MOCK_CLIENT_CERT

    async def test_cert_file_saved_on_cert_generation(
        self,
        hass: HomeAssistant,
        mock_entry_no_certs,
        mock_mqtt_setup,
    ):
        """Test that cert file is saved when certs are auto-generated."""
        mock_entry_no_certs.add_to_hass(hass)

        generated_cert = "-----BEGIN CERTIFICATE-----\nGEN\n-----END CERTIFICATE-----"
        generated_key = (
            "-----BEGIN RSA PRIVATE KEY-----\nGEN\n-----END RSA PRIVATE KEY-----"
        )
        server_cert = "-----BEGIN CERTIFICATE-----\nFETCHED\n-----END CERTIFICATE-----"

        with (
            patch(
                "custom_components.eaton_ups_mqtt.async_fetch_server_certificate",
                return_value=server_cert,
            ),
            patch(
                "custom_components.eaton_ups_mqtt.async_generate_client_certificate",
                return_value=(generated_cert, generated_key),
            ),
        ):
            await hass.config_entries.async_setup(mock_entry_no_certs.entry_id)
            await hass.async_block_till_done()

        cert_path = Path(
            hass.config.path(
                "www",
                DOMAIN,
                f"eaton_ups_client_{mock_entry_no_certs.entry_id}.pem",
            )
        )
        assert cert_path.exists()
        assert cert_path.read_text() == generated_cert
