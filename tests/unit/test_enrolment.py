"""Tests for client certificate enrolment with the UPS network card."""

from __future__ import annotations

from http import HTTPStatus

import aiohttp
import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
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


@pytest.fixture(scope="module")
def cert_pem() -> str:
    """Generate a client certificate."""
    return generate_client_certificate("test-host")[0]


@pytest.fixture
def status_url(cert_pem: str) -> str:
    """Return the status URL of the client certificate."""
    return f"{CLIENTS_URL}/{get_subject_hash(cert_pem)}.0"


def _mock_status_sequence(
    aioclient_mock: AiohttpClientMocker, status_url: str, *responses: dict
) -> None:
    """Answer successive status requests with the given responses."""
    pending = iter(responses)

    async def _next_response(method, url, _data):
        return AiohttpClientMockResponse(method, url, **next(pending))

    aioclient_mock.get(status_url, side_effect=_next_response)


async def _enrol(hass: HomeAssistant, cert_pem: str) -> EnrolmentResult:
    session = async_get_clientsession(hass, verify_ssl=False)
    return await async_enrol_client_certificate(session, HOST, cert_pem)


async def test_already_accepted(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    cert_pem: str,
    status_url: str,
):
    """Test that an accepted certificate is not uploaded again."""
    aioclient_mock.get(status_url, json=ACCEPTED)

    assert await _enrol(hass, cert_pem) is EnrolmentResult.ACCEPTED
    assert aioclient_mock.call_count == 1


async def test_uploads_unknown_certificate(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    cert_pem: str,
    status_url: str,
):
    """Test that an unknown certificate is uploaded and then accepted."""
    _mock_status_sequence(
        aioclient_mock,
        status_url,
        {"status": HTTPStatus.NOT_FOUND},
        {"json": ACCEPTED},
    )
    aioclient_mock.post(CLIENTS_URL)

    assert await _enrol(hass, cert_pem) is EnrolmentResult.ENROLLED

    method, url, data, _headers = aioclient_mock.mock_calls[1]
    assert method == "POST"
    assert str(url) == CLIENTS_URL
    assert data == {"format": "PEM", "certificate": cert_pem}


async def test_pairing_closed(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    cert_pem: str,
    status_url: str,
):
    """Test that a refused upload reports the pairing window as closed."""
    aioclient_mock.get(status_url, status=HTTPStatus.NOT_FOUND)
    aioclient_mock.post(CLIENTS_URL, status=HTTPStatus.UNAUTHORIZED)

    assert await _enrol(hass, cert_pem) is EnrolmentResult.PAIRING_CLOSED


async def test_upload_error(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    cert_pem: str,
    status_url: str,
):
    """Test that a failed upload is reported as unavailable."""
    aioclient_mock.get(status_url, status=HTTPStatus.NOT_FOUND)
    aioclient_mock.post(CLIENTS_URL, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    assert await _enrol(hass, cert_pem) is EnrolmentResult.UNAVAILABLE


async def test_upload_not_accepted(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    cert_pem: str,
    status_url: str,
):
    """Test that an upload the card does not accept is reported as unavailable."""
    aioclient_mock.get(status_url, json={"status": "pending"})
    aioclient_mock.post(CLIENTS_URL)

    assert await _enrol(hass, cert_pem) is EnrolmentResult.UNAVAILABLE


@pytest.mark.parametrize(
    "status_kwargs",
    [
        {"status": HTTPStatus.UNAUTHORIZED},
        {"exc": aiohttp.ClientConnectionError("refused")},
        {"exc": TimeoutError},
        {"text": "not json"},
    ],
)
async def test_status_unavailable(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    cert_pem: str,
    status_url: str,
    status_kwargs: dict,
):
    """Test that a failing status request is reported as unavailable."""
    aioclient_mock.get(status_url, **status_kwargs)

    assert await _enrol(hass, cert_pem) is EnrolmentResult.UNAVAILABLE
    assert aioclient_mock.call_count == 1


async def test_invalid_certificate(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
):
    """Test that an unparsable certificate is reported as unavailable."""
    result = await _enrol(hass, "not a certificate")

    assert result is EnrolmentResult.UNAVAILABLE
    assert aioclient_mock.call_count == 0
