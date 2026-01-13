"""
Sanitize PII from UPS MQTT fixture data.

This script replaces personally identifiable information (PII) in the
raw UPS data dump with realistic fake data.

Usage:
    python scripts/sanitize_fixture.py \
        --input tests/fixtures/raw_ups_data.json \
        --output tests/fixtures/sample_ups_data.json
"""

from __future__ import annotations

import argparse
import json
import random
import re
import string
import uuid
from datetime import datetime, timedelta
from pathlib import Path

# Seed for reproducible fake data (change this to get different values)
RANDOM_SEED = 42


class PiiSanitizer:
    """Sanitizes PII from UPS fixture data."""

    def __init__(self, seed: int = RANDOM_SEED) -> None:
        """Initialize with a random seed for reproducibility."""
        self.rng = random.Random(seed)
        self.changes: list[tuple[str, str, str]] = []  # (path, old, new)
        # Time offset to apply to dates (random between 30-365 days in the past)
        self.date_offset = timedelta(days=self.rng.randint(30, 365))

    def _random_serial(self, prefix: str = "", length: int = 10) -> str:
        """Generate a random serial number."""
        chars = string.ascii_uppercase + string.digits
        return prefix + "".join(self.rng.choices(chars, k=length))

    def _random_uuid(self) -> str:
        """Generate a deterministic UUID based on seed."""
        # Use random bytes seeded by our RNG
        random_bytes = bytes(self.rng.randint(0, 255) for _ in range(16))
        return str(uuid.UUID(bytes=random_bytes, version=4))

    def _random_mac(self) -> str:
        """Generate a random MAC address."""
        return ":".join(f"{self.rng.randint(0, 255):02X}" for _ in range(6))

    def _random_hex(self, length: int = 7) -> str:
        """Generate a random hex string."""
        return "".join(self.rng.choices("0123456789abcdef", k=length))

    def _random_part_number(self) -> str:
        """Generate a random part number."""
        return f"{self.rng.randint(100, 999)}-{self.rng.choice(string.ascii_uppercase)}{self.rng.randint(1000, 9999)}-{self.rng.randint(1, 99):02d}"

    def _offset_date_iso(self, date_str: str) -> str:
        """Offset an ISO format date string."""
        try:
            # Parse ISO format with or without milliseconds
            if "." in date_str:
                dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            else:
                dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            # Apply offset
            new_dt = dt - self.date_offset
            # Format back to same format
            if "." in date_str:
                return new_dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")
            return new_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        except (ValueError, TypeError):
            return date_str

    def _offset_timestamp(self, ts: int) -> int:
        """Offset a Unix timestamp."""
        return ts - int(self.date_offset.total_seconds())

    def _record_change(self, path: str, old: str, new: str) -> None:
        """Record a change for reporting."""
        self.changes.append((path, str(old), str(new)))

    def sanitize(self, data: dict) -> dict:
        """Sanitize the entire data structure."""
        result = json.loads(json.dumps(data))  # Deep copy

        # Sanitize metadata
        if "host" in result:
            old = result["host"]
            result["host"] = "ups.example.local"
            self._record_change("host", old, result["host"])

        if "captured_at" in result:
            old = result["captured_at"]
            # Use a fixed date for reproducibility
            result["captured_at"] = "2025-01-15T12:00:00+00:00"
            self._record_change("captured_at", old, result["captured_at"])

        # Sanitize the data section
        if "data" in result:
            result["data"] = self._sanitize_data(result["data"])

        return result

    def _sanitize_data(self, data: dict) -> dict:
        """Sanitize the MQTT data dictionary."""
        result = data.copy()

        # Manager identification
        if "managers/1/identification" in result:
            result["managers/1/identification"] = self._sanitize_manager_id(
                result["managers/1/identification"]
            )

        # Power distribution identification
        if "powerDistributions/1/identification" in result:
            result["powerDistributions/1/identification"] = self._sanitize_pd_id(
                result["powerDistributions/1/identification"]
            )

        # Power bank status (dates)
        if "powerDistributions/1/backupSystem/powerBank/status" in result:
            result["powerDistributions/1/backupSystem/powerBank/status"] = (
                self._sanitize_powerbank_status(
                    result["powerDistributions/1/backupSystem/powerBank/status"]
                )
            )

        # Outlet identifications
        for key in list(result.keys()):
            if re.match(r"powerDistributions/1/outlets/\d+/identification", key):
                result[key] = self._sanitize_outlet_id(result[key], key)

        return result

    def _sanitize_manager_id(self, mgr: dict) -> dict:
        """Sanitize manager identification fields."""
        result = mgr.copy()
        path = "managers/1/identification"

        # UUID
        if "uuid" in result:
            old = result["uuid"]
            result["uuid"] = self._random_uuid()
            self._record_change(f"{path}.uuid", old, result["uuid"])

        # Serial number
        if "serialNumber" in result:
            old = result["serialNumber"]
            result["serialNumber"] = self._random_serial("G", 10)
            self._record_change(f"{path}.serialNumber", old, result["serialNumber"])

        # Part number
        if "partNumber" in result:
            old = result["partNumber"]
            result["partNumber"] = self._random_part_number()
            self._record_change(f"{path}.partNumber", old, result["partNumber"])

        # Name - keep as-is, not PII (generic product name)
        # if "name" in result:
        #     old = result["name"]
        #     result["name"] = "TestUPS"
        #     self._record_change(f"{path}.name", old, result["name"])

        # MAC address
        if "macAddress" in result:
            old = result["macAddress"]
            result["macAddress"] = self._random_mac()
            self._record_change(f"{path}.macAddress", old, result["macAddress"])

        # Firmware SHA
        if "firmwareSha" in result:
            old = result["firmwareSha"]
            result["firmwareSha"] = self._random_hex(7)
            self._record_change(f"{path}.firmwareSha", old, result["firmwareSha"])

        # Timestamps
        for field in [
            "firmwareInstallationDate",
            "firmwareActivationDate",
            "firmwareDate",
        ]:
            if field in result and isinstance(result[field], int):
                old = result[field]
                result[field] = self._offset_timestamp(old)
                self._record_change(f"{path}.{field}", str(old), str(result[field]))

        return result

    def _sanitize_pd_id(self, pd: dict) -> dict:
        """Sanitize power distribution identification fields."""
        result = pd.copy()
        path = "powerDistributions/1/identification"

        # UUID
        if "uuid" in result:
            old = result["uuid"]
            result["uuid"] = self._random_uuid()
            self._record_change(f"{path}.uuid", old, result["uuid"])

        # Serial number
        if "serialNumber" in result:
            old = result["serialNumber"]
            result["serialNumber"] = self._random_serial("GF", 10)
            self._record_change(f"{path}.serialNumber", old, result["serialNumber"])

        return result

    def _sanitize_powerbank_status(self, status: dict) -> dict:
        """Sanitize power bank status dates."""
        result = status.copy()
        path = "powerDistributions/1/backupSystem/powerBank/status"

        date_fields = [
            "lastTestResultDate",
            "lastSuccessfulTestDate",
            "lcmInstallationDate",
            "lcmReplacementDate",
        ]

        for field in date_fields:
            if field in result and isinstance(result[field], str):
                old = result[field]
                result[field] = self._offset_date_iso(old)
                self._record_change(f"{path}.{field}", old, result[field])

        return result

    def _sanitize_outlet_id(self, outlet: dict, topic_path: str) -> dict:
        """Sanitize outlet identification fields."""
        result = outlet.copy()

        if "uuid" in result:
            old = result["uuid"]
            result["uuid"] = self._random_uuid()
            self._record_change(f"{topic_path}.uuid", old, result["uuid"])

        return result

    def print_report(self) -> None:
        """Print a summary of all changes made."""
        print("\n" + "=" * 60)
        print("PII SANITIZATION REPORT")
        print("=" * 60)
        print(f"\nTotal fields sanitized: {len(self.changes)}")
        print("-" * 60)

        for path, old, new in self.changes:
            # Truncate long values
            old_display = old[:40] + "..." if len(old) > 40 else old
            new_display = new[:40] + "..." if len(new) > 40 else new
            print(f"\n{path}:")
            print(f"  OLD: {old_display}")
            print(f"  NEW: {new_display}")

        print("\n" + "=" * 60)


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Sanitize PII from UPS fixture data")
    parser.add_argument("--input", required=True, help="Input JSON file path")
    parser.add_argument("--output", required=True, help="Output JSON file path")
    parser.add_argument(
        "--seed",
        type=int,
        default=RANDOM_SEED,
        help="Random seed for reproducible fake data",
    )

    args = parser.parse_args()

    # Load input
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file not found: {args.input}")
        return

    with input_path.open() as f:
        data = json.load(f)

    # Sanitize
    sanitizer = PiiSanitizer(seed=args.seed)
    sanitized = sanitizer.sanitize(data)

    # Write output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w") as f:
        json.dump(sanitized, f, indent=2)

    # Print report
    sanitizer.print_report()

    print(f"\nSanitized data written to: {args.output}")
    print("\nPlease review the changes above before committing!")


if __name__ == "__main__":
    main()
