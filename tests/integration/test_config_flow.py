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
from custom_components.eaton_ups_mqtt.const import (
    CONF_CLIENT_CERT,
    CONF_CLIENT_KEY,
    CONF_SERVER_CERT,
    DOMAIN,
)


@pytest.fixture
def valid_user_input():
    """Return valid user input for config flow."""
    return {
        CONF_HOST: "ups.example.local",
        CONF_PORT: 8883,
        CONF_SERVER_CERT: "-----BEGIN CERTIFICATE-----\nSERVER\n-----END CERTIFICATE-----",
        CONF_CLIENT_CERT: "-----BEGIN CERTIFICATE-----\nCLIENT\n-----END CERTIFICATE-----",
        CONF_CLIENT_KEY: "-----BEGIN PRIVATE KEY-----\nKEY\n-----END PRIVATE KEY-----",
    }


@pytest.fixture
def mock_identification():
    """Return mock UPS identification data."""
    return {"macAddress": "00:11:22:33:44:55", "modelName": "5PX 1500i RT2U G2"}


class TestUserFlow:
    """Tests for user config flow."""

    async def test_form_display(self, hass: HomeAssistant):
        """Test that user form displays correct fields."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "user"
        assert result["errors"] == {}

    async def test_successful_setup(
        self, hass: HomeAssistant, valid_user_input, mock_identification
    ):
        """Test successful config entry creation."""
        with (
            patch(
                "custom_components.eaton_ups_mqtt.config_flow.EatonUpsFlowHandler._test_credentials",
                new_callable=AsyncMock,
            ),
            patch(
                "custom_components.eaton_ups_mqtt.config_flow.try_connection",
                return_value=mock_identification,
            ),
        ):
            result = await hass.config_entries.flow.async_init(
                DOMAIN, context={"source": config_entries.SOURCE_USER}
            )
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], valid_user_input
            )

        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["title"] == valid_user_input[CONF_HOST]
        assert result["data"] == valid_user_input

    @pytest.mark.parametrize(
        ("exception", "error_key"),
        [
            (EatonUpsClientAuthenticationError("Auth failed"), "auth"),
            (EatonUpsClientCommunicationError("Connection failed"), "connection"),
            (EatonUpsClientError("Unknown error"), "unknown"),
        ],
    )
    async def test_error_handling(
        self, hass: HomeAssistant, valid_user_input, exception, error_key
    ):
        """Test error handling for various failure modes."""
        with patch(
            "custom_components.eaton_ups_mqtt.config_flow.EatonUpsFlowHandler._test_credentials",
            new_callable=AsyncMock,
            side_effect=exception,
        ):
            result = await hass.config_entries.flow.async_init(
                DOMAIN, context={"source": config_entries.SOURCE_USER}
            )
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], valid_user_input
            )

        assert result["type"] == FlowResultType.FORM
        assert result["errors"]["base"] == error_key

    async def test_cannot_connect(self, hass: HomeAssistant, valid_user_input):
        """Test handling when try_connection returns None."""
        with (
            patch(
                "custom_components.eaton_ups_mqtt.config_flow.EatonUpsFlowHandler._test_credentials",
                new_callable=AsyncMock,
            ),
            patch(
                "custom_components.eaton_ups_mqtt.config_flow.try_connection",
                return_value=None,
            ),
        ):
            result = await hass.config_entries.flow.async_init(
                DOMAIN, context={"source": config_entries.SOURCE_USER}
            )
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], valid_user_input
            )

        assert result["type"] == FlowResultType.FORM
        assert result["errors"]["base"] == "cannot_connect"

    async def test_already_configured(
        self, hass: HomeAssistant, valid_user_input, mock_identification
    ):
        """Test abort when device is already configured."""
        # Create existing entry with same unique_id
        existing_entry = MockConfigEntry(
            domain=DOMAIN,
            title="Existing UPS",
            data=valid_user_input,
            unique_id=mock_identification["macAddress"],
        )
        existing_entry.add_to_hass(hass)

        with (
            patch(
                "custom_components.eaton_ups_mqtt.config_flow.EatonUpsFlowHandler._test_credentials",
                new_callable=AsyncMock,
            ),
            patch(
                "custom_components.eaton_ups_mqtt.config_flow.try_connection",
                return_value=mock_identification,
            ),
        ):
            result = await hass.config_entries.flow.async_init(
                DOMAIN, context={"source": config_entries.SOURCE_USER}
            )
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], valid_user_input
            )

        assert result["type"] == FlowResultType.ABORT
        assert result["reason"] == "already_configured"


class TestReauthFlow:
    """Tests for reauth flow."""

    async def test_reauth_form_display(self, hass: HomeAssistant, valid_user_input):
        """Test that reauth form displays with current values."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="Test UPS",
            data=valid_user_input,
            unique_id="00:11:22:33:44:55",
        )
        entry.add_to_hass(hass)

        result = await entry.start_reauth_flow(hass)

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "reauth_confirm"

    async def test_reauth_success(
        self, hass: HomeAssistant, valid_user_input, mock_identification
    ):
        """Test successful reauthentication updates entry and aborts."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="Test UPS",
            data=valid_user_input,
            unique_id="00:11:22:33:44:55",
        )
        entry.add_to_hass(hass)

        updated_input = {
            **valid_user_input,
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

    @pytest.mark.parametrize(
        ("exception", "error_key"),
        [
            (EatonUpsClientAuthenticationError("Auth failed"), "auth"),
            (EatonUpsClientCommunicationError("Connection failed"), "connection"),
            (EatonUpsClientError("Unknown error"), "unknown"),
        ],
    )
    async def test_reauth_error_handling(
        self, hass: HomeAssistant, valid_user_input, exception, error_key
    ):
        """Test reauth error handling for various failure modes."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="Test UPS",
            data=valid_user_input,
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
                result["flow_id"], valid_user_input
            )

        assert result["type"] == FlowResultType.FORM
        assert result["errors"]["base"] == error_key


