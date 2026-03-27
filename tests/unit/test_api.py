"""Unit tests for API client functionality."""

from __future__ import annotations

import json
import ssl
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.eaton_ups_mqtt.api import (
    EatonUpsClientAuthenticationError,
    EatonUpsClientCommunicationError,
    EatonUpsClientError,
    EatonUpsMqttClient,
    EatonUpsMqttConfig,
)
from custom_components.eaton_ups_mqtt.const import MQTT_PREFIX


@pytest.fixture
def mqtt_config():
    """Create a test MQTT config."""
    return EatonUpsMqttConfig(
        host="test.example.com",
        port="8883",
        server_cert="-----BEGIN CERTIFICATE-----\nSERVER\n-----END CERTIFICATE-----",
        client_cert="-----BEGIN CERTIFICATE-----\nCLIENT\n-----END CERTIFICATE-----",
        client_key="-----BEGIN PRIVATE KEY-----\nKEY\n-----END PRIVATE KEY-----",
    )


@pytest.fixture
def mqtt_client(mqtt_config):
    """Create a client instance for testing."""
    session = MagicMock()
    return EatonUpsMqttClient(mqtt_config, session)


class TestSubscribeToUpdates:
    """Tests for subscribe_to_updates method."""

    def test_subscribe_adds_callback(self, mqtt_client):
        """Test that subscribing adds the callback to the list."""
        callback = MagicMock()
        mqtt_client.subscribe_to_updates(callback)
        assert callback in mqtt_client._update_callbacks

    def test_unsubscribe_removes_callback(self, mqtt_client):
        """Test that unsubscribe function removes the callback."""
        callback = MagicMock()
        unsubscribe = mqtt_client.subscribe_to_updates(callback)
        assert callback in mqtt_client._update_callbacks

        unsubscribe()
        assert callback not in mqtt_client._update_callbacks

    def test_unsubscribe_handles_missing_callback(self, mqtt_client):
        """Test unsubscribe is safe when callback already removed."""
        callback = MagicMock()
        unsubscribe = mqtt_client.subscribe_to_updates(callback)

        # Remove manually first
        mqtt_client._update_callbacks.remove(callback)

        # Should not raise
        unsubscribe()

    def test_multiple_subscriptions(self, mqtt_client):
        """Test multiple callbacks can be subscribed."""
        callbacks = [MagicMock() for _ in range(3)]
        unsubscribes = [mqtt_client.subscribe_to_updates(cb) for cb in callbacks]

        assert len(mqtt_client._update_callbacks) == 3

        # Unsubscribe middle one
        unsubscribes[1]()
        assert len(mqtt_client._update_callbacks) == 2
        assert callbacks[1] not in mqtt_client._update_callbacks


