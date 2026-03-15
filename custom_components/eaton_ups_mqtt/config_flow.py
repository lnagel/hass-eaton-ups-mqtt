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
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .api import (
    EatonUpsClientAuthenticationError,
    EatonUpsClientCommunicationError,
    EatonUpsClientError,
    EatonUpsMqttClient,
    EatonUpsMqttConfig,
)
from .certificates import (
    async_fetch_server_certificate,
    async_generate_client_certificate,
)
from .const import (
    CONF_CLIENT_CERT,
    CONF_CLIENT_KEY,
    CONF_SERVER_CERT,
    DEFAULT_PORT,
    DOMAIN,
    LOGGER,
    MQTT_PREFIX,
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

        Prompts user for UPS hostname/IP and MQTT port only.
        Certificates are auto-generated during setup.
        """
        if user_input is not None:
            return self.async_create_entry(
                title=user_input[CONF_HOST],
                data={
                    CONF_HOST: user_input[CONF_HOST],
                    CONF_PORT: user_input[CONF_PORT],
                    CONF_SERVER_CERT: "",
                    CONF_CLIENT_CERT: "",
                    CONF_CLIENT_KEY: "",
                },
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
                },
            ),
            errors={},
        )

    async def async_step_reauth(
        self,
        _entry_data: dict[str, Any],
    ) -> config_entries.ConfigFlowResult:
        """Handle reauth triggered by ConfigEntryAuthFailed."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self,
        user_input: dict | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle reauth confirmation step."""
        reauth_entry = self._get_reauth_entry()
        _errors = {}

        if user_input is not None:
            final_data = dict(user_input)

            # Auto-generate certs for any cleared fields
            try:
                final_data = await self._auto_fill_certs(final_data)
            except (OSError, TimeoutError):
                _errors["base"] = "cert_fetch_failed"
            else:
                try:
                    await self._test_credentials(
                        host=final_data[CONF_HOST],
                        port=final_data[CONF_PORT],
                        server_cert=final_data[CONF_SERVER_CERT],
                        client_cert=final_data[CONF_CLIENT_CERT],
                        client_key=final_data[CONF_CLIENT_KEY],
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
                    return self.async_update_reload_and_abort(
                        reauth_entry,
                        data=final_data,
                    )

        current_state = user_input or reauth_entry.data

        return self.async_show_form(
            step_id="reauth_confirm",
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
                    vol.Optional(
                        CONF_SERVER_CERT,
                        default=current_state.get(CONF_SERVER_CERT, vol.UNDEFINED),
                    ): PEM_CERT_SELECTOR,
                    vol.Optional(
                        CONF_CLIENT_CERT,
                        default=current_state.get(CONF_CLIENT_CERT, vol.UNDEFINED),
                    ): PEM_CERT_SELECTOR,
                    vol.Optional(
                        CONF_CLIENT_KEY,
                        default=current_state.get(CONF_CLIENT_KEY, vol.UNDEFINED),
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
        """
        reconfigure_entry = self._get_reconfigure_entry()

        _errors = {}
        if user_input is not None:
            final_data = dict(user_input)

            # Auto-generate certs for any cleared fields
            try:
                final_data = await self._auto_fill_certs(final_data)
            except (OSError, TimeoutError):
                _errors["base"] = "cert_fetch_failed"
            else:
                identification = await self.hass.async_add_executor_job(
                    try_connection,
                    final_data,
                )

                if identification and "macAddress" in identification:
                    self.hass.config_entries.async_update_entry(
                        reconfigure_entry,
                        data=final_data,
                    )
                    return self.async_abort(reason="reauth_successful")

                _errors["base"] = "cannot_connect"

        current_state = user_input or reconfigure_entry.data

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
                    vol.Optional(
                        CONF_SERVER_CERT,
                        default=current_state.get(CONF_SERVER_CERT, vol.UNDEFINED),
                    ): PEM_CERT_SELECTOR,
                    vol.Optional(
                        CONF_CLIENT_CERT,
                        default=current_state.get(CONF_CLIENT_CERT, vol.UNDEFINED),
                    ): PEM_CERT_SELECTOR,
                    vol.Optional(
                        CONF_CLIENT_KEY,
                        default=current_state.get(CONF_CLIENT_KEY, vol.UNDEFINED),
                    ): PEM_KEY_SELECTOR,
                },
            ),
            errors=_errors,
        )

    async def _auto_fill_certs(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Auto-fill empty certificate fields.

        Fetches server cert and generates client cert/key for empty fields.
        """
        if not data.get(CONF_SERVER_CERT):
            data[CONF_SERVER_CERT] = await async_fetch_server_certificate(
                self.hass, data[CONF_HOST], data[CONF_PORT]
            )

        if not data.get(CONF_CLIENT_CERT) or not data.get(CONF_CLIENT_KEY):
            cert_pem, key_pem = await async_generate_client_certificate(self.hass)
            if not data.get(CONF_CLIENT_CERT):
                data[CONF_CLIENT_CERT] = cert_pem
            if not data.get(CONF_CLIENT_KEY):
                data[CONF_CLIENT_KEY] = key_pem

        return data

    async def _test_credentials(
        self, host: str, port: int, server_cert: str, client_cert: str, client_key: str
    ) -> None:
        """Validate MQTT connection credentials."""
        config = EatonUpsMqttConfig(
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
    import json  # noqa: PLC0415

    import paho.mqtt.client as mqtt  # noqa: PLC0415
    from homeassistant.components.mqtt.async_client import (  # noqa: PLC0415
        AsyncMQTTClient,
    )

    client_id = f"hass-eaton-ups-{uuid.uuid4()}"
    client = AsyncMQTTClient(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION1,
        client_id=client_id,
        protocol=mqtt.MQTTv31,
        reconnect_on_failure=False,
    )

    result: queue.Queue[dict[str, Any] | None] = queue.Queue(maxsize=1)

    def on_connect(
        client: mqtt.Client,
        _userdata: None,
        _flags: dict[str, Any],
        result_code: int,
        _properties: mqtt.Properties | None = None,
    ) -> None:
        """Handle connection result."""
        if result_code == mqtt.CONNACK_ACCEPTED:
            client.subscribe(MQTT_PREFIX + "managers/1/identification")
        else:
            result.put(None)

    def on_message(
        _client: mqtt.Client,
        _userdata: None,
        msg: mqtt.MQTTMessage,
    ) -> None:
        """Handle received messages."""
        if msg.topic == MQTT_PREFIX + "managers/1/identification":
            try:
                identification = json.loads(msg.payload)
                result.put(identification)
            except json.JSONDecodeError:
                result.put(None)

    client.on_connect = on_connect  # type: ignore[assignment]
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
        client.tls_insecure_set(value=False)
        client.enable_logger(logger)

        client.connect_async(host=user_input[CONF_HOST], port=user_input[CONF_PORT])
        client.loop_start()

        try:
            return result.get(timeout=MQTT_TIMEOUT)
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
