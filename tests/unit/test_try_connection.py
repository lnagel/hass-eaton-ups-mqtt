"""Unit tests for try_connection in config_flow."""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from custom_components.eaton_ups_mqtt.config_flow import try_connection
from custom_components.eaton_ups_mqtt.const import (
    CONF_CLIENT_CERT,
    CONF_CLIENT_KEY,
    CONF_SERVER_CERT,
    MQTT_PREFIX,
)


@pytest.fixture
def user_input() -> dict[str, Any]:
    """Create valid user input for try_connection."""
    return {
        "host": "ups.example.local",
        "port": 8883,
        CONF_SERVER_CERT: "-----BEGIN CERTIFICATE-----\nSERVER\n-----END CERTIFICATE-----",
        CONF_CLIENT_CERT: "-----BEGIN CERTIFICATE-----\nCLIENT\n-----END CERTIFICATE-----",
        CONF_CLIENT_KEY: "-----BEGIN PRIVATE KEY-----\nKEY\n-----END PRIVATE KEY-----",
    }


class TestTryConnection:
    """Tests for the try_connection function."""

    def test_tls_configured_with_hostname_verification_disabled(self, user_input):
        """Test that TLS is configured with hostname verification disabled.

        try_connection must call tls_insecure_set(value=True) to disable
        hostname verification, allowing connection by IP or hostname with
        the same pinned server certificate.
        """
        mock_client = MagicMock()

        # Make connect_async trigger on_connect which subscribes, then
        # on_message delivers identification data
        def fake_connect_async(host, port):
            mock_client.on_connect(mock_client, None, {}, 0)

        def fake_loop_start():
            msg = MagicMock()
            msg.topic = MQTT_PREFIX + "managers/1/identification"
            msg.payload = json.dumps({"mac": "00:11:22:33:44:55"}).encode()
            mock_client.on_message(mock_client, None, msg)

        mock_client.connect_async = MagicMock(side_effect=fake_connect_async)
        mock_client.loop_start = MagicMock(side_effect=fake_loop_start)

        with patch(
            "homeassistant.components.mqtt.async_client.AsyncMQTTClient",
            return_value=mock_client,
        ):
            result = try_connection(user_input)

        assert result == {"mac": "00:11:22:33:44:55"}

        # Verify TLS was configured correctly
        mock_client.tls_set.assert_called_once()
        call_kwargs = mock_client.tls_set.call_args.kwargs
        assert "ca_certs" in call_kwargs
        assert "certfile" in call_kwargs
        assert "keyfile" in call_kwargs

        # Key assertion: hostname verification must be disabled
        mock_client.tls_insecure_set.assert_called_once_with(value=True)

    def test_returns_none_on_connect_failure(self, user_input):
        """Test that try_connection returns None on connection failure."""
        mock_client = MagicMock()

        def fake_connect_async(host, port):
            mock_client.on_connect(mock_client, None, {}, 1)

        mock_client.connect_async = MagicMock(side_effect=fake_connect_async)

        with (
            patch(
                "homeassistant.components.mqtt.async_client.AsyncMQTTClient",
                return_value=mock_client,
            ),
            patch(
                "custom_components.eaton_ups_mqtt.config_flow.MQTT_TIMEOUT",
                0.1,
            ),
        ):
            result = try_connection(user_input)

        assert result is None
