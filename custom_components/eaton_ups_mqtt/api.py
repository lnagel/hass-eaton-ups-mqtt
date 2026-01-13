"""API Client for Eaton UPS MQTT Communication."""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import tempfile
import uuid
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING, Any

import paho.mqtt.client as mqtt
from paho.mqtt.client import Client, MQTTv31

from .const import MQTT_CONNECTION_ATTEMPTS, MQTT_PREFIX

if TYPE_CHECKING:
    from collections.abc import Callable

    import aiohttp


@dataclass
class EatonUpsMqttConfig:
    """Configuration for MQTT client."""

    host: str
    port: str
    server_cert: str
    client_cert: str
    client_key: str


logger = logging.getLogger(__name__)


class EatonUpsClientError(Exception):
    """Exception to indicate a general API error."""


class EatonUpsClientCommunicationError(
    EatonUpsClientError,
):
    """Exception to indicate a communication error."""


class EatonUpsClientAuthenticationError(
    EatonUpsClientError,
):
    """Exception to indicate an authentication error."""


class EatonUpsMqttClient:
    """Eaton UPS MQTT API Client."""

    _mqtt_client: Client | None
    _mqtt_connected: bool
    _mqtt_data: dict[str, Any]
    _temp_files: list[str]
    _update_callbacks: list[Callable[[dict[str, Any]], None]]
    _loop: asyncio.AbstractEventLoop | None

    def __init__(
        self, config: EatonUpsMqttConfig, session: aiohttp.ClientSession
    ) -> None:
        """Initialize Eaton UPS MQTT client."""
        self._host = config.host
        self._port = int(config.port)
        self._server_cert = config.server_cert
        self._client_cert = config.client_cert
        self._client_key = config.client_key
        self._session = session
        self._mqtt_client = None
        self._mqtt_connected = False
        self._mqtt_data = {}
        self._temp_files = []
        self._update_callbacks = []
        self._loop = None

    def subscribe_to_updates(
        self, callback: Callable[[dict[str, Any]], None]
    ) -> Callable[[], None]:
        """
        Subscribe to data updates.

        Returns a function that can be called to unsubscribe.
        """
        self._update_callbacks.append(callback)

        def unsubscribe() -> None:
            """Unsubscribe from updates."""
            if callback in self._update_callbacks:
                self._update_callbacks.remove(callback)

        return unsubscribe

    async def async_setup(self) -> None:
        """Set up the MQTT client connection."""
        if self._mqtt_client is not None:
            return

        # Store the event loop for later use
        self._loop = asyncio.get_running_loop()

        # Create the MQTT client
        client_id = f"hass-eaton-ups-{uuid.uuid4()}"
        self._mqtt_client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION1,
            client_id=client_id,
            protocol=MQTTv31,
        )
        self._mqtt_client.reconnect_delay_set(min_delay=1, max_delay=30)

        # Set up callbacks
        self._mqtt_client.on_connect = self._on_connect
        self._mqtt_client.on_message = self._on_message
        self._mqtt_client.on_disconnect = self._on_disconnect

        # Create temporary certificate files
        self._temp_files = await self._create_temp_cert_files()

        # Set up TLS/SSL certificates in the executor to avoid blocking the event loop
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            partial(
                self._setup_tls,
                self._temp_files[0],
                self._temp_files[1],
                self._temp_files[2],
            ),
        )

        # Connect to MQTT broker
        self._mqtt_client.connect_async(host=self._host, port=self._port)
        self._mqtt_client.loop_start()

        # Wait for connection to establish
        attempts = 0
        while not self._mqtt_connected and attempts < MQTT_CONNECTION_ATTEMPTS:
            await asyncio.sleep(1)
            attempts += 1

        if not self._mqtt_connected:
            self._cleanup_temp_files()
            error_msg = f"Failed to connect to MQTT broker at {self._host}:{self._port}"
            raise EatonUpsClientCommunicationError(error_msg)

        # Initial subscription to topics
        self._subscribe_to_topics()

    def _setup_tls(self, ca_certs: str, certfile: str, keyfile: str) -> None:
        """Set up TLS with certificates - runs in executor."""
        if self._mqtt_client is None:
            msg = "MQTT client not initialized"
            raise EatonUpsClientError(msg)
        self._mqtt_client.tls_set(
            ca_certs=ca_certs,
            certfile=certfile,
            keyfile=keyfile,
        )
        self._mqtt_client.tls_insecure_set(value=False)

    async def async_get_data(self) -> dict[str, Any]:
        """Get data from the MQTT broker."""
        if not self._mqtt_connected:
            await self.async_setup()

        # Return the current data
        return self._mqtt_data

    async def async_set_title(self, value: str) -> dict[str, bool]:
        """Set a value via MQTT (placeholder for now)."""
        if not self._mqtt_connected:
            await self.async_setup()

        if self._mqtt_client is None:
            msg = "MQTT client not initialized"
            raise EatonUpsClientError(msg)

        # This is a placeholder for actual command sending
        # In a real implementation, you would publish to a specific topic
        topic = MQTT_PREFIX + "powerDistributions/1/command"
        payload = json.dumps({"command": value})
        self._mqtt_client.publish(topic, payload)
        return {"success": True}

    async def async_disconnect(self) -> None:
        """Disconnect from the MQTT broker."""
        if self._mqtt_client is not None:
            self._mqtt_client.disconnect()
            self._mqtt_client.loop_stop()
            self._mqtt_client = None
            self._mqtt_connected = False
            self._cleanup_temp_files()

    def _subscribe_to_topics(self) -> None:
        """Subscribe to all required MQTT topics."""
        if self._mqtt_client is None:
            return
        self._mqtt_client.subscribe(
            topic=[
                (MQTT_PREFIX + "managers/#", 0),
                (MQTT_PREFIX + "powerDistributions/#", 0),
            ]
        )

    def _on_connect(
        self,
        _client: mqtt.Client,
        _userdata: Any,
        _flags: dict[str, int],
        rc: int,
        _properties: mqtt.Properties | None = None,
    ) -> None:
        """Handle connection callback."""
        if rc == 0:
            self._mqtt_connected = True
            # Resubscribe to topics on reconnect
            self._subscribe_to_topics()
        else:
            self._mqtt_connected = False

    def _on_disconnect(
        self,
        _client: mqtt.Client,
        _userdata: Any,
        _rc: int,
        _properties: mqtt.Properties | None = None,
    ) -> None:
        """Handle disconnection."""
        self._mqtt_connected = False

    def _on_message(
        self,
        _client: mqtt.Client,
        _userdata: Any,
        msg: mqtt.MQTTMessage,
    ) -> None:
        """Handle incoming messages."""
        try:
            topic = msg.topic
            payload = msg.payload.decode("utf-8")

            # Try to parse as JSON if possible
            data = json.loads(payload)

            # Store in the data dictionary using flat structure
            # Note: Topics are stored without `mbdetnrs/1.0/` prefix and payload data
            # is stored without modifications. This will make it possible to use the
            # storage key to make direct lookups in the data dictionary and provide
            # more efficient callbacks to sensor updates.
            key = topic.removeprefix(MQTT_PREFIX)
            self._mqtt_data[key] = data

            # Use the event loop to safely notify callbacks
            if self._loop and self._update_callbacks:
                for callback in self._update_callbacks:
                    self._loop.call_soon_threadsafe(
                        lambda cb=callback: cb(self._mqtt_data)
                    )

        except json.JSONDecodeError as e:
            # Just log the error and continue
            logger.warning("Error decoding JSON in MQTT message: %s", e)

        except Exception:
            # Just log the error and continue
            logger.exception("Error processing MQTT message")

    async def _create_temp_cert_files(self) -> list[str]:
        """Create temporary certificate files and return their paths."""
        # Create temp files in the executor to avoid blocking
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._create_temp_files)

    def _create_temp_files(self) -> list[str]:
        """Create temporary certificate files synchronously."""
        temp_files = []

        # Server certificate
        with tempfile.NamedTemporaryFile(mode="wb", delete=False) as server_cert_file:
            server_cert_file.write(self._server_cert.encode())
            temp_files.append(server_cert_file.name)

        # Client certificate
        with tempfile.NamedTemporaryFile(mode="wb", delete=False) as client_cert_file:
            client_cert_file.write(self._client_cert.encode())
            temp_files.append(client_cert_file.name)

        # Client key
        with tempfile.NamedTemporaryFile(mode="wb", delete=False) as client_key_file:
            client_key_file.write(self._client_key.encode())
            temp_files.append(client_key_file.name)

        return temp_files

    def _cleanup_temp_files(self) -> None:
        """Clean up temporary certificate files."""
        for file_path in self._temp_files:
            with contextlib.suppress(Exception):
                Path(file_path).unlink()
        self._temp_files = []