class TestMqttCallbacks:
    """Tests for MQTT callback handlers."""

    def test_on_connect_success(self, mqtt_client):
        """Test on_connect sets connected flag on success."""
        mqtt_client._mqtt_client = MagicMock()
        reason_code = MagicMock()
        reason_code.is_failure = False
        mqtt_client._on_connect(
            _client=MagicMock(),
            _userdata=None,
            connect_flags=MagicMock(),
            reason_code=reason_code,
        )
        assert mqtt_client._mqtt_connected is True
        mqtt_client._mqtt_client.subscribe.assert_called()

    def test_on_connect_failure(self, mqtt_client):
        """Test on_connect sets connected flag False on failure."""
        mqtt_client._mqtt_client = MagicMock()
        reason_code = MagicMock()
        reason_code.is_failure = True
        mqtt_client._on_connect(
            _client=MagicMock(),
            _userdata=None,
            connect_flags=MagicMock(),
            reason_code=reason_code,
        )
        assert mqtt_client._mqtt_connected is False

    def test_on_disconnect(self, mqtt_client):
        """Test on_disconnect sets connected flag False."""
        mqtt_client._mqtt_connected = True
        mqtt_client._on_disconnect(
            _client=MagicMock(),
            _userdata=None,
            disconnect_flags=MagicMock(),
            reason_code=MagicMock(),
        )
        assert mqtt_client._mqtt_connected is False

    def test_on_message_valid_json(self, mqtt_client):
        """Test on_message parses valid JSON messages."""
        msg = MagicMock()
        msg.topic = MQTT_PREFIX + "managers/1/identification"
        msg.payload = json.dumps({"model": "Test UPS"}).encode()

        mqtt_client._on_message(
            _client=MagicMock(),
            _userdata=None,
            msg=msg,
        )

        assert "managers/1/identification" in mqtt_client._mqtt_data
        assert (
            mqtt_client._mqtt_data["managers/1/identification"]["model"] == "Test UPS"
        )

    def test_on_message_invalid_json(self, mqtt_client):
        """Test on_message handles invalid JSON gracefully."""
        msg = MagicMock()
        msg.topic = MQTT_PREFIX + "managers/1/test"
        msg.payload = b"not valid json"

        # Should not raise
        mqtt_client._on_message(
            _client=MagicMock(),
            _userdata=None,
            msg=msg,
        )

        # Data should not be added
        assert "managers/1/test" not in mqtt_client._mqtt_data

    def test_on_message_notifies_callbacks(self, mqtt_client):
        """Test on_message notifies update callbacks."""
        mqtt_client._loop = MagicMock()
        callback = MagicMock()
        mqtt_client._update_callbacks.append(callback)

        msg = MagicMock()
        msg.topic = MQTT_PREFIX + "test/topic"
        msg.payload = json.dumps({"value": 42}).encode()

        mqtt_client._on_message(
            _client=MagicMock(),
            _userdata=None,
            msg=msg,
        )

        mqtt_client._loop.call_soon_threadsafe.assert_called()

    def test_on_message_handles_general_exception(self, mqtt_client):
        """Test on_message handles general exceptions gracefully."""
        msg = MagicMock()
        msg.topic = MQTT_PREFIX + "test/topic"
        # Configure payload.decode to raise an exception
        msg.payload.decode.side_effect = UnicodeDecodeError("utf-8", b"", 0, 1, "test")

        # Should not raise
        mqtt_client._on_message(
            _client=MagicMock(),
            _userdata=None,
            msg=msg,
        )


class TestSubscribeToTopics:
    """Tests for _subscribe_to_topics method."""

    def test_subscribe_when_client_none(self, mqtt_client):
        """Test _subscribe_to_topics handles None client."""
        mqtt_client._mqtt_client = None
        # Should not raise
        mqtt_client._subscribe_to_topics()

    def test_subscribe_calls_mqtt_subscribe(self, mqtt_client):
        """Test _subscribe_to_topics subscribes to correct topics."""
        mqtt_client._mqtt_client = MagicMock()
        mqtt_client._subscribe_to_topics()

        mqtt_client._mqtt_client.subscribe.assert_called_once()
        call_args = mqtt_client._mqtt_client.subscribe.call_args
        topics = call_args.kwargs.get("topic") or call_args.args[0]

        # Should subscribe to managers and powerDistributions
        topic_paths = [t[0] for t in topics]
        assert any("managers/#" in t for t in topic_paths)
        assert any("powerDistributions/#" in t for t in topic_paths)


