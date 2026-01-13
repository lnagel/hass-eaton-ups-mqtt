#!/usr/bin/env python3
"""Dump MQTT data from Eaton UPS for test fixtures.

This script connects to a real Eaton UPS MQTT broker and captures
all messages to create test fixtures.

Usage:
    python scripts/dump_mqtt_data.py \
        --host ups.example.local \
        --port 8883 \
        --server-cert /path/to/server.pem \
        --client-cert /path/to/client.pem \
        --client-key /path/to/client.key \
        --output tests/fixtures/raw_ups_data.json \
        --duration 30
"""

from __future__ import annotations

import argparse
import json
import ssl
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import paho.mqtt.client as mqtt

MQTT_PREFIX = "mbdetnrs/1.0/"


class MqttDataDumper:
    """Captures MQTT messages from Eaton UPS."""

    def __init__(self, host: str, port: int, server_cert: str, client_cert: str, client_key: str) -> None:
        """Initialize the dumper."""
        self.host = host
        self.port = port
        self.server_cert = server_cert
        self.client_cert = client_cert
        self.client_key = client_key
        self.connected = False
        self.data: dict[str, dict] = {}
        self.message_count = 0
        self.client: mqtt.Client | None = None

    def _on_connect(
        self,
        client: mqtt.Client,
        userdata: object,
        flags: dict[str, int],
        rc: int,
        properties: mqtt.Properties | None = None,
    ) -> None:
        """Handle connection callback."""
        if rc == 0:
            print(f"Connected to {self.host}:{self.port}")
            self.connected = True
            # Subscribe to all relevant topics
            client.subscribe(
                [
                    (MQTT_PREFIX + "managers/#", 0),
                    (MQTT_PREFIX + "powerDistributions/#", 0),
                ]
            )
            print("Subscribed to managers/# and powerDistributions/#")
        else:
            print(f"Connection failed with code {rc}")
            self.connected = False

    def _on_message(
        self,
        client: mqtt.Client,
        userdata: object,
        msg: mqtt.MQTTMessage,
    ) -> None:
        """Handle incoming messages."""
        try:
            topic = msg.topic
            payload = msg.payload.decode("utf-8")
            data = json.loads(payload)

            # Store without prefix
            key = topic.removeprefix(MQTT_PREFIX)
            self.data[key] = data
            self.message_count += 1
            print(f"  [{self.message_count}] {key}")

        except json.JSONDecodeError as e:
            print(f"  Warning: JSON decode error for {msg.topic}: {e}")
        except Exception as e:
            print(f"  Error processing message: {e}")

    def _on_disconnect(
        self,
        client: mqtt.Client,
        userdata: object,
        rc: int,
        properties: mqtt.Properties | None = None,
    ) -> None:
        """Handle disconnection."""
        print(f"Disconnected (rc={rc})")
        self.connected = False

    def run(self, duration: int) -> dict:
        """Run the data capture for specified duration."""
        # Create MQTT client
        self.client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION1,
            client_id=f"mqtt-dumper-{int(time.time())}",
            protocol=mqtt.MQTTv31,
        )

        # Set up callbacks
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

        # Set up TLS
        self.client.tls_set(
            ca_certs=self.server_cert,
            certfile=self.client_cert,
            keyfile=self.client_key,
            cert_reqs=ssl.CERT_REQUIRED,
            tls_version=ssl.PROTOCOL_TLS_CLIENT,
        )
        self.client.tls_insecure_set(False)

        # Connect
        print(f"Connecting to {self.host}:{self.port}...")
        self.client.connect(self.host, self.port, keepalive=60)
        self.client.loop_start()

        # Wait for connection
        timeout = 10
        while not self.connected and timeout > 0:
            time.sleep(1)
            timeout -= 1

        if not self.connected:
            print("Failed to connect!")
            self.client.loop_stop()
            sys.exit(1)

        # Capture messages for duration
        print(f"\nCapturing messages for {duration} seconds...")
        print("-" * 50)
        time.sleep(duration)
        print("-" * 50)

        # Disconnect
        self.client.disconnect()
        self.client.loop_stop()

        return {
            "captured_at": datetime.now(UTC).isoformat(),
            "host": self.host,
            "port": self.port,
            "duration_seconds": duration,
            "message_count": self.message_count,
            "data": self.data,
        }


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Dump MQTT data from Eaton UPS")
    parser.add_argument("--host", required=True, help="MQTT broker hostname")
    parser.add_argument("--port", type=int, default=8883, help="MQTT broker port")
    parser.add_argument("--server-cert", required=True, help="Path to server certificate")
    parser.add_argument("--client-cert", required=True, help="Path to client certificate")
    parser.add_argument("--client-key", required=True, help="Path to client key")
    parser.add_argument("--output", required=True, help="Output JSON file path")
    parser.add_argument("--duration", type=int, default=30, help="Capture duration in seconds")

    args = parser.parse_args()

    # Validate certificate files exist
    for cert_path in [args.server_cert, args.client_cert, args.client_key]:
        if not Path(cert_path).exists():
            print(f"Error: Certificate file not found: {cert_path}")
            sys.exit(1)

    # Create dumper and run
    dumper = MqttDataDumper(
        host=args.host,
        port=args.port,
        server_cert=args.server_cert,
        client_cert=args.client_cert,
        client_key=args.client_key,
    )

    result = dumper.run(args.duration)

    # Write output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w") as f:
        json.dump(result, f, indent=2)

    print(f"\nCaptured {result['message_count']} messages")
    print(f"Topics captured: {len(result['data'])}")
    print(f"Output written to: {args.output}")


if __name__ == "__main__":
    main()