class TestReconfigureFlow:
    """Tests for reconfigure flow."""

    async def test_reconfigure_form_display(
        self, hass: HomeAssistant, valid_user_input
    ):
        """Test that reconfigure form displays with current values."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="Test UPS",
            data=valid_user_input,
            unique_id="00:11:22:33:44:55",
        )
        entry.add_to_hass(hass)

        result = await entry.start_reconfigure_flow(hass)

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "reconfigure"

    async def test_reconfigure_success(
        self, hass: HomeAssistant, valid_user_input, mock_identification
    ):
        """Test successful reconfiguration."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="Test UPS",
            data=valid_user_input,
            unique_id="00:11:22:33:44:55",
        )
        entry.add_to_hass(hass)

        updated_input = {**valid_user_input, CONF_HOST: "new-ups.example.local"}

        with patch(
            "custom_components.eaton_ups_mqtt.config_flow.try_connection",
            return_value=mock_identification,
        ):
            result = await entry.start_reconfigure_flow(hass)
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], updated_input
            )

        assert result["type"] == FlowResultType.ABORT
        assert result["reason"] == "reauth_successful"
        assert entry.data[CONF_HOST] == "new-ups.example.local"

    async def test_reconfigure_connection_failure(
        self, hass: HomeAssistant, valid_user_input
    ):
        """Test reconfigure with connection failure."""
        entry = MockConfigEntry(
            domain=DOMAIN,
            title="Test UPS",
            data=valid_user_input,
            unique_id="00:11:22:33:44:55",
        )
        entry.add_to_hass(hass)

        with patch(
            "custom_components.eaton_ups_mqtt.config_flow.try_connection",
            return_value=None,
        ):
            result = await entry.start_reconfigure_flow(hass)
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], valid_user_input
            )

        assert result["type"] == FlowResultType.FORM
        assert result["errors"]["base"] == "cannot_connect"
