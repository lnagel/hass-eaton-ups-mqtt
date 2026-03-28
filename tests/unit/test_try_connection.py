"""Unit tests for try_connection in config_flow."""

from __future__ import annotations

import json
import ssl
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from custom_components.eaton_ups_mqtt.config_flow import (
    ConnectionResult,
    try_connection,
)
from custom_components.eaton_ups_mqtt.const import (
    CONF_CLIENT_CERT,
    CONF_CLIENT_KEY,
    CONF_SERVER_CERT,
    MQTT_SUPPORTED_PREFIXES,
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


def _make_mock_client_with_success():
    """Create a mock client that simulates a successful connection."""
    mock_client = MagicMock()

    def fake_connect(host, port):
        mock_client.on_connect(mock_client, None, {}, 0)

    def fake_loop_start():
        msg = MagicMock()
        msg.topic = MQTT_SUPPORTED_PREFIXES[0] + "managers/1/identification"
        msg.payload = json.dumps({"macAddress": "00:11:22:33:44:55"}).encode()
        mock_client.on_message(mock_client, None, msg)

    mock_client.connect = MagicMock(side_effect=fake_connect)
    mock_client.loop_start = MagicMock(side_effect=fake_loop_start)
    return mock_client


class TestTryConnection:
    """Tests for the try_connection function."""

    def test_successful_connection(self, user_input):
        """Test successful connection returns identification data."""
        mock_client = _make_mock_client_with_success()

        with patch(
            "homeassistant.components.mqtt.async_client.AsyncMQTTClient",
            return_value=mock_client,
        ):
            result = try_connection(user_input)

        assert isinstance(result, ConnectionResult)
        assert result.identification == {"macAddress": "00:11:22:33:44:55"}
        assert result.error_key is None

    def test_tls_configured_with_hostname_verification_disabled(self, user_input):
        """Test that TLS is configured with hostname verification disabled.

        try_connection must call tls_insecure_set(value=True) to disable
        hostname verification, allowing connection by IP or hostname with
        the same pinned server certificate.
        """
        mock_client = _make_mock_client_with_success()

        with patch(
            "homeassistant.components.mqtt.async_client.AsyncMQTTClient",
            return_value=mock_client,
        ):
            result = try_connection(user_input)

        assert result.identification == {"macAddress": "00:11:22:33:44:55"}

        # Verify TLS was configured correctly
        mock_client.tls_set.assert_called_once()
        call_kwargs = mock_client.tls_set.call_args.kwargs
        assert "ca_certs" in call_kwargs
        assert "certfile" in call_kwargs
        assert "keyfile" in call_kwargs

        # Key assertion: hostname verification must be disabled
        mock_client.tls_insecure_set.assert_called_once_with(value=True)

    def test_returns_connection_refused(self, user_input):
        """Test that ConnectionRefusedError returns connection_refused."""
        mock_client = MagicMock()
        mock_client.connect = MagicMock(
            side_effect=ConnectionRefusedError("Connection refused")
        )

        with patch(
            "homeassistant.components.mqtt.async_client.AsyncMQTTClient",
            return_value=mock_client,
        ):
            result = try_connection(user_input)

        assert result.error_key == "connection_refused"
        assert "Connection refused" in result.error_detail

    def test_returns_connection_timeout(self, user_input):
        """Test that TimeoutError returns connection_timeout."""
        mock_client = MagicMock()
        mock_client.connect = MagicMock(side_effect=TimeoutError("Timed out"))

        with patch(
            "homeassistant.components.mqtt.async_client.AsyncMQTTClient",
            return_value=mock_client,
        ):
            result = try_connection(user_input)

        assert result.error_key == "connection_timeout"
        assert "timed out" in result.error_detail.lower()

    def test_returns_host_unreachable_on_os_error(self, user_input):
        """Test that generic OSError returns host_unreachable."""
        mock_client = MagicMock()
        mock_client.connect = MagicMock(side_effect=OSError("No route to host"))

        with patch(
            "homeassistant.components.mqtt.async_client.AsyncMQTTClient",
            return_value=mock_client,
        ):
            result = try_connection(user_input)

        assert result.error_key == "host_unreachable"
        assert "No route to host" in result.error_detail

    def test_returns_server_cert_mismatch_on_ssl_verification_error(self, user_input):
        """Test that SSLCertVerificationError returns server_cert_mismatch."""
        mock_client = MagicMock()
        mock_client.connect = MagicMock(
            side_effect=ssl.SSLCertVerificationError("certificate verify failed")
        )

        with patch(
            "homeassistant.components.mqtt.async_client.AsyncMQTTClient",
            return_value=mock_client,
        ):
            result = try_connection(user_input)

        assert result.error_key == "server_cert_mismatch"
        assert "certificate verify failed" in result.error_detail

    def test_returns_tls_handshake_failed_on_ssl_error(self, user_input):
        """Test that generic SSLError returns tls_handshake_failed."""
        mock_client = MagicMock()
        mock_client.connect = MagicMock(
            side_effect=ssl.SSLError("tlsv1 alert unknown ca")
        )

        with patch(
            "homeassistant.components.mqtt.async_client.AsyncMQTTClient",
            return_value=mock_client,
        ):
            result = try_connection(user_input)

        assert result.error_key == "tls_handshake_failed"
        assert "tlsv1 alert unknown ca" in result.error_detail

    def test_returns_mqtt_connect_refused_on_bad_result_code(self, user_input):
        """Test that MQTT CONNACK rejection returns mqtt_connect_refused."""
        mock_client = MagicMock()

        def fake_connect(host, port):
            # Simulate MQTT broker rejecting with result_code=5
            mock_client.on_connect(mock_client, None, {}, 5)

        mock_client.connect = MagicMock(side_effect=fake_connect)

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

        assert result.error_key == "mqtt_connect_refused"
        assert "refused" in result.error_detail.lower()

    def test_returns_no_data_received_on_timeout(self, user_input):
        """Test that queue timeout returns no_data_received."""
        mock_client = MagicMock()

        def fake_connect(host, port):
            # Successful connection but no message ever arrives
            mock_client.on_connect(mock_client, None, {}, 0)

        mock_client.connect = MagicMock(side_effect=fake_connect)

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

        assert result.error_key == "no_data_received"
        assert "no identification data" in result.error_detail.lower()

    def test_returns_invalid_response_on_json_decode_error(self, user_input):
        """Test that invalid JSON in message returns invalid_response."""
        mock_client = MagicMock()

        def fake_connect(host, port):
            mock_client.on_connect(mock_client, None, {}, 0)

        def fake_loop_start():
            msg = MagicMock()
            msg.topic = MQTT_SUPPORTED_PREFIXES[0] + "managers/1/identification"
            msg.payload = b"not valid json"
            mock_client.on_message(mock_client, None, msg)

        mock_client.connect = MagicMock(side_effect=fake_connect)
        mock_client.loop_start = MagicMock(side_effect=fake_loop_start)

        with patch(
            "homeassistant.components.mqtt.async_client.AsyncMQTTClient",
            return_value=mock_client,
        ):
            result = try_connection(user_input)

        assert result.error_key == "invalid_response"
        assert "invalid JSON" in result.error_detail

    @pytest.mark.parametrize(
        "prefix",
        MQTT_SUPPORTED_PREFIXES,
        ids=[p.strip("/").replace("/", "_") for p in MQTT_SUPPORTED_PREFIXES],
    )
    def test_successful_connection_with_prefix(self, user_input, prefix):
        """Test successful connection works with both M2 and M3 prefixes."""
        mock_client = MagicMock()

        def fake_connect(host, port):
            mock_client.on_connect(mock_client, None, {}, 0)

        def fake_loop_start():
            msg = MagicMock()
            msg.topic = prefix + "managers/1/identification"
            msg.payload = json.dumps({"macAddress": "AA:BB:CC:DD:EE:FF"}).encode()
            mock_client.on_message(mock_client, None, msg)

        mock_client.connect = MagicMock(side_effect=fake_connect)
        mock_client.loop_start = MagicMock(side_effect=fake_loop_start)

        with patch(
            "homeassistant.components.mqtt.async_client.AsyncMQTTClient",
            return_value=mock_client,
        ):
            result = try_connection(user_input)

        assert result.identification == {"macAddress": "AA:BB:CC:DD:EE:FF"}
        assert result.error_key is None

    def test_ignores_non_matching_topic(self, user_input):
        """Test that messages with non-matching topics are ignored."""
        mock_client = MagicMock()

        def fake_connect(host, port):
            mock_client.on_connect(mock_client, None, {}, 0)

        def fake_loop_start():
            # Send a message with a topic that doesn't match the regex
            msg = MagicMock()
            msg.topic = "other/topic/managers/1/identification"
            msg.payload = json.dumps({"macAddress": "AA:BB:CC:DD:EE:FF"}).encode()
            mock_client.on_message(mock_client, None, msg)

        mock_client.connect = MagicMock(side_effect=fake_connect)
        mock_client.loop_start = MagicMock(side_effect=fake_loop_start)

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

        assert result.error_key == "no_data_received"
