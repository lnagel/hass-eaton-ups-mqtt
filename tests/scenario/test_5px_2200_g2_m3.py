"""Scenario tests for Eaton 5PX 2200 G2 UPS with Network-M3 card."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock

import pytest
from homeassistant.components.sensor import SensorDeviceClass, SensorEntityDescription

from custom_components.eaton_ups_mqtt import binary_sensor as bs
from custom_components.eaton_ups_mqtt import sensor as s
from custom_components.eaton_ups_mqtt.binary_sensor import (
    EatonUpsBinarySensor,
    get_binary_entity_descriptions,
)
from custom_components.eaton_ups_mqtt.const import MQTT_PREFIX_V2
from custom_components.eaton_ups_mqtt.sensor import (
    SENSOR_HUMIDITY_PATTERN,
    SENSOR_TEMP_PATTERN,
    EatonUpsSensor,
    get_entity_descriptions,
)


@pytest.fixture
def mock_coordinator(ups_5px_2200_g2_m3_data):
    """Create a mock coordinator with M3 fixture data."""
    coordinator = MagicMock()
    coordinator.config_entry.entry_id = "test_5px_2200_g2_m3"
    coordinator.config_entry.runtime_data.client.mqtt_prefix = MQTT_PREFIX_V2
    coordinator.data = ups_5px_2200_g2_m3_data
    return coordinator


class TestAllSensorsAvailable:
    """Verify all sensor descriptions return values with M3 data."""

    @pytest.fixture
    def sensor_descriptions(self, mock_coordinator):
        """Get M3 sensor descriptions."""
        return get_entity_descriptions(mock_coordinator)

    def test_all_sensors_have_values(self, mock_coordinator, sensor_descriptions):
        """Test that every sensor returns a non-None value with M3 data."""
        for description in sensor_descriptions:
            sensor = EatonUpsSensor(mock_coordinator, description)
            assert sensor.native_value is not None, (
                f"Sensor {description.key} returned None with M3 data"
            )

    def test_includes_friendly_name(self, sensor_descriptions):
        """Test that M3 descriptions include friendlyName."""
        keys = [d.key for d in sensor_descriptions]
        assert "managers/1/identification$friendlyName" in keys

    def test_excludes_m2_only_fields(self, sensor_descriptions):
        """Test that M3 descriptions exclude M2-only fields."""
        keys = [d.key for d in sensor_descriptions]
        assert "managers/1/identification$name" not in keys
        assert "managers/1/identification$manufacturer" not in keys


class TestAllBinarySensorsAvailable:
    """Verify all binary sensor descriptions return values with M3 data."""

    def test_all_binary_sensors_have_values(self, mock_coordinator):
        """Test that every binary sensor returns a non-None value with M3 data."""
        descriptions = get_binary_entity_descriptions(mock_coordinator)
        for description in descriptions:
            sensor = EatonUpsBinarySensor(mock_coordinator, description)
            assert sensor.is_on is not None, (
                f"Binary sensor {description.key} returned None with M3 data"
            )


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


class TestEnvironmentalSensorProbes:
    """Tests for environmental sensor probe support."""

    def test_temperature_sensor_detected(self, mock_coordinator):
        """Test that temperature sensor description is generated."""
        descriptions = get_entity_descriptions(mock_coordinator)
        temp_keys = [
            d.key
            for d in descriptions
            if SENSOR_TEMP_PATTERN.match(d.key.split("$")[0])
        ]
        assert len(temp_keys) == 1

    def test_humidity_sensor_detected(self, mock_coordinator):
        """Test that humidity sensor description is generated."""
        descriptions = get_entity_descriptions(mock_coordinator)
        humidity_keys = [
            d.key
            for d in descriptions
            if SENSOR_HUMIDITY_PATTERN.match(d.key.split("$")[0])
        ]
        assert len(humidity_keys) == 1

    def test_digital_input_sensors_detected(self, mock_coordinator):
        """Test that digital input binary sensors are generated."""
        descriptions = get_binary_entity_descriptions(mock_coordinator)
        di_keys = [d.key for d in descriptions if "channels/digitalInputs/" in d.key]
        assert len(di_keys) == 2

    def test_communication_status_detected(self, mock_coordinator):
        """Test that communication status binary sensor is generated."""
        descriptions = get_binary_entity_descriptions(mock_coordinator)
        comm_keys = [d.key for d in descriptions if "communicationStatus" in d.key]
        assert len(comm_keys) == 1

    def test_temperature_value(self, mock_coordinator):
        """Test temperature sensor reads Kelvin value correctly."""
        descriptions = get_entity_descriptions(mock_coordinator)
        temp_desc = next(
            d for d in descriptions if SENSOR_TEMP_PATTERN.match(d.key.split("$")[0])
        )
        sensor = EatonUpsSensor(mock_coordinator, temp_desc)
        assert sensor.native_value == pytest.approx(301.049988)

    def test_humidity_value(self, mock_coordinator):
        """Test humidity sensor reads value correctly."""
        descriptions = get_entity_descriptions(mock_coordinator)
        humidity_desc = next(
            d
            for d in descriptions
            if SENSOR_HUMIDITY_PATTERN.match(d.key.split("$")[0])
        )
        sensor = EatonUpsSensor(mock_coordinator, humidity_desc)
        assert sensor.native_value == pytest.approx(14.3000002)

    def test_digital_input_values(self, mock_coordinator):
        """Test digital input binary sensors read correctly."""
        descriptions = get_binary_entity_descriptions(mock_coordinator)
        di_descs = [d for d in descriptions if "channels/digitalInputs/" in d.key]
        for desc in di_descs:
            sensor = EatonUpsBinarySensor(mock_coordinator, desc)
            assert sensor.is_on is False

    def test_communication_status_value(self, mock_coordinator):
        """Test communication status reads 'ok' as True."""
        descriptions = get_binary_entity_descriptions(mock_coordinator)
        comm_desc = next(d for d in descriptions if "communicationStatus" in d.key)
        sensor = EatonUpsBinarySensor(mock_coordinator, comm_desc)
        assert sensor.is_on is True

    def test_temperature_sensor_name(self, mock_coordinator):
        """Test temperature sensor uses channel identification name."""
        descriptions = get_entity_descriptions(mock_coordinator)
        temp_desc = next(
            d for d in descriptions if SENSOR_TEMP_PATTERN.match(d.key.split("$")[0])
        )
        assert temp_desc.name == "SI-NW-UV-1@1-T1 Temperature"

    def test_humidity_sensor_name(self, mock_coordinator):
        """Test humidity sensor uses channel identification name."""
        descriptions = get_entity_descriptions(mock_coordinator)
        humidity_desc = next(
            d
            for d in descriptions
            if SENSOR_HUMIDITY_PATTERN.match(d.key.split("$")[0])
        )
        assert humidity_desc.name == "SI-NW-UV-1@1-H1 Humidity"

    def test_digital_input_sensor_names(self, mock_coordinator):
        """Test digital input sensors use channel identification names."""
        descriptions = get_binary_entity_descriptions(mock_coordinator)
        di_descs = [d for d in descriptions if "channels/digitalInputs/" in d.key]
        names = sorted(d.name for d in di_descs)
        assert names == ["SI-NW-UV-1@1-C1 Contact", "SI-NW-UV-1@1-C2 Contact"]

    def test_communication_status_name(self, mock_coordinator):
        """Test communication status uses device identification name."""
        descriptions = get_binary_entity_descriptions(mock_coordinator)
        comm_desc = next(d for d in descriptions if "communicationStatus" in d.key)
        assert comm_desc.name == "SI-NW-UV-1 Communication"


class TestSensorNameFallbacks:
    """Tests for name lookup fallbacks when identification data is missing."""

    def test_sensor_channel_name_fallback_non_dict(self):
        """Test sensor _get_sensor_channel_name returns channel_id for non-dict."""
        data = {
            "sensors/devices/dev1/channels/temperatures/ch1/identification": None,
        }
        result = s._get_sensor_channel_name(data, "temperatures", "dev1", "ch1")
        assert result == "ch1"

    def test_sensor_channel_name_fallback_missing(self):
        """Test sensor _get_sensor_channel_name returns channel_id when missing."""
        result = s._get_sensor_channel_name({}, "temperatures", "dev1", "ch1")
        assert result == "ch1"

    def test_binary_sensor_channel_name_fallback_non_dict(self):
        """Test binary_sensor _get_sensor_channel_name returns channel_id for non-dict."""
        data = {
            "sensors/devices/dev1/channels/digitalInputs/ch1/identification": None,
        }
        result = bs._get_sensor_channel_name(data, "digitalInputs", "dev1", "ch1")
        assert result == "ch1"

    def test_binary_sensor_device_name_fallback_non_dict(self):
        """Test _get_sensor_device_name returns device_id for non-dict data."""
        data = {"sensors/devices/dev1/identification": None}
        assert bs._get_sensor_device_name(data, "dev1") == "dev1"

    def test_binary_sensor_device_name_fallback_missing(self):
        """Test _get_sensor_device_name returns device_id when key is missing."""
        assert bs._get_sensor_device_name({}, "dev1") == "dev1"
