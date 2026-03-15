"""Constants for eaton_ups_mqtt."""

from logging import Logger, getLogger
from typing import Final

LOGGER: Logger = getLogger(__package__)

DOMAIN = "eaton_ups_mqtt"
ATTRIBUTION = "Data provided by Eaton UPS"

CONF_SERVER_CERT: Final = "server_cert"
CONF_CLIENT_KEY: Final = "client_key"
CONF_CLIENT_CERT: Final = "client_cert"

DEFAULT_PORT = 8883

CERT_KEY_SIZE = 4096
CERT_VALIDITY_YEARS = 10
CERT_DEFAULT_CN = "Home Assistant"

CERT_UPLOAD_INSTRUCTIONS = (
    "A client certificate was auto-generated for your Eaton UPS at **{host}**."
    "\n\nTo complete setup:"
    "\n1. {download_step}"
    "\n2. Open the UPS web interface at [https://{host}](https://{host})"
    "\n3. Navigate to **Settings \u2192 Certificate**"
    " \u2192 **Trusted remote certificates**"
    "\n4. Click **Import**"
    "\n5. Select **Protected applications (MQTT)**"
    "\n6. Click **Browse** and select the downloaded file"
    "\n7. Click **Import**"
    "\n\nThe integration will automatically connect once the certificate"
    " is uploaded. You may need to reload the integration after uploading."
)

CERT_DOWNLOAD_STEP_LINK = "[Download the client certificate]({download_url})"
CERT_DOWNLOAD_STEP_REPAIRS = (
    "Check **Settings \u2192 System \u2192 Repairs** to download the client certificate"
)

MQTT_TIMEOUT = 5
MQTT_CONNECTION_ATTEMPTS = 10
MQTT_PREFIX = "mbdetnrs/1.0/"
