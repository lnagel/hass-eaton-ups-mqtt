"""
Profile MQTT topic update timing from Eaton UPS.

This script connects to a real Eaton UPS MQTT broker and profiles
how frequently each topic is updated during the observation period.

Usage:
    python scripts/profile_mqtt_topics.py \
        --host ups.example.local \
        --port 8883 \
        --server-cert /path/to/server.pem \
        --client-cert /path/to/client.pem \
        --client-key /path/to/client.key \
        --duration 30
"""

from __future__ import annotations

import argparse
import ssl
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import paho.mqtt.client as mqtt

MQTT_SUPPORTED_PREFIXES = ("mbdetnrs/1.0/", "mbdetnrs/2.0/")


@dataclass
class TopicStats:
    """Statistics for a single MQTT topic."""

    timestamps: list[float] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.timestamps)

    def interval_stats(self) -> tuple[float, float, float] | None:
        """Return (min, avg, max) interval in seconds, or None if < 2 messages."""
        if len(self.timestamps) < 2:
            return None
        intervals = [
            self.timestamps[i + 1] - self.timestamps[i]
            for i in range(len(self.timestamps) - 1)
        ]
        return min(intervals), sum(intervals) / len(intervals), max(intervals)


class MqttTopicProfiler:
    """Profiles MQTT topic update frequency from Eaton UPS."""

    def __init__(
        self, host: str, port: int, server_cert: str, client_cert: str, client_key: str
    ) -> None:
        """Initialize the profiler."""
        self.host = host
        self.port = port
        self.server_cert = server_cert
        self.client_cert = client_cert
        self.client_key = client_key
        self.connected = False
        self.stats: dict[str, TopicStats] = {}
        self.mqtt_prefix: str | None = None
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
            client.subscribe([("mbdetnrs/#", 0)])
            print("Subscribed to mbdetnrs/#")
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
        topic = msg.topic
        now = time.monotonic()

        # Detect prefix from first message
        if self.mqtt_prefix is None:
            for prefix in MQTT_SUPPORTED_PREFIXES:
                if topic.startswith(prefix):
                    self.mqtt_prefix = prefix
                    print(f"  Detected MQTT prefix: {prefix}")
                    break
            else:
                print(f"  Warning: Unknown MQTT topic prefix: {topic}")
                return

        key = topic.removeprefix(self.mqtt_prefix)

        if key not in self.stats:
            self.stats[key] = TopicStats()
        self.stats[key].timestamps.append(now)

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

    def run(self, duration: int) -> None:
        """Run the profiler for specified duration."""
        self.client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION1,
            client_id=f"mqtt-profiler-{int(time.time())}",
            protocol=mqtt.MQTTv31,
        )

        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

        self.client.tls_set(
            ca_certs=self.server_cert,
            certfile=self.client_cert,
            keyfile=self.client_key,
            cert_reqs=ssl.CERT_REQUIRED,
            tls_version=ssl.PROTOCOL_TLS_CLIENT,
        )
        self.client.tls_insecure_set(False)

        print(f"Connecting to {self.host}:{self.port}...")
        self.client.connect(self.host, self.port, keepalive=60)
        self.client.loop_start()

        timeout = 10
        while not self.connected and timeout > 0:
            time.sleep(1)
            timeout -= 1

        if not self.connected:
            print("Failed to connect!")
            self.client.loop_stop()
            sys.exit(1)

        print(f"\nProfiling topics for {duration} seconds...")
        print("-" * 50)
        time.sleep(duration)
        print("-" * 50)

        self.client.disconnect()
        self.client.loop_stop()

        self._print_report(duration)

    def _print_report(self, duration: int) -> None:
        """Print the profiling report."""
        total_messages = sum(s.count for s in self.stats.values())
        print(f"\nMQTT Topic Profile Report ({duration}s observation)")
        print(f"Total messages: {total_messages}")
        print(f"Unique topics: {len(self.stats)}")
        print()

        # Header
        print(
            f"{'Topic':<55} {'Count':>6} {'Rate (/s)':>10} "
            f"{'Min (s)':>8} {'Avg (s)':>8} {'Max (s)':>8}"
        )
        print("-" * 100)

        # Sort by count descending
        for topic, stats in sorted(
            self.stats.items(), key=lambda x: x[1].count, reverse=True
        ):
            rate = stats.count / duration
            intervals = stats.interval_stats()
            if intervals:
                min_i, avg_i, max_i = intervals
                print(
                    f"{topic:<55} {stats.count:>6} {rate:>10.3f} "
                    f"{min_i:>8.2f} {avg_i:>8.2f} {max_i:>8.2f}"
                )
            else:
                print(
                    f"{topic:<55} {stats.count:>6} {rate:>10.3f} "
                    f"{'n/a':>8} {'n/a':>8} {'n/a':>8}"
                )

        print("-" * 100)


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Profile MQTT topic update timing from Eaton UPS"
    )
    parser.add_argument("--host", required=True, help="MQTT broker hostname")
    parser.add_argument("--port", type=int, default=8883, help="MQTT broker port")
    parser.add_argument(
        "--server-cert", required=True, help="Path to server certificate"
    )
    parser.add_argument(
        "--client-cert", required=True, help="Path to client certificate"
    )
    parser.add_argument("--client-key", required=True, help="Path to client key")
    parser.add_argument(
        "--duration", type=int, default=30, help="Observation duration in seconds"
    )

    args = parser.parse_args()

    for cert_path in [args.server_cert, args.client_cert, args.client_key]:
        if not Path(cert_path).exists():
            print(f"Error: Certificate file not found: {cert_path}")
            sys.exit(1)

    profiler = MqttTopicProfiler(
        host=args.host,
        port=args.port,
        server_cert=args.server_cert,
        client_cert=args.client_cert,
        client_key=args.client_key,
    )

    profiler.run(args.duration)


if __name__ == "__main__":
    main()
