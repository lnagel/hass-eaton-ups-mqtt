"""Tests for TLS certificate pinning behavior.

These tests use real TLS handshakes via in-memory BIO to verify that:
1. The pinned server certificate is validated (chain verification works)
2. Hostname/CN verification is disabled (same cert works for any host)
3. A wrong server certificate is rejected

No network sockets are needed — ssl.MemoryBIO performs the TLS handshake
entirely in memory, testing real OpenSSL certificate validation logic.
"""

from __future__ import annotations

import contextlib
import datetime
import ssl
import tempfile
from pathlib import Path

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa


def _generate_self_signed_cert(cn: str) -> tuple[str, str]:
    """Generate a self-signed certificate with the given CN."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name([x509.NameAttribute(x509.oid.NameOID.COMMON_NAME, cn)])
    now = datetime.datetime.now(datetime.UTC)
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + datetime.timedelta(days=1))
        .sign(key, hashes.SHA256())
    )
    cert_pem = cert.public_bytes(serialization.Encoding.PEM).decode()
    key_pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.TraditionalOpenSSL,
        serialization.NoEncryption(),
    ).decode()
    return cert_pem, key_pem


def _write_temp_pem(content: str) -> str:
    """Write PEM content to a temporary file and return the path."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".pem", delete=False) as f:
        f.write(content)
        return f.name


def _make_server_context(
    server_cert_pem: str,
    server_key_pem: str,
    client_ca_pem: str,
) -> ssl.SSLContext:
    """Create a server SSL context with mutual TLS."""
    cert_file = _write_temp_pem(server_cert_pem)
    key_file = _write_temp_pem(server_key_pem)
    ca_file = _write_temp_pem(client_ca_pem)

    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(cert_file, key_file)
    ctx.load_verify_locations(ca_file)
    ctx.verify_mode = ssl.CERT_REQUIRED

    for f in (cert_file, key_file, ca_file):
        Path(f).unlink()
    return ctx


def _make_client_context(
    ca_pem: str,
    client_cert_pem: str,
    client_key_pem: str,
    *,
    check_hostname: bool,
) -> ssl.SSLContext:
    """Create a client SSL context matching the integration's TLS setup.

    This mirrors what paho-mqtt does internally when tls_set() and
    tls_insecure_set() are called:
    - tls_set(ca_certs=...) -> load_verify_locations + CERT_REQUIRED
    - tls_insecure_set(True) -> check_hostname = False
    - tls_insecure_set(False) -> check_hostname = True
    """
    ca_file = _write_temp_pem(ca_pem)
    cert_file = _write_temp_pem(client_cert_pem)
    key_file = _write_temp_pem(client_key_pem)

    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.load_verify_locations(ca_file)
    ctx.load_cert_chain(cert_file, key_file)
    ctx.verify_mode = ssl.CERT_REQUIRED
    ctx.check_hostname = check_hostname

    for f in (ca_file, cert_file, key_file):
        Path(f).unlink()
    return ctx


def _do_tls_handshake(
    server_ctx: ssl.SSLContext,
    client_ctx: ssl.SSLContext,
    server_hostname: str,
) -> None:
    """Perform a TLS handshake using in-memory BIO (no sockets needed).

    Raises ssl.SSLError or ssl.SSLCertVerificationError on failure.
    """
    # Create in-memory transport pairs
    incoming_from_client = ssl.MemoryBIO()
    outgoing_to_client = ssl.MemoryBIO()
    incoming_from_server = ssl.MemoryBIO()
    outgoing_to_server = ssl.MemoryBIO()

    server_obj = server_ctx.wrap_bio(
        incoming_from_client,
        outgoing_to_client,
        server_side=True,
    )
    client_obj = client_ctx.wrap_bio(
        incoming_from_server,
        outgoing_to_server,
        server_side=False,
        server_hostname=server_hostname,
    )

    # Drive the handshake by passing data between client and server BIOs
    for _ in range(50):  # Max iterations to prevent infinite loops
        # Try client handshake step
        try:
            client_obj.do_handshake()
        except ssl.SSLWantReadError:
            pass
        else:
            # Client handshake complete, flush remaining data to server
            data = outgoing_to_server.read()
            if data:
                incoming_from_client.write(data)
            with contextlib.suppress(ssl.SSLWantReadError):
                server_obj.do_handshake()
            return  # Success

        # Transfer client -> server
        data = outgoing_to_server.read()
        if data:
            incoming_from_client.write(data)

        # Try server handshake step
        with contextlib.suppress(ssl.SSLWantReadError):
            server_obj.do_handshake()

        # Transfer server -> client
        data = outgoing_to_client.read()
        if data:
            incoming_from_server.write(data)

    msg = "TLS handshake did not complete within iteration limit"
    raise RuntimeError(msg)


