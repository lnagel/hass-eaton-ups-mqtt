"""Config flow for Eaton UPS integration."""

from __future__ import annotations

import logging
import queue
import tempfile
import uuid
from pathlib import Path
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import SOURCE_RECONFIGURE
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from slugify import slugify

from .api import (
    EatonUpsClientAuthenticationError,
    EatonUpsClientCommunicationError,
    EatonUpsClientError,
    EatonUpsMqttClient,
)
from .const import (
    CONF_CLIENT_CERT,
    CONF_CLIENT_KEY,
    CONF_SERVER_CERT,
    DEFAULT_PORT,
    DOMAIN,
    LOGGER,
    MQTT_TIMEOUT,
)

logger = logging.getLogger(__name__)


HOST_SELECTOR = selector.TextSelector(
    selector.TextSelectorConfig(
        type=selector.TextSelectorType.TEXT,
    ),
)
PORT_SELECTOR = vol.All(
    selector.NumberSelector(
        selector.NumberSelectorConfig(
            mode=selector.NumberSelectorMode.BOX,
            min=1,
            max=65535,
        )
    ),
    vol.Coerce(int),
)
PEM_CERT_SELECTOR = selector.TextSelector(
    selector.TextSelectorConfig(
        multiline=True,
        type=selector.TextSelectorType.TEXT,
    ),
)
PEM_KEY_SELECTOR = selector.TextSelector(
    selector.TextSelectorConfig(
        multiline=True,
        type=selector.TextSelectorType.TEXT,
    ),
)


class EatonUpsFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow handler for Eaton UPS integration."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> config_entries.ConfigFlowResult:
        """
        Handle initial configuration flow.

        Prompts user for:
        - UPS Network-M2/M3 card hostname/IP
        - MQTT port (default 8883)
        - Server certificate (PEM format)
        - Client certificate (PEM format)
        - Client private key (PEM format)
        """
        _errors = {}

        if user_input is not None:
            try:
                await self._test_credentials(
                    host=user_input[CONF_HOST],
                    port=user_input[CONF_PORT],
                    server_cert=user_input[CONF_SERVER_CERT],
                    client_cert=user_input[CONF_CLIENT_CERT],
                    client_key=user_input[CONF_CLIENT_KEY],
                )
            except EatonUpsClientAuthenticationError as exception:
                LOGGER.warning(exception)
                _errors["base"] = "auth"
            except EatonUpsClientCommunicationError as exception:
                LOGGER.error(exception)
                _errors["base"] = "connection"
            except EatonUpsClientError as exception:
                LOGGER.exception(exception)
                _errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(
                    ## Do NOT use this in production code
                    ## The unique_id should never be something that can change
                    ## https://developers.home-assistant.io/docs/config_entries_config_flow_handler#unique-ids
                    unique_id=slugify(user_input[CONF_HOST])
                )
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input[CONF_HOST],
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_HOST,
                        default=(user_input or {}).get(CONF_HOST, vol.UNDEFINED),
                    ): HOST_SELECTOR,
                    vol.Required(
                        CONF_PORT,
                        default=(user_input or {}).get(CONF_PORT, DEFAULT_PORT),
                    ): PORT_SELECTOR,
                    vol.Required(
                        CONF_SERVER_CERT,
                        default=(user_input or {}).get(CONF_SERVER_CERT, vol.UNDEFINED),
                    ): PEM_CERT_SELECTOR,
                    vol.Required(
                        CONF_CLIENT_CERT,
                        default=(user_input or {}).get(CONF_CLIENT_CERT, vol.UNDEFINED),
                    ): PEM_CERT_SELECTOR,
                    vol.Required(
                        CONF_CLIENT_KEY,
                        default=(user_input or {}).get(CONF_CLIENT_KEY, vol.UNDEFINED),
                    ): PEM_KEY_SELECTOR,
                },
            ),
            errors=_errors,
        )

    async def async_step_reconfigure(
        self,
        user_input: dict | None = None,
    ) -> config_entries.ConfigFlowResult:
        """
        Handle reconfiguration flow.

        Allows updating connection settings for an existing integration instance.
        Reuses the same form as initial setup but preserves current values.
        """
        if is_reconfigure := (self.source == SOURCE_RECONFIGURE):
            reconfigure_entry = self._get_reconfigure_entry()

        _errors = {}
        if user_input is not None:
            identification = await self.hass.async_add_executor_job(
                try_connection,
                user_input,
            )

            if identification and "macAddress" in identification:
                await self.async_set_unique_id(identification["macAddress"])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input[CONF_HOST],
                    data=user_input,
                )

            _errors["base"] = "cannot_connect"

        current_state = user_input or (reconfigure_entry.data if is_reconfigure else {})

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_HOST,
                        default=current_state.get(CONF_HOST, vol.UNDEFINED),
                    ): HOST_SELECTOR,
                    vol.Required(
                        CONF_PORT,
                        default=current_state.get(CONF_PORT, DEFAULT_PORT),
                    ): PORT_SELECTOR,
                    vol.Required(
                        CONF_SERVER_CERT,
                        default=current_state.get(CONF_SERVER_CERT, vol.UNDEFINED),
                    ): PEM_CERT_SELECTOR,
                    vol.Required(
                        CONF_CLIENT_CERT,
                        default=current_state.get(CONF_CLIENT_CERT, vol.UNDEFINED),
                    ): PEM_CERT_SELECTOR,
                    vol.Required(
                        CONF_CLIENT_KEY,
                        default=current_state.get(CONF_CLIENT_KEY, vol.UNDEFINED),
                    ): PEM_KEY_SELECTOR,
                },
            ),
            errors=_errors,
        )

    async def _test_credentials(
        self, host: str, port: str, server_cert: str, client_cert: str, client_key: str
    ) -> None:
        """
        Validate MQTT connection credentials.

        Tests connection to the UPS Network-M card using provided certificates.
        Raises appropriate exceptions for authentication or connection failures.
        """
        config = EatonUpsMqttClient(
            host=host,
            port=port,
            server_cert=server_cert,
            client_cert=client_cert,
            client_key=client_key,
        )
        client = EatonUpsMqttClient(
            config=config,
            session=async_create_clientsession(self.hass),
        )
        await client.async_get_data()


