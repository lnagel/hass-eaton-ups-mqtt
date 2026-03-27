"""Integration tests for config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.eaton_ups_mqtt.api import (
    EatonUpsClientAuthenticationError,
    EatonUpsClientCommunicationError,
    EatonUpsClientError,
)
from custom_components.eaton_ups_mqtt.config_flow import ConnectionResult
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
def valid_user_input():
    """Return valid user input for config flow (host + port only)."""
    return {
        CONF_HOST: "ups.example.local",
        CONF_PORT: 8883,
    }


@pytest.fixture
def full_entry_data():
    """Return full config entry data with certificates."""
    return {
        CONF_HOST: "ups.example.local",
        CONF_PORT: 8883,
        CONF_SERVER_CERT: MOCK_SERVER_CERT,
        CONF_CLIENT_CERT: MOCK_CLIENT_CERT,
        CONF_CLIENT_KEY: MOCK_CLIENT_KEY,
    }


@pytest.fixture
def mock_identification():
    """Return mock UPS identification data."""
    return {"macAddress": "00:11:22:33:44:55", "modelName": "5PX 1500i RT2U G2"}


class TestUserFlow:
    """Tests for user config flow."""

    async def test_form_display(self, hass: HomeAssistant):
        """Test that user form displays correct fields (host + port only)."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "user"
        assert result["errors"] == {}

    async def test_successful_setup(self, hass: HomeAssistant, valid_user_input):
        """Test successful config entry creation with host + port only."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], valid_user_input
        )

        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["title"] == valid_user_input[CONF_HOST]
        assert result["data"][CONF_HOST] == valid_user_input[CONF_HOST]
        assert result["data"][CONF_PORT] == valid_user_input[CONF_PORT]
        # Cert fields should be empty (will be auto-generated during setup)
        assert result["data"][CONF_SERVER_CERT] == ""
        assert result["data"][CONF_CLIENT_CERT] == ""
        assert result["data"][CONF_CLIENT_KEY] == ""


class TestReauthFlow:
    """Tests for reauth flow."""

    async def test_reauth_form_display(self, hass: HomeAssistant, full_entry_data):
        """Test that reauth form displays with current values."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="Test UPS",
            data=full_entry_data,
            unique_id="00:11:22:33:44:55",
        )
        entry.add_to_hass(hass)

        result = await entry.start_reauth_flow(hass)

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "reauth_confirm"

    async def test_reauth_success_with_certs(
        self, hass: HomeAssistant, full_entry_data
    ):
        """Test successful reauthentication with provided certs."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="Test UPS",
            data=full_entry_data,
            unique_id="00:11:22:33:44:55",
        )
        entry.add_to_hass(hass)

        updated_input = {
            CONF_HOST: "ups.example.local",
            CONF_PORT: 8883,
            CONF_SERVER_CERT: MOCK_SERVER_CERT,
            CONF_CLIENT_CERT: MOCK_CLIENT_CERT,
            CONF_CLIENT_KEY: "-----BEGIN PRIVATE KEY-----\nNEWKEY\n-----END PRIVATE KEY-----",
        }

        with patch(
            "custom_components.eaton_ups_mqtt.config_flow.EatonUpsFlowHandler._test_credentials",
            new_callable=AsyncMock,
        ):
            result = await entry.start_reauth_flow(hass)
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], updated_input
            )

        assert result["type"] == FlowResultType.ABORT
        assert result["reason"] == "reauth_successful"
        assert entry.data[CONF_CLIENT_KEY] == updated_input[CONF_CLIENT_KEY]

    async def test_reauth_auto_generates_cleared_certs(
        self, hass: HomeAssistant, full_entry_data
    ):
        """Test that clearing cert fields triggers auto-generation."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="Test UPS",
            data=full_entry_data,
            unique_id="00:11:22:33:44:55",
        )
        entry.add_to_hass(hass)

        # Submit with empty cert fields (simulates user clearing the fields)
        input_with_cleared_certs = {
            CONF_HOST: "ups.example.local",
            CONF_PORT: 8883,
            CONF_SERVER_CERT: "",
            CONF_CLIENT_CERT: "",
            CONF_CLIENT_KEY: "",
        }

        generated_cert = "-----BEGIN CERTIFICATE-----\nGEN\n-----END CERTIFICATE-----"
        generated_key = (
            "-----BEGIN RSA PRIVATE KEY-----\nGEN\n-----END RSA PRIVATE KEY-----"
        )
        server_cert = "-----BEGIN CERTIFICATE-----\nFETCHED\n-----END CERTIFICATE-----"

        with (
            patch(
                "custom_components.eaton_ups_mqtt.config_flow.async_fetch_server_certificate",
                return_value=server_cert,
            ),
            patch(
                "custom_components.eaton_ups_mqtt.config_flow.async_generate_client_certificate",
                return_value=(generated_cert, generated_key),
            ),
            patch(
                "custom_components.eaton_ups_mqtt.config_flow.EatonUpsFlowHandler._test_credentials",
                new_callable=AsyncMock,
            ),
        ):
            result = await entry.start_reauth_flow(hass)
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], input_with_cleared_certs
            )

        assert result["type"] == FlowResultType.ABORT
        assert result["reason"] == "reauth_successful"
        assert entry.data[CONF_SERVER_CERT] == server_cert
        assert entry.data[CONF_CLIENT_CERT] == generated_cert
        assert entry.data[CONF_CLIENT_KEY] == generated_key

    async def test_reauth_cert_fetch_failed(self, hass: HomeAssistant, full_entry_data):
        """Test error when cert fetch fails during reauth."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="Test UPS",
            data=full_entry_data,
            unique_id="00:11:22:33:44:55",
        )
        entry.add_to_hass(hass)

        input_with_cleared_certs = {
            CONF_HOST: "ups.example.local",
            CONF_PORT: 8883,
            CONF_SERVER_CERT: "",
            CONF_CLIENT_CERT: "",
            CONF_CLIENT_KEY: "",
        }

        with patch(
            "custom_components.eaton_ups_mqtt.config_flow.async_fetch_server_certificate",
            side_effect=OSError("Connection refused"),
        ):
            result = await entry.start_reauth_flow(hass)
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], input_with_cleared_certs
            )

        assert result["type"] == FlowResultType.FORM
        assert result["errors"]["base"] == "cert_fetch_failed"

    @pytest.mark.parametrize(
        ("exception", "error_key"),
        [
            (EatonUpsClientAuthenticationError("Auth failed"), "auth"),
            (EatonUpsClientCommunicationError("Connection failed"), "connection"),
            (EatonUpsClientError("Unknown error"), "unknown"),
        ],
    )
    async def test_reauth_error_handling(
        self, hass: HomeAssistant, full_entry_data, exception, error_key
    ):
        """Test reauth error handling for various failure modes."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="Test UPS",
            data=full_entry_data,
            unique_id="00:11:22:33:44:55",
        )
        entry.add_to_hass(hass)

        with patch(
            "custom_components.eaton_ups_mqtt.config_flow.EatonUpsFlowHandler._test_credentials",
            new_callable=AsyncMock,
            side_effect=exception,
        ):
            result = await entry.start_reauth_flow(hass)
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], full_entry_data
            )

        assert result["type"] == FlowResultType.FORM
        assert result["errors"]["base"] == error_key


