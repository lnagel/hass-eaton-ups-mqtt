"""API Client for Eaton UPS MQTT Communication."""

from __future__ import annotations

import asyncio
import json
import logging
import socket
import ssl
import tempfile
import os
import uuid
from typing import Any, Callable, Dict, Optional
from functools import partial

import aiohttp
import async_timeout
import paho.mqtt.client as mqtt
from paho.mqtt.client import MQTTv31

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

    def __init__(
        self,
        host: str,
        port: str,
        server_cert: str,
        client_cert: str,
        client_key: str,
        session: aiohttp.ClientSession,
    ) -> None:
        """Initialize Eaton UPS MQTT client."""
        self._host = host
        self._port = int(port)
        self._server_cert = server_cert
        self._client_cert = client_cert
        self._client_key = client_key
        self._session = session
        self._mqtt_client = None
        self._mqtt_connected = False
        self._mqtt_data = {}
        self._temp_files = []
        self._update_callbacks = []  # Add this line to store callbacks
        self._loop = None  # Store the event loop

    def subscribe_to_updates(self, callback: Callable[[dict], None]) -> Callable[[], None]:
        """Subscribe to data updates.

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
        client_id = f"hass-eaton-ups-{mqtt.base62(uuid.uuid4().int, padding=10)}"
        self._mqtt_client = mqtt.Client(client_id=client_id, protocol=MQTTv31)

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
        while not self._mqtt_connected and attempts < 10:
            await asyncio.sleep(1)
            attempts += 1

        if not self._mqtt_connected:
            self._cleanup_temp_files()
            raise EatonUpsClientCommunicationError(f"Failed to connect to MQTT broker at {self._host}:{self._port}")

        # Subscribe to the topics
        self._mqtt_client.subscribe("mbdetnrs/1.0/#")

    def _setup_tls(self, ca_certs, certfile, keyfile):
        """Set up TLS with certificates - runs in executor."""
        self._mqtt_client.tls_set(
            ca_certs=ca_certs,
            certfile=certfile,
            keyfile=keyfile,
        )
        self._mqtt_client.tls_insecure_set(False)

    async def async_get_data(self) -> Dict[str, Any]:
        """Get data from the MQTT broker."""
        if not self._mqtt_connected:
            await self.async_setup()

        # Return the current data
        return self._mqtt_data

    async def async_set_title(self, value: str) -> Any:
        """Set a value via MQTT (placeholder for now)."""
        if not self._mqtt_connected:
            await self.async_setup()

        # This is a placeholder for actual command sending
        # In a real implementation, you would publish to a specific topic
        self._mqtt_client.publish("mbdetnrs/1.0/powerDistributions/1/command", json.dumps({"command": value}))
        return {"success": True}

    async def async_disconnect(self) -> None:
        """Disconnect from the MQTT broker."""
        if self._mqtt_client is not None:
            self._mqtt_client.disconnect()
            self._mqtt_client.loop_stop()
            self._mqtt_client = None
            self._mqtt_connected = False
            self._cleanup_temp_files()

    def _on_connect(
        self,
        client: mqtt.Client,
        userdata: Any,
        flags: Dict[str, int],
        rc: int,
        properties: mqtt.Properties | None = None,
    ) -> None:
        """Handle connection callback."""
        if rc == 0:
            self._mqtt_connected = True
        else:
            self._mqtt_connected = False

    def _on_disconnect(
        self,
        client: mqtt.Client,
        userdata: Any,
        rc: int,
        properties: mqtt.Properties | None = None,
    ) -> None:
        """Handle disconnection."""
        self._mqtt_connected = False

    def _on_message(self, client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage) -> None:
        """Handle incoming messages."""
        try:
            topic = msg.topic
            payload = msg.payload.decode("utf-8")

            # Try to parse as JSON if possible
            data = json.loads(payload)

            # Store in the data dictionary using flat structure
            # Note: Topics are stored without `mbdetnrs/1.0/` prefix and payload data is stored without modifications.
            # This will make it possible to use the storage key to make direct lookups in the data dictionary and
            # provide more efficient callbacks to sensor updates.
            key = topic.removeprefix("mbdetnrs/1.0/")
            self._mqtt_data[key] = data

            # Use the event loop to safely notify callbacks
            if self._loop and self._update_callbacks:
                for callback in self._update_callbacks:
                    self._loop.call_soon_threadsafe(lambda cb=callback: cb(self._mqtt_data))

        except json.JSONDecodeError as e:
            # Just log the error and continue
            logger.warning(f"Error decoding JSON in MQTT message: {e}")

        except Exception as e:
            # Just log the error and continue
            logger.error(f"Error processing MQTT message: {e}")

    async def _create_temp_cert_files(self) -> list[str]:
        """Create temporary certificate files and return their paths."""
        # Create temp files in the executor to avoid blocking
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._create_temp_files)

    def _create_temp_files(self) -> list[str]:
        """Create temporary certificate files synchronously."""
        temp_files = []

        # Server certificate
        server_cert_file = tempfile.NamedTemporaryFile(delete=False)
        server_cert_file.write(self._server_cert.encode())
        server_cert_file.close()
        temp_files.append(server_cert_file.name)

        # Client certificate
        client_cert_file = tempfile.NamedTemporaryFile(delete=False)
        client_cert_file.write(self._client_cert.encode())
        client_cert_file.close()
        temp_files.append(client_cert_file.name)

        # Client key
        client_key_file = tempfile.NamedTemporaryFile(delete=False)
        client_key_file.write(self._client_key.encode())
        client_key_file.close()
        temp_files.append(client_key_file.name)

        return temp_files

    def _cleanup_temp_files(self) -> None:
        """Clean up temporary certificate files."""
        for file_path in self._temp_files:
            try:
                os.remove(file_path)
            except Exception:
                pass
        self._temp_files = []