class TestSetupTls:
    """Tests for _setup_tls method."""

    def test_setup_tls_with_none_client(self, mqtt_client):
        """Test _setup_tls raises error when client is None."""
        mqtt_client._mqtt_client = None
        with pytest.raises(EatonUpsClientError, match="MQTT client not initialized"):
            mqtt_client._setup_tls("ca", "cert", "key")

    def test_setup_tls_configures_client(self, mqtt_client):
        """Test _setup_tls configures TLS on client."""
        mqtt_client._mqtt_client = MagicMock()
        mqtt_client._setup_tls("/path/ca", "/path/cert", "/path/key")

        mqtt_client._mqtt_client.tls_set.assert_called_once_with(
            ca_certs="/path/ca",
            certfile="/path/cert",
            keyfile="/path/key",
        )
        mqtt_client._mqtt_client.tls_insecure_set.assert_called_once_with(value=True)

    def test_setup_tls_disables_hostname_verification(self, mqtt_client):
        """Test TLS disables hostname verification for certificate pinning.

        Since we pin the server certificate (using it as the CA cert), hostname
        verification must be disabled so users can connect by either hostname
        or IP address with the same certificate. The certificate's CN/SAN
        fields should not be validated against the connection host.
        """
        mqtt_client._mqtt_client = MagicMock()
        mqtt_client._setup_tls("/path/ca", "/path/cert", "/path/key")

        # tls_insecure_set(True) disables hostname/CN checking in paho-mqtt
        # while still verifying the certificate chain against the CA cert.
        mqtt_client._mqtt_client.tls_insecure_set.assert_called_once_with(value=True)

    @pytest.mark.parametrize(
        "host",
        [
            "ups.example.local",
            "192.168.1.100",
            "10.0.0.1",
            "fd12:3456:789a::1",
        ],
        ids=["hostname", "ipv4", "ipv4-private", "ipv6"],
    )
    def test_setup_tls_same_cert_for_hostname_and_ip(self, host):
        """Test that TLS setup uses the same config regardless of host type.

        The same pinned server certificate must work for both hostname and IP
        address connections. This verifies that _setup_tls does not change
        behavior based on the host value, and always disables hostname
        verification so the certificate CN is never checked.
        """
        config = EatonUpsMqttConfig(
            host=host,
            port="8883",
            server_cert="-----BEGIN CERTIFICATE-----\nSERVER\n-----END CERTIFICATE-----",
            client_cert="-----BEGIN CERTIFICATE-----\nCLIENT\n-----END CERTIFICATE-----",
            client_key="-----BEGIN PRIVATE KEY-----\nKEY\n-----END PRIVATE KEY-----",
        )
        session = MagicMock()
        client = EatonUpsMqttClient(config, session)
        client._mqtt_client = MagicMock()

        client._setup_tls("/path/ca", "/path/cert", "/path/key")

        # Certificate chain verification is still active (tls_set called)
        client._mqtt_client.tls_set.assert_called_once_with(
            ca_certs="/path/ca",
            certfile="/path/cert",
            keyfile="/path/key",
        )
        # But hostname/CN verification is disabled for certificate pinning
        client._mqtt_client.tls_insecure_set.assert_called_once_with(value=True)


class TestAsyncDisconnect:
    """Tests for async_disconnect method."""

    @pytest.mark.asyncio
    async def test_disconnect_cleans_up(self, mqtt_client):
        """Test disconnect cleans up client and files."""
        mqtt_client._mqtt_client = MagicMock()
        mqtt_client._mqtt_connected = True
        mqtt_client._temp_files = ["/tmp/test1", "/tmp/test2"]

        with patch.object(mqtt_client, "_cleanup_temp_files") as mock_cleanup:
            await mqtt_client.async_disconnect()
            mock_cleanup.assert_called_once()

        assert mqtt_client._mqtt_client is None
        assert mqtt_client._mqtt_connected is False

    @pytest.mark.asyncio
    async def test_disconnect_with_none_client(self, mqtt_client):
        """Test disconnect handles None client gracefully."""
        mqtt_client._mqtt_client = None
        # Should not raise
        await mqtt_client.async_disconnect()


class TestAsyncSetup:
    """Tests for async_setup method."""

    @pytest.mark.asyncio
    async def test_setup_returns_early_if_already_setup(self, mqtt_client):
        """Test async_setup returns early if client already exists."""
        mqtt_client._mqtt_client = MagicMock()  # Already set up

        # Should return without doing anything
        await mqtt_client.async_setup()

        # Nothing should change
        assert mqtt_client._mqtt_client is not None