class TestReconfigureFlow:
    """Tests for reconfigure flow."""

    async def test_reconfigure_form_display(self, hass: HomeAssistant, full_entry_data):
        """Test that reconfigure form displays with current values."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="Test UPS",
            data=full_entry_data,
            unique_id="00:11:22:33:44:55",
        )
        entry.add_to_hass(hass)

        result = await entry.start_reconfigure_flow(hass)

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "reconfigure"

    async def test_reconfigure_success(
        self, hass: HomeAssistant, full_entry_data, mock_identification
    ):
        """Test successful reconfiguration."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="Test UPS",
            data=full_entry_data,
            unique_id="00:11:22:33:44:55",
        )
        entry.add_to_hass(hass)

        updated_input = {**full_entry_data, CONF_HOST: "new-ups.example.local"}

        with (
            patch(
                "custom_components.eaton_ups_mqtt.config_flow.try_connection",
                return_value=ConnectionResult(identification=mock_identification),
            ),
            patch(
                "custom_components.eaton_ups_mqtt.async_setup_entry",
                return_value=True,
            ),
        ):
            result = await entry.start_reconfigure_flow(hass)
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], updated_input
            )

        assert result["type"] == FlowResultType.ABORT
        assert result["reason"] == "reconfigure_successful"
        assert entry.data[CONF_HOST] == "new-ups.example.local"

    @pytest.mark.parametrize(
        ("error_key", "error_detail"),
        [
            ("host_unreachable", "No route to host"),
            ("connection_refused", "Connection refused"),
            ("connection_timeout", "Connection timed out"),
            ("server_cert_mismatch", "Server certificate verification failed"),
            ("tls_handshake_failed", "TLS handshake failed"),
            ("mqtt_connect_refused", "MQTT broker refused connection"),
            ("no_data_received", "No identification data received"),
            ("invalid_response", "UPS returned invalid JSON"),
        ],
    )
    async def test_reconfigure_connection_errors(
        self, hass: HomeAssistant, full_entry_data, error_key, error_detail
    ):
        """Test reconfigure with specific connection error types."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="Test UPS",
            data=full_entry_data,
            unique_id="00:11:22:33:44:55",
        )
        entry.add_to_hass(hass)

        with patch(
            "custom_components.eaton_ups_mqtt.config_flow.try_connection",
            return_value=ConnectionResult(
                error_key=error_key, error_detail=error_detail
            ),
        ):
            result = await entry.start_reconfigure_flow(hass)
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], full_entry_data
            )

        assert result["type"] == FlowResultType.FORM
        assert result["errors"]["base"] == error_key

    async def test_reconfigure_auto_generates_cleared_certs(
        self, hass: HomeAssistant, full_entry_data, mock_identification
    ):
        """Test that clearing cert fields in reconfigure triggers auto-generation."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="Test UPS",
            data=full_entry_data,
            unique_id="00:11:22:33:44:55",
        )
        entry.add_to_hass(hass)

        input_with_cleared_certs = {
            CONF_HOST: "ups.example.local",
            CONF_PORT: 8883,
            CONF_SERVER_CERT: "",
            CONF_CLIENT_CERT: "",
            CONF_CLIENT_KEY: "",
        }

        generated_cert = "-----BEGIN CERTIFICATE-----\nGEN\n-----END CERTIFICATE-----"
        generated_key = (
            "-----BEGIN RSA PRIVATE KEY-----\nGEN\n-----END RSA PRIVATE KEY-----"
        )
        server_cert = "-----BEGIN CERTIFICATE-----\nFETCHED\n-----END CERTIFICATE-----"

        with (
            patch(
                "custom_components.eaton_ups_mqtt.config_flow.async_fetch_server_certificate",
                return_value=server_cert,
            ),
            patch(
                "custom_components.eaton_ups_mqtt.config_flow.async_generate_client_certificate",
                return_value=(generated_cert, generated_key),
            ),
            patch(
                "custom_components.eaton_ups_mqtt.config_flow.try_connection",
                return_value=ConnectionResult(identification=mock_identification),
            ),
            patch(
                "custom_components.eaton_ups_mqtt.async_setup_entry",
                return_value=True,
            ),
        ):
            result = await entry.start_reconfigure_flow(hass)
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], input_with_cleared_certs
            )

        assert result["type"] == FlowResultType.ABORT
        assert result["reason"] == "reconfigure_successful"
        assert entry.data[CONF_SERVER_CERT] == server_cert
        assert entry.data[CONF_CLIENT_CERT] == generated_cert
        assert entry.data[CONF_CLIENT_KEY] == generated_key

    async def test_reconfigure_cert_fetch_failed(
        self, hass: HomeAssistant, full_entry_data
    ):
        """Test error when cert fetch fails during reconfigure."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="Test UPS",
            data=full_entry_data,
            unique_id="00:11:22:33:44:55",
        )
        entry.add_to_hass(hass)

        input_with_cleared_certs = {
            CONF_HOST: "ups.example.local",
            CONF_PORT: 8883,
            CONF_SERVER_CERT: "",
            CONF_CLIENT_CERT: "",
            CONF_CLIENT_KEY: "",
        }

        with patch(
            "custom_components.eaton_ups_mqtt.config_flow.async_fetch_server_certificate",
            side_effect=TimeoutError("Timed out"),
        ):
            result = await entry.start_reconfigure_flow(hass)
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], input_with_cleared_certs
            )

        assert result["type"] == FlowResultType.FORM
        assert result["errors"]["base"] == "cert_fetch_failed"
