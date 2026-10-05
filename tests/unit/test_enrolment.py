"""Tests for client certificate enrolment with the UPS network card."""

from __future__ import annotations

import asyncio
from functools import partial
from http import HTTPStatus

import aiohttp
import pytest
from pytest_homeassistant_custom_component.test_util.aiohttp import (
    AiohttpClientMocker,
    AiohttpClientMockResponse,
)

from custom_components.eaton_ups_mqtt.certificates import (
    generate_client_certificate,
    get_subject_hash,
)
from custom_components.eaton_ups_mqtt.enrolment import (
    EnrolmentResult,
    async_enrol_client_certificate,
)

HOST = "ups.example.local"
CLIENTS_URL = f"https://{HOST}/etn/v1/comm/certificates/mqtt/clients"
ACCEPTED = {"status": "accepted"}
NOT_FOUND = {"status": HTTPStatus.NOT_FOUND}


@pytest.fixture(scope="module")
def cert_pem() -> str:
    """Generate a client certificate."""
    return generate_client_certificate("test-host")[0]


@pytest.fixture
def status_url(cert_pem: str) -> str:
    """Return the status URL of the client certificate."""
    return f"{CLIENTS_URL}/{get_subject_hash(cert_pem)}.0"


@pytest.fixture
async def session(aioclient_mock: AiohttpClientMocker):
    """Create a client session answered by the mocker."""
    session = aioclient_mock.create_session(asyncio.get_running_loop())
    yield session
    await session.close()


@pytest.fixture
def enrol(session, cert_pem: str):
    """Return the enrolment call for the client certificate."""
    return partial(async_enrol_client_certificate, session, HOST, cert_pem)


class TestEnrolClientCertificate:
    """Tests for async_enrol_client_certificate."""

    async def test_already_accepted(self, aioclient_mock, enrol, status_url):
        """Test that an accepted certificate is not uploaded again."""
        aioclient_mock.get(status_url, json=ACCEPTED)

        assert await enrol() is EnrolmentResult.ACCEPTED
        assert aioclient_mock.call_count == 1

    async def test_uploads_unknown_certificate(
        self, aioclient_mock, enrol, status_url, cert_pem
    ):
        """Test that an unknown certificate is uploaded and then accepted."""
        responses = iter([NOT_FOUND, {"json": ACCEPTED}])

        async def next_status(method, url, _data):
            return AiohttpClientMockResponse(method, url, **next(responses))

        aioclient_mock.get(status_url, side_effect=next_status)
        aioclient_mock.post(CLIENTS_URL)

        assert await enrol() is EnrolmentResult.ENROLLED
        method, url, data, _headers = aioclient_mock.mock_calls[1]
        assert method == "POST"
        assert str(url) == CLIENTS_URL
        assert data == {"format": "PEM", "certificate": cert_pem}

    async def test_pairing_closed(self, aioclient_mock, enrol, status_url):
        """Test that a refused upload reports the pairing window as closed."""
        aioclient_mock.get(status_url, **NOT_FOUND)
        aioclient_mock.post(CLIENTS_URL, status=HTTPStatus.UNAUTHORIZED)

        assert await enrol() is EnrolmentResult.PAIRING_CLOSED

    @pytest.mark.parametrize(
        ("status", "upload_status"),
        [
            (NOT_FOUND, HTTPStatus.INTERNAL_SERVER_ERROR),
            ({"json": {"status": "pending"}}, HTTPStatus.OK),
        ],
    )
    async def test_upload_not_accepted(
        self, aioclient_mock, enrol, status_url, status, upload_status
    ):
        """Test that an upload the card does not accept is unavailable."""
        aioclient_mock.get(status_url, **status)
        aioclient_mock.post(CLIENTS_URL, status=upload_status)

        assert await enrol() is EnrolmentResult.UNAVAILABLE

    @pytest.mark.parametrize(
        "status",
        [
            {"status": HTTPStatus.UNAUTHORIZED},
            {"exc": aiohttp.ClientConnectionError("refused")},
            {"exc": TimeoutError},
            {"text": "not json"},
        ],
    )
    async def test_status_unavailable(self, aioclient_mock, enrol, status_url, status):
        """Test that a failing status request is reported as unavailable."""
        aioclient_mock.get(status_url, **status)

        assert await enrol() is EnrolmentResult.UNAVAILABLE
        assert aioclient_mock.call_count == 1

    async def test_invalid_certificate(self, aioclient_mock, session):
        """Test that an unparsable certificate is reported as unavailable."""
        result = await async_enrol_client_certificate(session, HOST, "not a cert")

        assert result is EnrolmentResult.UNAVAILABLE
        assert aioclient_mock.call_count == 0