class TestAsyncSetTitle:
    """Tests for async_set_title method."""

    @pytest.mark.asyncio
    async def test_set_title_publishes_command(self, mqtt_client):
        """Test set_title publishes to MQTT."""
        mqtt_client._mqtt_connected = True
        mqtt_client._mqtt_client = MagicMock()

        result = await mqtt_client.async_set_title("test_command")

        mqtt_client._mqtt_client.publish.assert_called_once()
        assert result == {"success": True}

    @pytest.mark.asyncio
    async def test_set_title_raises_when_client_none(self, mqtt_client):
        """Test set_title raises error when client is None."""
        mqtt_client._mqtt_connected = True
        mqtt_client._mqtt_client = None

        with pytest.raises(EatonUpsClientError, match="MQTT client not initialized"):
            await mqtt_client.async_set_title("test")


class TestAsyncGetData:
    """Tests for async_get_data method."""

    @pytest.mark.asyncio
    async def test_get_data_returns_mqtt_data(self, mqtt_client):
        """Test get_data returns stored MQTT data."""
        mqtt_client._mqtt_connected = True
        mqtt_client._mqtt_data = {"test": "data"}

        result = await mqtt_client.async_get_data()
        assert result == {"test": "data"}

    @pytest.mark.asyncio
    async def test_get_data_calls_setup_when_disconnected(self, mqtt_client):
        """Test get_data calls setup when not connected."""
        mqtt_client._mqtt_connected = False

        with patch.object(
            mqtt_client, "async_setup", new_callable=AsyncMock
        ) as mock_setup:
            # After setup, simulate connection
            async def set_connected():
                mqtt_client._mqtt_connected = True

            mock_setup.side_effect = set_connected

            await mqtt_client.async_get_data()
            mock_setup.assert_called_once()


class TestAsyncSetupErrors:
    """Tests for async_setup error handling."""

    @pytest.mark.asyncio
    async def test_setup_tls_ssl_error_raises_auth_error(self, mqtt_client):
        """Test that SSLError during TLS setup raises authentication error."""
        with (
            patch("paho.mqtt.client.Client") as mock_client_class,
            patch.object(
                mqtt_client,
                "_create_temp_cert_files",
                new_callable=AsyncMock,
                return_value=["/tmp/ca", "/tmp/cert", "/tmp/key"],
            ),
            patch.object(mqtt_client, "_cleanup_temp_files"),
            patch.object(
                mqtt_client,
                "_setup_tls",
                side_effect=ssl.SSLError("bad certificate"),
            ),
        ):
            mock_client_class.return_value = MagicMock()
            mqtt_client._mqtt_client = None

            with pytest.raises(
                EatonUpsClientAuthenticationError,
                match="TLS setup failed",
            ):
                await mqtt_client.async_setup()

    @pytest.mark.asyncio
    async def test_setup_connection_timeout_raises_comm_error(self, mqtt_client):
        """Test that connection timeout raises communication error."""
        mock_client = MagicMock()
        mock_client.connect_async = MagicMock()
        mock_client.loop_start = MagicMock()
        mock_client.reconnect_delay_set = MagicMock()
        mock_client.tls_set = MagicMock()
        mock_client.tls_insecure_set = MagicMock()

        with (
            patch("paho.mqtt.client.Client", return_value=mock_client),
            patch.object(
                mqtt_client,
                "_create_temp_cert_files",
                new_callable=AsyncMock,
                return_value=["/tmp/ca", "/tmp/cert", "/tmp/key"],
            ),
            patch.object(mqtt_client, "_cleanup_temp_files"),
            patch(
                "custom_components.eaton_ups_mqtt.api.MQTT_CONNECTION_ATTEMPTS",
                1,
            ),
            patch("asyncio.sleep", new_callable=AsyncMock),
        ):
            mqtt_client._mqtt_client = None

            with pytest.raises(
                EatonUpsClientCommunicationError,
                match=f"after {1} attempts",
            ):
                await mqtt_client.async_setup()
