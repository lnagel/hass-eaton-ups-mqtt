"""Config flow for Eaton UPS integration."""

from __future__ import annotations

import logging
import queue
import re
import ssl
import tempfile
import uuid
from dataclasses import dataclass
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


@dataclass
class ConnectionResult:
    """Result of a try_connection attempt."""

    identification: dict[str, Any] | None = None
    error_key: str | None = None
    error_detail: str | None = None


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
                conn_result = await self.hass.async_add_executor_job(
                    try_connection,
                    final_data,
                )

                if (
                    conn_result.identification
                    and "macAddress" in conn_result.identification
                ):
                    return self.async_update_reload_and_abort(
                        reconfigure_entry,
                        data=final_data,
                    )

                logger.error(
                    "Reconfigure connection test failed: %s",
                    conn_result.error_detail,
                )
                _errors["base"] = conn_result.error_key

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


def _write_temp_cert(content: str) -> str:
    """Write a PEM string to a temporary file and return its path."""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(content.encode())
        return f.name


def try_connection(  # noqa: PLR0911
    user_input: dict[str, Any],
) -> ConnectionResult:
    """
    Test MQTT connection to UPS Network-M card and get identification data.

    Creates temporary certificate files and attempts MQTT connection.
    Returns a ConnectionResult with identification data or error details.
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

    result: queue.Queue[ConnectionResult] = queue.Queue(maxsize=1)

    def on_connect(
        client: mqtt.Client,
        _userdata: None,
        _flags: dict[str, Any],
        result_code: int,
        _properties: mqtt.Properties | None = None,
    ) -> None:
        """Handle connection result."""
        if result_code == mqtt.CONNACK_ACCEPTED:
            client.subscribe("mbdetnrs/+/managers/1/identification")
        else:
            result.put(
                ConnectionResult(
                    error_key="mqtt_connect_refused",
                    error_detail=(
                        f"MQTT broker refused connection:"
                        f" {mqtt.connack_string(result_code)}"
                    ),
                )
            )

    def on_message(
        _client: mqtt.Client,
        _userdata: None,
        msg: mqtt.MQTTMessage,
    ) -> None:
        """Handle received messages."""
        if re.match(r"^mbdetnrs/\d+\.\d+/managers/1/identification$", msg.topic):
            try:
                identification = json.loads(msg.payload)
                result.put(ConnectionResult(identification=identification))
            except json.JSONDecodeError as e:
                result.put(
                    ConnectionResult(
                        error_key="invalid_response",
                        error_detail=f"UPS returned invalid JSON: {e}",
                    )
                )

    client.on_connect = on_connect  # type: ignore[assignment]
    client.on_message = on_message

    # Write PEM strings to temporary files
    temp_files = [
        _write_temp_cert(user_input[CONF_SERVER_CERT]),
        _write_temp_cert(user_input[CONF_CLIENT_CERT]),
        _write_temp_cert(user_input[CONF_CLIENT_KEY]),
    ]
    host = user_input[CONF_HOST]
    port = user_input[CONF_PORT]

    try:
        client.tls_set(
            ca_certs=temp_files[0],
            certfile=temp_files[1],
            keyfile=temp_files[2],
        )
        # Disable hostname verification since we pin the server certificate.
        # This allows connecting by either hostname or IP address with the
        # same certificate, regardless of the certificate's CN/SAN fields.
        client.tls_insecure_set(value=True)
        client.enable_logger(logger)

        # Use synchronous connect() so TLS/network errors raise directly
        client.connect(host=host, port=port)
        client.loop_start()

        try:
            return result.get(timeout=MQTT_TIMEOUT)
        except queue.Empty:
            return ConnectionResult(
                error_key="no_data_received",
                error_detail=(
                    f"Connected to {host}:{port} but no identification"
                    f" data received within {MQTT_TIMEOUT}s"
                ),
            )
        finally:
            client.disconnect()
            client.loop_stop()

    except ssl.SSLCertVerificationError as e:
        return ConnectionResult(
            error_key="server_cert_mismatch",
            error_detail=f"Server cert verification failed for {host}:{port}: {e}",
        )
    except ssl.SSLError as e:
        return ConnectionResult(
            error_key="tls_handshake_failed",
            error_detail=f"TLS handshake failed with {host}:{port}: {e}",
        )
    except ConnectionRefusedError as e:
        return ConnectionResult(
            error_key="connection_refused",
            error_detail=f"Connection refused by {host}:{port}: {e}",
        )
    except TimeoutError as e:
        return ConnectionResult(
            error_key="connection_timeout",
            error_detail=f"Connection to {host}:{port} timed out: {e}",
        )
    except OSError as e:
        return ConnectionResult(
            error_key="host_unreachable",
            error_detail=f"Cannot reach {host}:{port}: {e}",
        )

    finally:
        for path in temp_files:
            Path(path).unlink()
