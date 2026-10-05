"""Tests for certificate generation and fetching."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import load_pem_private_key

from custom_components.eaton_ups_mqtt.certificates import (
    async_fetch_server_certificate,
    async_generate_client_certificate,
    fetch_server_certificate,
    generate_client_certificate,
    get_common_name,
    get_subject_hash,
)
from custom_components.eaton_ups_mqtt.const import CERT_VALIDITY_YEARS

TEST_HOST_CERT = """-----BEGIN CERTIFICATE-----
MIIBFTCBu6ADAgECAgEBMAoGCCqGSM49BAMEMBQxEjAQBgNVBAMMCXRlc3QtaG9z
dDAeFw0yNjAxMDEwMDAwMDBaFw00MDEyMjgwMDAwMDBaMBQxEjAQBgNVBAMMCXRl
c3QtaG9zdDBZMBMGByqGSM49AgEGCCqGSM49AwEHA0IABAiOcDL5nL8zjSm7KvM2
gD0pEamtaL6J7ebIuSTd0XNosnm+hs61O63NnImnYSGL58u3LbaDiIqFpPnEvpB6
jxEwCgYIKoZIzj0EAwQDSQAwRgIhAJsWHOAg0/ehfNZ3t77laUFdWWs7wadoA9Wn
lmK9giWuAiEA53Cl+B0cCXeMShf0dJPKI7Q7fOrGOJjCNB8bRfC9S2c=
-----END CERTIFICATE-----
"""


def _get_cn(cert: x509.Certificate) -> str:
    """Return the common name of a certificate."""
    return cert.subject.get_attributes_for_oid(x509.oid.NameOID.COMMON_NAME)[0].value


class TestGenerateClientCertificate:
    """Tests for generate_client_certificate."""

    def test_returns_pem_strings(self):
        """Test that generated cert and key are valid PEM strings."""
        cert_pem, key_pem = generate_client_certificate("test-host")

        assert cert_pem.startswith("-----BEGIN CERTIFICATE-----")
        assert cert_pem.strip().endswith("-----END CERTIFICATE-----")
        assert key_pem.startswith("-----BEGIN EC PRIVATE KEY-----")
        assert key_pem.strip().endswith("-----END EC PRIVATE KEY-----")

    def test_correct_key_type(self):
        """Test that the generated key is an EC key on the P-256 curve."""
        _cert_pem, key_pem = generate_client_certificate("test-host")

        key = load_pem_private_key(key_pem.encode(), password=None)
        assert isinstance(key, ec.EllipticCurvePrivateKey)
        assert isinstance(key.curve, ec.SECP256R1)

    def test_certificate_matches_key(self):
        """Test that the certificate carries the generated key's public key."""
        cert_pem, key_pem = generate_client_certificate("test-host")

        cert = x509.load_pem_x509_certificate(cert_pem.encode())
        key = load_pem_private_key(key_pem.encode(), password=None)
        assert cert.public_key() == key.public_key()

    def test_signed_with_sha512(self):
        """Test that the certificate is signed with ECDSA using SHA-512."""
        cert_pem, _key_pem = generate_client_certificate("test-host")

        cert = x509.load_pem_x509_certificate(cert_pem.encode())
        assert isinstance(cert.signature_hash_algorithm, hashes.SHA512)

    def test_subject_cn_has_public_key_hash(self):
        """Test that the common name ends with the start of the public key hash."""
        cert_pem, _key_pem = generate_client_certificate("my-ha-instance")

        cert = x509.load_pem_x509_certificate(cert_pem.encode())
        key_hash = x509.SubjectKeyIdentifier.from_public_key(cert.public_key()).digest
        assert _get_cn(cert) == f"my-ha-instance-{key_hash.hex()[:8]}"

    def test_long_common_name_is_truncated(self):
        """Test that a long name is cut to fit the key hash in 64 characters."""
        cert_pem, _key_pem = generate_client_certificate("a" * 70)

        cn = _get_cn(x509.load_pem_x509_certificate(cert_pem.encode()))
        assert len(cn) == 64
        assert cn.startswith("a" * 55 + "-")

    def test_regenerated_certificate_has_own_subject_hash(self):
        """Test that two certificates for the same name differ in subject hash."""
        first, _key_pem = generate_client_certificate("test-host")
        second, _key_pem = generate_client_certificate("test-host")

        assert get_subject_hash(first) != get_subject_hash(second)

    def test_self_signed(self):
        """Test that the certificate is self-signed (issuer == subject)."""
        cert_pem, _key_pem = generate_client_certificate("test-host")

        cert = x509.load_pem_x509_certificate(cert_pem.encode())
        assert cert.issuer == cert.subject

    def test_validity_period(self):
        """Test that the certificate has approximately correct validity."""
        cert_pem, _key_pem = generate_client_certificate("test-host")

        cert = x509.load_pem_x509_certificate(cert_pem.encode())
        delta = cert.not_valid_after_utc - cert.not_valid_before_utc
        expected_days = 365 * CERT_VALIDITY_YEARS
        # Allow 1 day tolerance
        assert abs(delta.days - expected_days) <= 1


