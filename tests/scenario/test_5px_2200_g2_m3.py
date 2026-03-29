"""Scenario tests for Eaton 5PX 2200 G2 UPS with Network-M3 card."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock

import pytest
from homeassistant.components.sensor import SensorDeviceClass, SensorEntityDescription

from custom_components.eaton_ups_mqtt.binary_sensor import (
    BASE_ENTITY_DESCRIPTIONS as BINARY_BASE_DESCRIPTIONS,
)
from custom_components.eaton_ups_mqtt.binary_sensor import (
    EatonUpsBinarySensor,
    _generate_input_binary_descriptions,
    _generate_outlet_binary_descriptions,
)
from custom_components.eaton_ups_mqtt.sensor import (
    BASE_ENTITY_DESCRIPTIONS as SENSOR_BASE_DESCRIPTIONS,
)
from custom_components.eaton_ups_mqtt.sensor import (
    EatonUpsSensor,
    _generate_input_descriptions,
    _generate_outlet_descriptions,
    _generate_output_descriptions,
)


@pytest.fixture
def mock_coordinator(ups_5px_2200_g2_m3_data):
    """Create a mock coordinator with M3 fixture data."""
    coordinator = MagicMock()
    coordinator.config_entry.entry_id = "test_5px_2200_g2_m3"
    coordinator.data = ups_5px_2200_g2_m3_data
    return coordinator


# --- M3 field differences ---
# These sensor keys reference fields that exist on M2 but not on M3.
# They are expected to return None until field aliasing is implemented.
M3_MISSING_FIELDS = {
    "managers/1/identification$name",  # M3 uses friendlyName
    "managers/1/identification$manufacturer",  # M3 uses vendor
}


class TestAllBaseSensorsAvailable:
    """Verify all base sensor descriptions return values with M3 data."""

    @pytest.mark.parametrize(
        "description",
        [d for d in SENSOR_BASE_DESCRIPTIONS if d.key not in M3_MISSING_FIELDS],
        ids=[d.key for d in SENSOR_BASE_DESCRIPTIONS if d.key not in M3_MISSING_FIELDS],
    )
    def test_sensor_has_value(self, mock_coordinator, description):
        """Test that sensor returns a non-None value with M3 data."""
        sensor = EatonUpsSensor(mock_coordinator, description)
        assert sensor.native_value is not None, (
            f"Sensor {description.key} returned None with M3 data"
        )

    @pytest.mark.parametrize(
        "description",
        [d for d in SENSOR_BASE_DESCRIPTIONS if d.key in M3_MISSING_FIELDS],
        ids=[d.key for d in SENSOR_BASE_DESCRIPTIONS if d.key in M3_MISSING_FIELDS],
    )
    def test_known_missing_fields_return_none(self, mock_coordinator, description):
        """Test that known M3-missing fields return None (expected)."""
        sensor = EatonUpsSensor(mock_coordinator, description)
        assert sensor.native_value is None


class TestAllBaseBinarySensorsAvailable:
    """Verify all base binary sensor descriptions return values with M3 data."""

    @pytest.mark.parametrize(
        "description",
        BINARY_BASE_DESCRIPTIONS,
        ids=[d.key for d in BINARY_BASE_DESCRIPTIONS],
    )
    def test_binary_sensor_has_value(self, mock_coordinator, description):
        """Test that binary sensor returns a non-None value with M3 data."""
        sensor = EatonUpsBinarySensor(mock_coordinator, description)
        assert sensor.is_on is not None, (
            f"Binary sensor {description.key} returned None with M3 data"
        )


class TestDynamicSensorsAvailable:
    """Verify dynamically generated sensor descriptions work with M3 data."""

    @pytest.mark.parametrize(
        "description",
        _generate_input_descriptions(1),
        ids=[d.key for d in _generate_input_descriptions(1)],
    )
    def test_input_sensors(self, mock_coordinator, description):
        """Test input sensor values are available."""
        sensor = EatonUpsSensor(mock_coordinator, description)
        assert sensor.native_value is not None

    @pytest.mark.parametrize(
        "description",
        _generate_output_descriptions(1),
        ids=[d.key for d in _generate_output_descriptions(1)],
    )
    def test_output_sensors(self, mock_coordinator, description):
        """Test output sensor values are available."""
        sensor = EatonUpsSensor(mock_coordinator, description)
        assert sensor.native_value is not None

    @pytest.mark.parametrize(
        "description",
        _generate_outlet_descriptions(1),
        ids=[d.key for d in _generate_outlet_descriptions(1)],
    )
    def test_outlet_sensors(self, mock_coordinator, description):
        """Test outlet sensor values are available."""
        sensor = EatonUpsSensor(mock_coordinator, description)
        assert sensor.native_value is not None

    @pytest.mark.parametrize(
        "description",
        _generate_input_binary_descriptions(1),
        ids=[d.key for d in _generate_input_binary_descriptions(1)],
    )
    def test_input_binary_sensors(self, mock_coordinator, description):
        """Test input binary sensor values are available."""
        sensor = EatonUpsBinarySensor(mock_coordinator, description)
        assert sensor.is_on is not None

    @pytest.mark.parametrize(
        "description",
        _generate_outlet_binary_descriptions(1),
        ids=[d.key for d in _generate_outlet_binary_descriptions(1)],
    )
    def test_outlet_binary_sensors(self, mock_coordinator, description):
        """Test outlet binary sensor values are available."""
        sensor = EatonUpsBinarySensor(mock_coordinator, description)
        assert sensor.is_on is not None


class TestM3SpecificValues:
    """Tests for M3-specific data values."""

    @pytest.mark.parametrize(
        ("key", "expected"),
        [
            ("managers/1/identification$firmwareVersion", "2.2.0"),
            ("managers/1/identification$vendor", "Eaton"),
            ("managers/1/identification$macAddress", "00:20:85:AA:BB:CC"),
            ("managers/1/identification$bootloaderVersion", "4.0.4"),
            ("powerDistributions/1/identification$model", "Eaton 5PX 2200i RT3U G2"),
            ("powerDistributions/1/identification$vendor", "EATON"),
            ("powerDistributions/1/identification$firmwareVersion", "01.12.0024"),
        ],
    )
    def test_identification_values(self, mock_coordinator, key, expected):
        """Test identification sensor values for M3 card."""
        desc = SensorEntityDescription(key=key, name="Test")
        sensor = EatonUpsSensor(mock_coordinator, desc)
        assert sensor.native_value == expected

    def test_m3_firmware_date_without_milliseconds(self, mock_coordinator):
        """Test M3 firmware date parsing (no milliseconds in timestamp)."""
        desc = SensorEntityDescription(
            key="managers/1/identification$firmwareDate",
            name="Test",
            device_class=SensorDeviceClass.TIMESTAMP,
        )
        sensor = EatonUpsSensor(mock_coordinator, desc)
        result = sensor.native_value
        assert result is not None
        assert result.date() == date(2025, 4, 14)

    def test_m3_firmware_installation_date(self, mock_coordinator):
        """Test M3 firmware installation date parsing."""
        desc = SensorEntityDescription(
            key="managers/1/identification$firmwareInstallationDate",
            name="Test",
            device_class=SensorDeviceClass.TIMESTAMP,
        )
        sensor = EatonUpsSensor(mock_coordinator, desc)
        result = sensor.native_value
        assert result is not None
        assert result.date() == date(2025, 11, 25)

    def test_battery_test_status_is_string_on_m3(self, mock_coordinator):
        """Test that M3 returns testStatus as string instead of int."""
        desc = SensorEntityDescription(
            key="powerDistributions/1/backupSystem/powerBank/status$testStatus",
            name="Test",
        )
        sensor = EatonUpsSensor(mock_coordinator, desc)
        # M2 returns int (3), M3 returns string ("done")
        assert sensor.native_value == "done"
