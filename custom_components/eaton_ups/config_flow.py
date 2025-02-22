"""Adds config flow for Blueprint."""

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_PORT, CONF_HOST
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from slugify import slugify

from .api import (
    IntegrationBlueprintApiClient,
    IntegrationBlueprintApiClientAuthenticationError,
    IntegrationBlueprintApiClientCommunicationError,
    IntegrationBlueprintApiClientError,
)
from .const import DOMAIN, LOGGER, DEFAULT_PORT, CONF_SERVER_CERT, CONF_CLIENT_CERT, CONF_CLIENT_KEY

HOST_SELECTOR = selector.TextSelector(
    selector.TextSelectorConfig(
        type=selector.TextSelectorType.TEXT,
    ),
)
PORT_SELECTOR = vol.All(
    selector.NumberSelector(selector.NumberSelectorConfig(mode=selector.NumberSelectorMode.BOX, min=1, max=65535)),
    vol.Coerce(int),
)
PEM_CERT_SELECTOR = selector.TextSelector(
    selector.TextSelectorConfig(
        multiline=True, type=selector.TextSelectorType.TEXT,
    ),
)
PEM_KEY_SELECTOR = selector.TextSelector(
    selector.TextSelectorConfig(
        multiline=True, type=selector.TextSelectorType.TEXT,
    ),
)

class BlueprintFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Blueprint."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle a flow initialized by the user."""
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
            except IntegrationBlueprintApiClientAuthenticationError as exception:
                LOGGER.warning(exception)
                _errors["base"] = "auth"
            except IntegrationBlueprintApiClientCommunicationError as exception:
                LOGGER.error(exception)
                _errors["base"] = "connection"
            except IntegrationBlueprintApiClientError as exception:
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
                        default=(user_input or {}).get(CONF_PORT, DEFAULT_PORT)
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

    async def _test_credentials(self, host: str, port: str, server_cert: str, client_cert: str, client_key: str) -> None:
        """Validate credentials."""
        client = IntegrationBlueprintApiClient(
            host=host,
            port=port,
            server_cert=server_cert,
            client_cert=client_cert,
            client_key=client_key,
            session=async_create_clientsession(self.hass),
        )
        await client.async_get_data()