class TestGetSubjectHash:
    """Tests for get_subject_hash."""

    def test_matches_openssl_subject_hash(self):
        """Test the hash against `openssl x509 -subject_hash` for the same cert."""
        assert get_subject_hash(TEST_HOST_CERT) == "e61bb764"

    def test_rejects_invalid_pem(self):
        """Test that an unparsable certificate raises ValueError."""
        with pytest.raises(ValueError, match="PEM"):
            get_subject_hash("not a certificate")


class TestFetchServerCertificate:
    """Tests for fetch_server_certificate."""

    def test_fetches_certificate(self):
        """Test that server certificate is fetched via ssl."""
        mock_pem = "-----BEGIN CERTIFICATE-----\nMOCK\n-----END CERTIFICATE-----"

        with patch(
            "custom_components.eaton_ups_mqtt.certificates.ssl.get_server_certificate",
            return_value=mock_pem,
        ) as mock_get:
            result = fetch_server_certificate("ups.example.local", 8883)

        mock_get.assert_called_once_with(("ups.example.local", 8883))
        assert result == mock_pem

    def test_propagates_errors(self):
        """Test that SSL errors are propagated."""
        with (
            patch(
                "custom_components.eaton_ups_mqtt.certificates.ssl.get_server_certificate",
                side_effect=OSError("Connection refused"),
            ),
            pytest.raises(OSError, match="Connection refused"),
        ):
            fetch_server_certificate("bad-host", 8883)


class TestGetCommonName:
    """Tests for get_common_name."""

    def test_uses_internal_url_hostname(self):
        """Test that internal URL hostname is used when configured."""
        hass = MagicMock()
        hass.config.internal_url = "http://homeassistant.local:8123"

        result = get_common_name(hass)

        assert result == "homeassistant.local"

    def test_falls_back_to_domain(self):
        """Test fallback to domain name when internal URL is not set."""
        hass = MagicMock()
        hass.config.internal_url = None

        result = get_common_name(hass)

        assert result == "Home Assistant"

    def test_falls_back_when_url_has_no_hostname(self):
        """Test fallback when internal URL parsing yields no hostname."""
        hass = MagicMock()
        hass.config.internal_url = ""

        result = get_common_name(hass)

        assert result == "Home Assistant"


class TestAsyncWrappers:
    """Tests for async wrapper functions."""

    async def test_async_fetch_server_certificate(self):
        """Test async wrapper for fetch_server_certificate."""
        hass = MagicMock()
        mock_pem = "-----BEGIN CERTIFICATE-----\nMOCK\n-----END CERTIFICATE-----"

        async def mock_executor_job(func, *args):
            return func(*args)

        hass.async_add_executor_job = mock_executor_job

        with patch(
            "custom_components.eaton_ups_mqtt.certificates.ssl.get_server_certificate",
            return_value=mock_pem,
        ):
            result = await async_fetch_server_certificate(hass, "ups.local", 8883)

        assert result == mock_pem

    async def test_async_generate_client_certificate(self):
        """Test async wrapper for generate_client_certificate."""
        hass = MagicMock()
        hass.config.internal_url = "http://test.local:8123"

        async def mock_executor_job(func, *args):
            return func(*args)

        hass.async_add_executor_job = mock_executor_job

        cert_pem, key_pem = await async_generate_client_certificate(hass)

        assert "BEGIN CERTIFICATE" in cert_pem
        assert "BEGIN EC PRIVATE KEY" in key_pem
