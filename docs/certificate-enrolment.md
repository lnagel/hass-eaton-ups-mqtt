# Client certificate enrolment

The card only accepts MQTT connections from client certificates it trusts. Besides
importing a certificate in the web interface, a client can enrol its own certificate
over HTTPS (port 443).

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/etn/v1/comm/certificates/mqtt/clients/<subject_hash>.0` | State of a client certificate |
| POST | `/etn/v1/comm/certificates/mqtt/clients` | Upload a client certificate |

`<subject_hash>` is the OpenSSL subject name hash of the certificate, as printed by
`openssl x509 -noout -subject_hash`.

The status request returns `404` for an unknown certificate, and for a trusted one:

```json
{
  "path": "/etn/v1/comm/certificates/mqtt/clients/<subject_hash>.0",
  "id": "<subject_hash>.0",
  "status": "accepted"
}
```

The upload takes the certificate in PEM format:

```json
{
  "format": "PEM",
  "certificate": "-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----\n"
}
```

It needs no authentication, but the card only accepts it (`200`) while pairing with
clients is started in the web interface; otherwise it answers `401`.

The integration checks the status of its client certificate and uploads it when
needed: after generating a certificate, when the MQTT connection cannot be set up,
and in the reauthentication and reconfiguration flows. If the upload is refused or
the API is not reachable, a repair issue explains how to start pairing or import the
certificate manually.
