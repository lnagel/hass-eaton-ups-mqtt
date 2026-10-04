"""Client certificate enrolment with the UPS network card."""

from __future__ import annotations

from enum import StrEnum
from http import HTTPStatus

import aiohttp
from yarl import URL

from .certificates import get_subject_hash
from .const import ENROLMENT_TIMEOUT, LOGGER

CLIENTS_PATH = "/etn/v1/comm/certificates/mqtt/clients"
STATUS_ACCEPTED = "accepted"
REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=ENROLMENT_TIMEOUT)


class EnrolmentResult(StrEnum):
    """Outcome of a client certificate enrolment attempt."""

    ACCEPTED = "accepted"
    """The card already trusted the certificate."""

    ENROLLED = "enrolled"
    """The certificate was uploaded and is now trusted."""

    PAIRING_CLOSED = "pairing_closed"
    """The card refused the upload because its pairing window is closed."""

    UNAVAILABLE = "unavailable"
    """The enrolment API could not be used."""


async def async_enrol_client_certificate(
    session: aiohttp.ClientSession, host: str, cert_pem: str
) -> EnrolmentResult:
    """Make sure the card trusts the client certificate, uploading it if needed."""
    try:
        clients_url = URL.build(scheme="https", host=host, path=CLIENTS_PATH)
        status_url = clients_url / f"{get_subject_hash(cert_pem)}.0"

        if await _async_is_accepted(session, status_url):
            return EnrolmentResult.ACCEPTED

        async with session.post(
            clients_url,
            json={"format": "PEM", "certificate": cert_pem},
            timeout=REQUEST_TIMEOUT,
        ) as response:
            if response.status == HTTPStatus.UNAUTHORIZED:
                return EnrolmentResult.PAIRING_CLOSED
            response.raise_for_status()

        if await _async_is_accepted(session, status_url):
            return EnrolmentResult.ENROLLED
    except (aiohttp.ClientError, TimeoutError, ValueError) as err:
        LOGGER.debug("Client certificate enrolment unavailable on %s: %s", host, err)
    return EnrolmentResult.UNAVAILABLE


async def _async_is_accepted(session: aiohttp.ClientSession, status_url: URL) -> bool:
    """Return whether the card reports the client certificate as accepted."""
    async with session.get(status_url, timeout=REQUEST_TIMEOUT) as response:
        if response.status == HTTPStatus.NOT_FOUND:
            return False
        response.raise_for_status()
        data = await response.json(content_type=None)
    return isinstance(data, dict) and data.get("status") == STATUS_ACCEPTED
