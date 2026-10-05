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

CERT_VALIDITY_YEARS = 15
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

CERT_PAIRING_INSTRUCTIONS = (
    "The Eaton UPS at **{host}** does not trust the client certificate yet."
    "\n\nTo let Home Assistant upload it automatically:"
    "\n1. Open **Settings \u2192 Certificate** in the UPS web interface at"
    " [https://{host}/settings/certificate](https://{host}/settings/certificate)"
    "\n2. Under **Pairing with clients**, choose how long to trust new client"
    " certificates and click **Start**"
    "\n\nThe certificate is uploaded on the next connection attempt."
    " Reload the integration to retry immediately."
    "\n\nAlternatively, import it manually:"
    "\n1. {download_step}"
    "\n2. On the same page, under **Trusted remote certificates**,"
    " click **Import**"
    "\n3. Select **Protected applications (MQTT)** and import the downloaded file"
)

CERT_DOWNLOAD_STEP_LINK = (
    "Right-click [this link]({download_url}) and **Save link as** to"
    " download the client certificate"
)
CERT_DOWNLOAD_STEP_REPAIRS = (
    "Check **Settings \u2192 System \u2192 Repairs** to download the client certificate"
)

# Seconds to wait for each request to the certificate enrolment API
ENROLMENT_TIMEOUT = 10

MQTT_TIMEOUT = 5
MQTT_CONNECTION_ATTEMPTS = 10
MQTT_PREFIX_V1 = "mbdetnrs/1.0/"
MQTT_PREFIX_V2 = "mbdetnrs/2.0/"
MQTT_SUPPORTED_PREFIXES = (MQTT_PREFIX_V1, MQTT_PREFIX_V2)

# Topics with this suffix carry continuously changing numeric readings
MQTT_MEASURES_SUFFIX = "/measures"

# Minimum seconds between state writes for measurement topics; 0 disables
CONF_DEBOUNCE_INTERVAL: Final = "debounce_interval"
DEFAULT_DEBOUNCE_INTERVAL = 5
MIN_DEBOUNCE_INTERVAL = 0
MAX_DEBOUNCE_INTERVAL = 300
STEP_DEBOUNCE_INTERVAL = 5