@pytest.fixture
def server_cert_pair():
    """Generate a server certificate with CN=ups.example.local."""
    return _generate_self_signed_cert("ups.example.local")


@pytest.fixture
def client_cert_pair():
    """Generate a client certificate."""
    return _generate_self_signed_cert("client")


@pytest.fixture
def wrong_cert_pair():
    """Generate a different server certificate (not the pinned one)."""
    return _generate_self_signed_cert("wrong-server")


class TestTlsCertificatePinning:
    """Test real TLS behavior with certificate pinning.

    These tests perform real TLS handshakes via in-memory BIO to verify
    certificate pinning at the OpenSSL level — not mock assertions.
    """

    def test_pinned_cert_accepted_when_connecting_by_ip(
        self, server_cert_pair, client_cert_pair
    ):
        """Test that connecting by IP works when hostname verification is off.

        The server cert has CN=ups.example.local but we connect using
        server_hostname="127.0.0.1". With check_hostname=False (equivalent
        to tls_insecure_set=True), the handshake succeeds because only the
        certificate chain is checked, not the CN/SAN.
        """
        server_cert, server_key = server_cert_pair
        client_cert, client_key = client_cert_pair

        server_ctx = _make_server_context(server_cert, server_key, client_cert)
        client_ctx = _make_client_context(
            server_cert, client_cert, client_key, check_hostname=False
        )

        # Should NOT raise — hostname mismatch is ignored
        _do_tls_handshake(server_ctx, client_ctx, server_hostname="127.0.0.1")

    def test_pinned_cert_accepted_with_matching_hostname(
        self, server_cert_pair, client_cert_pair
    ):
        """Test that connecting by hostname works when hostname verification is off."""
        server_cert, server_key = server_cert_pair
        client_cert, client_key = client_cert_pair

        server_ctx = _make_server_context(server_cert, server_key, client_cert)
        client_ctx = _make_client_context(
            server_cert, client_cert, client_key, check_hostname=False
        )

        _do_tls_handshake(server_ctx, client_ctx, server_hostname="ups.example.local")

    def test_hostname_mismatch_rejected_when_verification_enabled(
        self, server_cert_pair, client_cert_pair
    ):
        """Test that hostname verification rejects CN mismatch.

        With check_hostname=True (tls_insecure_set=False), connecting with
        server_hostname="127.0.0.1" when cert CN=ups.example.local must fail.
        This proves that tls_insecure_set controls hostname checking.
        """
        server_cert, server_key = server_cert_pair
        client_cert, client_key = client_cert_pair

        server_ctx = _make_server_context(server_cert, server_key, client_cert)
        client_ctx = _make_client_context(
            server_cert, client_cert, client_key, check_hostname=True
        )

        with pytest.raises(ssl.SSLCertVerificationError):
            _do_tls_handshake(server_ctx, client_ctx, server_hostname="127.0.0.1")

    def test_wrong_server_cert_rejected(
        self, server_cert_pair, client_cert_pair, wrong_cert_pair
    ):
        """Test that a non-pinned server certificate is rejected.

        Even with hostname verification disabled (check_hostname=False),
        the certificate chain must still be validated. A server presenting
        a different certificate than the pinned one must be rejected.
        This confirms tls_insecure_set(True) does NOT disable chain validation.
        """
        server_cert, server_key = server_cert_pair
        client_cert, client_key = client_cert_pair
        wrong_cert, _wrong_key = wrong_cert_pair

        server_ctx = _make_server_context(server_cert, server_key, client_cert)
        # Pin the WRONG cert as CA — server presents a different one
        client_ctx = _make_client_context(
            wrong_cert, client_cert, client_key, check_hostname=False
        )

        with pytest.raises(ssl.SSLCertVerificationError):
            _do_tls_handshake(
                server_ctx, client_ctx, server_hostname="ups.example.local"
            )
