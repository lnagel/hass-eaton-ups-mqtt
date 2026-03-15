"""Certificate generation and fetching for Eaton UPS MQTT."""

from __future__ import annotations

import datetime
import ssl
from typing import TYPE_CHECKING
from urllib.parse import urlparse

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from .const import CERT_DEFAULT_CN, CERT_KEY_SIZE, CERT_VALIDITY_YEARS

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


def fetch_server_certificate(host: str, port: int) -> str:
    """Fetch the server's TLS certificate in PEM format."""
    return ssl.get_server_certificate((host, port))


def generate_client_certificate(common_name: str) -> tuple[str, str]:
    """
    Generate a self-signed client certificate and private key.

    Returns:
        Tuple of (certificate PEM, private key PEM).

    """
    key = rsa.generate_private_key(public_exponent=65537, key_size=CERT_KEY_SIZE)

    subject = issuer = x509.Name(
        [x509.NameAttribute(x509.oid.NameOID.COMMON_NAME, common_name)]
    )

    now = datetime.datetime.now(datetime.UTC)
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + datetime.timedelta(days=365 * CERT_VALIDITY_YEARS))
        .sign(key, hashes.SHA256())
    )

    cert_pem = cert.public_bytes(serialization.Encoding.PEM).decode()
    key_pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.TraditionalOpenSSL,
        serialization.NoEncryption(),
    ).decode()

    return cert_pem, key_pem


def get_common_name(hass: HomeAssistant) -> str:
    """
    Derive a common name for the client certificate.

    Uses the HA internal URL hostname, falling back to the domain name.
    """
    if hass.config.internal_url:
        hostname = urlparse(hass.config.internal_url).hostname
        if hostname:
            return hostname
    return CERT_DEFAULT_CN


async def async_fetch_server_certificate(
    hass: HomeAssistant, host: str, port: int
) -> str:
    """Fetch server certificate in executor."""
    return await hass.async_add_executor_job(fetch_server_certificate, host, port)


async def async_generate_client_certificate(
    hass: HomeAssistant,
) -> tuple[str, str]:
    """Generate client certificate in executor."""
    common_name = get_common_name(hass)
    return await hass.async_add_executor_job(generate_client_certificate, common_name)
