"""Tests for certificate generation and fetching."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from cryptography import x509
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import load_pem_private_key

from custom_components.eaton_ups_mqtt.certificates import (
    async_fetch_server_certificate,
    async_generate_client_certificate,
    fetch_server_certificate,
    generate_client_certificate,
    get_common_name,
)
from custom_components.eaton_ups_mqtt.const import CERT_KEY_SIZE, CERT_VALIDITY_YEARS


class TestGenerateClientCertificate:
    """Tests for generate_client_certificate."""

    def test_returns_pem_strings(self):
        """Test that generated cert and key are valid PEM strings."""
        cert_pem, key_pem = generate_client_certificate("test-host")

        assert cert_pem.startswith("-----BEGIN CERTIFICATE-----")
        assert cert_pem.strip().endswith("-----END CERTIFICATE-----")
        assert key_pem.startswith("-----BEGIN RSA PRIVATE KEY-----")
        assert key_pem.strip().endswith("-----END RSA PRIVATE KEY-----")

    def test_correct_key_size(self):
        """Test that the generated key has the correct size."""
        _cert_pem, key_pem = generate_client_certificate("test-host")

        key = load_pem_private_key(key_pem.encode(), password=None)
        assert isinstance(key, rsa.RSAPrivateKey)
        assert key.key_size == CERT_KEY_SIZE

    def test_correct_subject_cn(self):
        """Test that the certificate has the correct common name."""
        cert_pem, _key_pem = generate_client_certificate("my-ha-instance")

        cert = x509.load_pem_x509_certificate(cert_pem.encode())
        cn = cert.subject.get_attributes_for_oid(x509.oid.NameOID.COMMON_NAME)[0].value
        assert cn == "my-ha-instance"

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
        assert "BEGIN RSA PRIVATE KEY" in key_pem
