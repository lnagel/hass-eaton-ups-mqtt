"""Test constants for eaton_ups_mqtt."""

from custom_components.eaton_ups_mqtt.const import (
    ATTRIBUTION,
    CONF_CLIENT_CERT,
    CONF_CLIENT_KEY,
    CONF_SERVER_CERT,
    DEFAULT_PORT,
    DOMAIN,
    MQTT_CONNECTION_ATTEMPTS,
    MQTT_PREFIX,
    MQTT_TIMEOUT,
)


def test_domain():
    """Test domain constant."""
    assert DOMAIN == "eaton_ups_mqtt"


def test_attribution():
    """Test attribution constant."""
    assert ATTRIBUTION == "Data provided by Eaton UPS"


def test_conf_constants():
    """Test configuration constants."""
    assert CONF_SERVER_CERT == "server_cert"
    assert CONF_CLIENT_KEY == "client_key"
    assert CONF_CLIENT_CERT == "client_cert"


def test_default_port():
    """Test default port."""
    assert DEFAULT_PORT == 8883


def test_mqtt_constants():
    """Test MQTT constants."""
    assert MQTT_TIMEOUT == 5
    assert MQTT_CONNECTION_ATTEMPTS == 10
    assert MQTT_PREFIX == "mbdetnrs/1.0/"
