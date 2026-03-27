"""
Custom integration to integrate Eaton UPS with Home Assistant.

For more details about this integration, please refer to
https://github.com/lnagel/hass-eaton-ups
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.issue_registry import (
    IssueSeverity,
    async_create_issue,
    async_delete_issue,
)
from homeassistant.loader import async_get_loaded_integration

from .api import (
    EatonUpsClientAuthenticationError,
    EatonUpsMqttClient,
    EatonUpsMqttConfig,
)
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

    # Always save client cert to www/ for download via /local/ URL
    await hass.async_add_executor_job(
        _write_cert_file, hass.config.config_dir, entry.entry_id, data[CONF_CLIENT_CERT]
    )

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
        config_entry=entry,
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
    except Exception as err:
        # Only show cert upload instructions for authentication/TLS errors
        cause = err.__cause__ if err.__cause__ else err
        if isinstance(cause, EatonUpsClientAuthenticationError):
            _create_cert_upload_issue(hass, entry, host, issue_id)
        else:
            LOGGER.error("Failed to connect to UPS at %s: %s", host, err)
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
    await hass.config_entries.async_reload(entry.entry_id)


def _get_cert_filename(entry_id: str) -> str:
    """Get the client certificate filename for a config entry."""
    return f"eaton_ups_client_{entry_id}.pem"


def _write_cert_file(config_path: str, entry_id: str, client_cert: str) -> None:
    """Write client certificate PEM to www/ (runs in executor)."""
    www_dir = Path(config_path) / "www" / DOMAIN
    www_dir.mkdir(parents=True, exist_ok=True)
    cert_path = www_dir / _get_cert_filename(entry_id)
    cert_path.write_text(client_cert)


def _create_cert_upload_issue(
    hass: HomeAssistant,
    entry: EatonUpsConfigEntry,
    host: str,
    issue_id: str,
) -> None:
    """Create a repairs issue with client certificate upload instructions."""
    download_url = f"/local/{DOMAIN}/{_get_cert_filename(entry.entry_id)}"
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
                    download_url=download_url,
                ),
            ),
        },
    )
