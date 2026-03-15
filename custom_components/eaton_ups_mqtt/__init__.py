"""
Custom integration to integrate Eaton UPS with Home Assistant.

For more details about this integration, please refer to
https://github.com/lnagel/hass-eaton-ups
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from aiohttp import web
from homeassistant.components.http import HomeAssistantView
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.issue_registry import (
    IssueSeverity,
    async_create_issue,
    async_delete_issue,
)
from homeassistant.loader import async_get_loaded_integration

from .api import EatonUpsMqttClient, EatonUpsMqttConfig
from .certificates import (
    async_fetch_server_certificate,
    async_generate_client_certificate,
)
from .const import (
    CERT_DOWNLOAD_STEP_LINK,
    CERT_UPLOAD_INSTRUCTIONS,
    CONF_CLIENT_CERT,
    CONF_CLIENT_KEY,
    CONF_SERVER_CERT,
    DOMAIN,
    LOGGER,
)
from .coordinator import EatonUPSDataUpdateCoordinator
from .data import EatonUpsData

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import EatonUpsConfigEntry

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
]

ISSUE_ID_CERT_UPLOAD = "cert_upload_{entry_id}"


# https://developers.home-assistant.io/docs/config_entries_index/#setting-up-an-entry
async def async_setup_entry(
    hass: HomeAssistant,
    entry: EatonUpsConfigEntry,
) -> bool:
    """Set up this integration using UI."""
    # Auto-generate certificates if missing
    data = dict(entry.data)
    certs_generated = False

    if not data.get(CONF_SERVER_CERT):
        try:
            data[CONF_SERVER_CERT] = await async_fetch_server_certificate(
                hass, data[CONF_HOST], data[CONF_PORT]
            )
        except (OSError, TimeoutError) as err:
            msg = (
                f"Failed to fetch server certificate"
                f" from {data[CONF_HOST]}:{data[CONF_PORT]}"
            )
            raise ConfigEntryNotReady(msg) from err
        certs_generated = True

    if not data.get(CONF_CLIENT_CERT) or not data.get(CONF_CLIENT_KEY):
        cert_pem, key_pem = await async_generate_client_certificate(hass)
        if not data.get(CONF_CLIENT_CERT):
            data[CONF_CLIENT_CERT] = cert_pem
        if not data.get(CONF_CLIENT_KEY):
            data[CONF_CLIENT_KEY] = key_pem
        certs_generated = True

    if certs_generated:
        hass.config_entries.async_update_entry(entry, data=data)

    # Register HTTP view for certificate download
    hass.http.register_view(ClientCertDownloadView())

    issue_id = ISSUE_ID_CERT_UPLOAD.format(entry_id=entry.entry_id)
    host = data[CONF_HOST]

    if certs_generated:
        # Don't attempt MQTT connection — user needs to upload the client
        # cert to the UPS first. HA will retry automatically.
        _create_cert_upload_issue(hass, entry, host, issue_id)
        msg = "Waiting for client certificate to be uploaded to UPS"
        raise ConfigEntryNotReady(msg)

    coordinator = EatonUPSDataUpdateCoordinator(
        hass=hass,
        logger=LOGGER,
        name=DOMAIN,
    )
    config = EatonUpsMqttConfig(
        host=host,
        port=data[CONF_PORT],
        server_cert=data[CONF_SERVER_CERT],
        client_cert=data[CONF_CLIENT_CERT],
        client_key=data[CONF_CLIENT_KEY],
    )
    entry.runtime_data = EatonUpsData(
        client=EatonUpsMqttClient(config=config, session=async_get_clientsession(hass)),
        integration=async_get_loaded_integration(hass, entry.domain),
        coordinator=coordinator,
    )

    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception:
        # Connection failed — show cert upload instructions
        _create_cert_upload_issue(hass, entry, host, issue_id)
        raise

    # Connection succeeded — delete any pending cert upload issue
    async_delete_issue(hass, DOMAIN, issue_id)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: EatonUpsConfigEntry,
) -> bool:
    """Handle removal of an entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(
    hass: HomeAssistant,
    entry: EatonUpsConfigEntry,
) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


def _get_download_url(hass: HomeAssistant, entry_id: str) -> str:
    """Build absolute download URL for the client certificate."""
    path = f"/api/eaton_ups_mqtt/client_cert/{entry_id}"
    try:
        from homeassistant.helpers.network import get_url  # noqa: PLC0415

        return f"{get_url(hass, allow_external=False)}{path}"
    except Exception:  # noqa: BLE001
        return path


def _create_cert_upload_issue(
    hass: HomeAssistant,
    entry: EatonUpsConfigEntry,
    host: str,
    issue_id: str,
) -> None:
    """Create a repairs issue with client certificate upload instructions."""
    async_create_issue(
        hass,
        DOMAIN,
        issue_id,
        is_fixable=False,
        severity=IssueSeverity.WARNING,
        translation_key="cert_upload_required",
        translation_placeholders={
            "instructions": CERT_UPLOAD_INSTRUCTIONS.format(
                host=host,
                download_step=CERT_DOWNLOAD_STEP_LINK.format(
                    download_url=_get_download_url(hass, entry.entry_id),
                ),
            ),
        },
    )


class ClientCertDownloadView(HomeAssistantView):
    """View to download client certificate PEM file."""

    url = "/api/eaton_ups_mqtt/client_cert/{entry_id}"
    name = "api:eaton_ups_mqtt:client_cert"
    requires_auth = False

    async def get(self, request: web.Request, entry_id: str) -> web.Response:
        """Handle GET request for client certificate download."""
        hass: HomeAssistant = request.app["hass"]
        entry = hass.config_entries.async_get_entry(entry_id)

        if entry is None or entry.domain != DOMAIN:
            return web.Response(status=404, text="Config entry not found")

        client_cert = entry.data.get(CONF_CLIENT_CERT, "")
        if not client_cert:
            return web.Response(status=404, text="No client certificate available")

        return web.Response(
            body=client_cert,
            content_type="application/x-pem-file",
            headers={
                "Content-Disposition": 'attachment; filename="eaton_ups_client.pem"',
            },
        )