def try_connection(
    user_input: dict[str, Any],
) -> dict[str, Any] | None:
    """
    Test MQTT connection to UPS Network-M card and get identification data.

    Creates temporary certificate files and attempts MQTT connection.
    Returns the identification data if connection succeeds, None otherwise.
    """
    # We don't import on the top because some integrations
    # should be able to optionally rely on MQTT.
    import json
    import paho.mqtt.client as mqtt  # pylint: disable=import-outside-toplevel
    from homeassistant.components.mqtt.async_client import AsyncMQTTClient

    client_id = mqtt.base62(uuid.uuid4().int, padding=22)
    client = AsyncMQTTClient(
        client_id,
        protocol=mqtt.MQTTv31,
        reconnect_on_failure=False,
    )

    result: queue.Queue[dict[str, Any] | None] = queue.Queue(maxsize=1)
    identification_received = False

    def on_connect(
        client: mqtt.Client,
        _userdata: None,
        _flags: dict[str, Any],
        result_code: int,
        _properties: mqtt.Properties | None = None,
    ) -> None:
        """Handle connection result."""
        if result_code == mqtt.CONNACK_ACCEPTED:
            client.subscribe("mbdetnrs/1.0/managers/1/identification")
        else:
            result.put(None)

    def on_message(
        _client: mqtt.Client,
        _userdata: None,
        msg: mqtt.MQTTMessage,
    ) -> None:
        """Handle received messages."""
        nonlocal identification_received
        if msg.topic == "mbdetnrs/1.0/managers/1/identification":
            try:
                identification = json.loads(msg.payload)
                result.put(identification)
                identification_received = True
            except json.JSONDecodeError:
                result.put(None)

    client.on_connect = on_connect
    client.on_message = on_message

    def on_connect_fail(
        _client: mqtt.Client,
        _userdata: None,
    ) -> None:
        """Handle connection failure."""
        result.put(None)

    client.on_connect_fail = on_connect_fail

    # Write PEM strings to temporary files
    with tempfile.NamedTemporaryFile(delete=False) as server_cert_file:
        server_cert_file.write(user_input[CONF_SERVER_CERT].encode())
    with tempfile.NamedTemporaryFile(delete=False) as client_cert_file:
        client_cert_file.write(user_input[CONF_CLIENT_CERT].encode())
    with tempfile.NamedTemporaryFile(delete=False) as client_key_file:
        client_key_file.write(user_input[CONF_CLIENT_KEY].encode())

    try:
        # Set up TLS/SSL certificates
        client.tls_set(
            ca_certs=server_cert_file.name,
            certfile=client_cert_file.name,
            keyfile=client_key_file.name,
        )
        client.tls_insecure_set(insecure=False)
        client.enable_logger(logger)

        client.connect_async(host=user_input[CONF_HOST], port=user_input[CONF_PORT])
        client.loop_start()

        try:
            identification = result.get(timeout=MQTT_TIMEOUT)
            if not identification_received:
                return None
            return identification
        except queue.Empty:
            return None
        finally:
            client.disconnect()
            client.loop_stop()

    finally:
        # Clean up temporary files
        Path(server_cert_file.name).unlink()
        Path(client_cert_file.name).unlink()
        Path(client_key_file.name).unlink()
