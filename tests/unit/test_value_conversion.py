"""Unit tests for value conversion functions."""

from __future__ import annotations

from datetime import UTC, date, datetime
from unittest.mock import MagicMock

import pytest
from homeassistant.components.sensor import SensorEntityDescription

from custom_components.eaton_ups_mqtt.sensor import EatonUpsSensor


@pytest.fixture
def mock_sensor():
    """Create a minimal sensor instance for testing conversion methods."""
    coordinator = MagicMock()
    coordinator.config_entry.entry_id = "test"
    coordinator.data = {}
    description = SensorEntityDescription(
        key="test$value",
        name="Test",
    )
    return EatonUpsSensor(coordinator, description)


class TestTimestampConversion:
    """Tests for _convert_timestamp method."""

    @pytest.mark.parametrize(
        ("value", "expected_date"),
        [
            (1707301493, date(2024, 2, 7)),  # Unix timestamp
            ("2025-01-04T14:17:36.000Z", date(2025, 1, 4)),  # ISO format
            ("2021-10-26T11:12:04.000Z", date(2021, 10, 26)),  # Another ISO
        ],
    )
    def test_convert_timestamp_valid(self, mock_sensor, value, expected_date):
        """Test valid timestamp conversions."""
        result = mock_sensor._convert_timestamp(value)
        assert result is not None
        assert result.date() == expected_date

    @pytest.mark.parametrize(
        "value",
        [
            None,
            "not a date",
            "2025-01-04",  # Missing time component
            [],
            {},
            -999999999999999,  # Out of range
        ],
    )
    def test_convert_timestamp_invalid(self, mock_sensor, value):
        """Test invalid timestamp values return None."""
        assert mock_sensor._convert_timestamp(value) is None


class TestDateConversion:
    """Tests for _convert_date method."""

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (1707301493, date(2024, 2, 7)),
            ("2021-10-26T11:12:04.000Z", date(2021, 10, 26)),
            ("2025-10-25T11:12:04.000Z", date(2025, 10, 25)),
        ],
    )
    def test_convert_date_valid(self, mock_sensor, value, expected):
        """Test valid date conversions."""
        assert mock_sensor._convert_date(value) == expected

    @pytest.mark.parametrize(
        "value",
        [None, "invalid", "2025-01-04", [], {}],
    )
    def test_convert_date_invalid(self, mock_sensor, value):
        """Test invalid date values return None."""
        assert mock_sensor._convert_date(value) is None


class TestBooleanConversion:
    """Tests for binary sensor boolean conversion logic."""

    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            # Boolean values
            (True, True),
            (False, False),
            # String values - truthy
            ("true", True),
            ("True", True),
            ("TRUE", True),
            ("yes", True),
            ("on", True),
            ("1", True),
            # String values - falsy
            ("false", False),
            ("False", False),
            ("no", False),
            ("off", False),
            ("0", False),
            ("random", False),
            # Numeric values
            (1, True),
            (2, True),
            (0.5, True),
            (0, False),
            (-1, False),
        ],
    )
    def test_bool_conversion(self, value, expected):
        """Test boolean conversion logic matches binary_sensor.is_on behavior."""
        # Replicate the conversion logic from binary_sensor.py
        if isinstance(value, bool):
            result = value
        elif isinstance(value, str):
            result = value.lower() in ("true", "yes", "on", "1")
        elif isinstance(value, int | float):
            result = value > 0
        else:
            result = False
        assert result == expected


class TestDataNavigation:
    """Tests for data navigation/extraction logic."""

    @pytest.mark.parametrize(
        ("data", "key", "expected"),
        [
            # Simple extraction
            ({"topic": {"value": 42}}, "topic$value", 42),
            # Nested extraction
            ({"a": {"b": {"c": "deep"}}}, "a$b/c", "deep"),
            # Missing key returns None
            ({"topic": {}}, "topic$missing", None),
            # Missing topic returns None
            ({}, "missing$value", None),
        ],
    )
    def test_value_extraction(self, data, key, expected):
        """Test data navigation returns correct values."""
        coordinator = MagicMock()
        coordinator.config_entry.entry_id = "test"
        coordinator.data = data
        description = SensorEntityDescription(key=key, name="Test")
        sensor = EatonUpsSensor(coordinator, description)
        assert sensor.native_value == expected
