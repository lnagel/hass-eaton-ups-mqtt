"""Scenario tests for Eaton 5PX G2 UPS using real fixture data."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock

import pytest
from homeassistant.components.sensor import SensorEntityDescription

from custom_components.eaton_ups_mqtt.sensor import EatonUpsSensor


@pytest.fixture
def mock_coordinator(ups_5px_g2_data):
    """Create a mock coordinator with 5PX G2 fixture data."""
    coordinator = MagicMock()
    coordinator.config_entry.entry_id = "test_5px_g2"
    coordinator.data = ups_5px_g2_data
    return coordinator


class TestUpsIdentification:
    """Tests for UPS identification sensors."""

    @pytest.mark.parametrize(
        ("key", "expected"),
        [
            ("powerDistributions/1/identification$model", "Eaton 5PX 1500i RT2U G2"),
            ("powerDistributions/1/identification$vendor", "EATON"),
            ("powerDistributions/1/identification$serialNumber", "GFHJ7XVG0FN9"),
            ("powerDistributions/1/identification$firmwareVersion", "01.12.0024"),
            ("powerDistributions/1/identification$partNumber", "5PX1500IRT2UG2"),
        ],
    )
    def test_identification_values(self, mock_coordinator, key, expected):
        """Test UPS identification sensor values."""
        desc = SensorEntityDescription(key=key, name="Test")
        sensor = EatonUpsSensor(mock_coordinator, desc)
        assert sensor.native_value == expected


class TestUpsStatus:
    """Tests for UPS status sensors."""

    @pytest.mark.parametrize(
        ("key", "expected"),
        [
            ("powerDistributions/1/status$operating", "in service"),
            ("powerDistributions/1/status$health", "ok"),
            ("powerDistributions/1/status$mode", "on line interactive normal"),
        ],
    )
    def test_status_values(self, mock_coordinator, key, expected):
        """Test UPS status sensor values."""
        desc = SensorEntityDescription(key=key, name="Test")
        sensor = EatonUpsSensor(mock_coordinator, desc)
        assert sensor.native_value == expected


class TestBattery:
    """Tests for battery sensors."""

    @pytest.mark.parametrize(
        ("key", "expected"),
        [
            ("powerDistributions/1/backupSystem/powerBank/measures$stateOfCharge", 100),
            ("powerDistributions/1/backupSystem/powerBank/measures$voltage", 52.2),
            (
                "powerDistributions/1/backupSystem/powerBank/measures$remainingTime",
                14861,
            ),
            ("powerDistributions/1/backupSystem/powerBank/status$operating", "stopped"),
            ("powerDistributions/1/backupSystem/powerBank/status$health", "ok"),
            (
                "powerDistributions/1/backupSystem/powerBank/status$lastTestResult",
                "success",
            ),
        ],
    )
    def test_battery_measurements(self, mock_coordinator, key, expected):
        """Test battery measurement sensor values."""
        desc = SensorEntityDescription(key=key, name="Test")
        sensor = EatonUpsSensor(mock_coordinator, desc)
        assert sensor.native_value == expected

    @pytest.mark.parametrize(
        ("key", "expected"),
        [
            (
                "powerDistributions/1/backupSystem/powerBank/chargers/1/status$active",
                True,
            ),
            (
                "powerDistributions/1/backupSystem/powerBank/chargers/1/status$mode",
                "abm",
            ),
            (
                "powerDistributions/1/backupSystem/powerBank/chargers/1/status$chargerStatus",
                "on not charging",
            ),
        ],
    )
    def test_charger_values(self, mock_coordinator, key, expected):
        """Test charger sensor values."""
        desc = SensorEntityDescription(key=key, name="Test")
        sensor = EatonUpsSensor(mock_coordinator, desc)
        assert sensor.native_value == expected


class TestInputSensors:
    """Tests for input sensors."""

    @pytest.mark.parametrize(
        ("key", "expected"),
        [
            ("powerDistributions/1/inputs/1/measures$voltage", 231.7),
            ("powerDistributions/1/inputs/1/measures$current", 1.3),
            ("powerDistributions/1/inputs/1/measures$frequency", 50),
            ("powerDistributions/1/inputs/1/status$operating", "in service"),
            ("powerDistributions/1/inputs/1/status$health", "ok"),
        ],
    )
    def test_input_values(self, mock_coordinator, key, expected):
        """Test input sensor values."""
        desc = SensorEntityDescription(key=key, name="Test")
        sensor = EatonUpsSensor(mock_coordinator, desc)
        assert sensor.native_value == expected


class TestOutputSensors:
    """Tests for output sensors."""

    @pytest.mark.parametrize(
        ("key", "expected"),
        [
            ("powerDistributions/1/outputs/1/measures$activePower", 192),
            ("powerDistributions/1/outputs/1/measures$apparentPower", 275),
            ("powerDistributions/1/outputs/1/measures$percentLoad", 18),
            ("powerDistributions/1/outputs/1/measures$efficiency", 99),
            ("powerDistributions/1/outputs/1/measures$voltage", 231.7),
            ("powerDistributions/1/outputs/1/measures$current", 1.2),
            ("powerDistributions/1/outputs/1/measures$frequency", 49.9),
            ("powerDistributions/1/outputs/1/measures$powerFactor", 0.69),
        ],
    )
    def test_output_values(self, mock_coordinator, key, expected):
        """Test output sensor values."""
        desc = SensorEntityDescription(key=key, name="Test")
        sensor = EatonUpsSensor(mock_coordinator, desc)
        assert sensor.native_value == expected


class TestOutlets:
    """Tests for outlet sensors across all 3 outlets."""

    @pytest.mark.parametrize(
        ("outlet_num", "expected_name", "expected_power", "expected_switchable"),
        [
            (1, "PRIMARY", 47, False),
            (2, "GROUP 1", 55, True),
            (3, "GROUP 2", 77, True),
        ],
    )
    def test_outlet_identification(
        self,
        mock_coordinator,
        outlet_num,
        expected_name,
        expected_power,
        expected_switchable,
    ):
        """Test outlet identification and measurements."""
        # Test name
        name_key = (
            f"powerDistributions/1/outlets/{outlet_num}/identification$physicalName"
        )
        desc = SensorEntityDescription(key=name_key, name="Test")
        sensor = EatonUpsSensor(mock_coordinator, desc)
        assert sensor.native_value == expected_name

        # Test power
        power_key = f"powerDistributions/1/outlets/{outlet_num}/measures$activePower"
        desc = SensorEntityDescription(key=power_key, name="Test")
        sensor = EatonUpsSensor(mock_coordinator, desc)
        assert sensor.native_value == expected_power

        # Test switchable
        spec_key = (
            f"powerDistributions/1/outlets/{outlet_num}/specifications$switchable"
        )
        desc = SensorEntityDescription(key=spec_key, name="Test")
        sensor = EatonUpsSensor(mock_coordinator, desc)
        assert sensor.native_value == expected_switchable

    @pytest.mark.parametrize(
        ("outlet_num", "field", "expected"),
        [
            # Outlet 1 (PRIMARY)
            (1, "apparentPower", 62),
            (1, "current", 0.1),
            (1, "voltage", 231.7),
            (1, "powerFactor", 0.75),
            # Outlet 2 (GROUP 1)
            (2, "apparentPower", 96),
            (2, "current", 0.5),
            (2, "powerFactor", 0.84),
            # Outlet 3 (GROUP 2)
            (3, "apparentPower", 131),
            (3, "current", 0.7),
            (3, "powerFactor", 0.58),
        ],
    )
    def test_outlet_measurements(self, mock_coordinator, outlet_num, field, expected):
        """Test outlet measurement values across all outlets."""
        key = f"powerDistributions/1/outlets/{outlet_num}/measures${field}"
        desc = SensorEntityDescription(key=key, name="Test")
        sensor = EatonUpsSensor(mock_coordinator, desc)
        assert sensor.native_value == expected


class TestDateSensors:
    """Tests for date/timestamp sensors."""

    def test_lcm_installation_date(self, mock_coordinator):
        """Test LCM installation date parsing."""
        key = "powerDistributions/1/backupSystem/powerBank/status$lcmInstallationDate"
        desc = SensorEntityDescription(key=key, name="Test")
        sensor = EatonUpsSensor(mock_coordinator, desc)
        result = sensor._convert_date(sensor.native_value)
        assert result == date(2021, 10, 26)

    def test_lcm_replacement_date(self, mock_coordinator):
        """Test LCM replacement date parsing."""
        key = "powerDistributions/1/backupSystem/powerBank/status$lcmReplacementDate"
        desc = SensorEntityDescription(key=key, name="Test")
        sensor = EatonUpsSensor(mock_coordinator, desc)
        result = sensor._convert_date(sensor.native_value)
        assert result == date(2025, 10, 25)

    def test_firmware_installation_timestamp(self, mock_coordinator):
        """Test firmware installation timestamp parsing."""
        key = "managers/1/identification$firmwareInstallationDate"
        desc = SensorEntityDescription(key=key, name="Test")
        sensor = EatonUpsSensor(mock_coordinator, desc)
        result = sensor._convert_timestamp(sensor.native_value)
        assert result is not None
        assert result.date() == date(2024, 2, 7)


class TestEnvironmentSensors:
    """Tests for environment sensors."""

    @pytest.mark.parametrize(
        ("key", "expected"),
        [
            ("powerDistributions/1/environment/status$health", "ok"),
            ("powerDistributions/1/environment/status$buildingAlarm1", False),
            ("powerDistributions/1/environment/status$temperatureTooHigh", False),
        ],
    )
    def test_environment_values(self, mock_coordinator, key, expected):
        """Test environment sensor values."""
        desc = SensorEntityDescription(key=key, name="Test")
        sensor = EatonUpsSensor(mock_coordinator, desc)
        assert sensor.native_value == expected


class TestMissingData:
    """Tests for graceful handling of missing data."""

    @pytest.mark.parametrize(
        "key",
        [
            "powerDistributions/1/missing_topic$value",
            "powerDistributions/1/status$missing_field",
            "nonexistent/path$value",
        ],
    )
    def test_missing_data_returns_none(self, mock_coordinator, key):
        """Test that missing data returns None without error."""
        desc = SensorEntityDescription(key=key, name="Test")
        sensor = EatonUpsSensor(mock_coordinator, desc)
        assert sensor.native_value is None


class TestManagerIdentification:
    """Tests for network card manager identification."""

    @pytest.mark.parametrize(
        ("key", "expected"),
        [
            ("managers/1/identification$firmwareVersion", "3.1.15"),
            ("managers/1/identification$vendor", "Eaton"),
            ("managers/1/identification$product", "Gigabit Network Card"),
            ("managers/1/identification$serialNumber", "GZZPQK51FPK"),
            ("managers/1/identification$macAddress", "2F:C2:31:B7:B0:87"),
            ("managers/1/identification$bootloaderVersion", "3.0.2"),
        ],
    )
    def test_manager_identification(self, mock_coordinator, key, expected):
        """Test network card manager identification values."""
        desc = SensorEntityDescription(key=key, name="Test")
        sensor = EatonUpsSensor(mock_coordinator, desc)
        assert sensor.native_value == expected


class TestSpecifications:
    """Tests for UPS specifications."""

    @pytest.mark.parametrize(
        ("key", "expected"),
        [
            ("powerDistributions/1/specifications$topology", "line interactive"),
            ("powerDistributions/1/specifications$voltageRange", "high voltage"),
            ("powerDistributions/1/specifications$powerCycleDuration", 10),
            ("powerDistributions/1/specifications$supported", True),
            (
                "powerDistributions/1/backupSystem/powerBank/specifications$technology",
                "PbAc",
            ),
            (
                "powerDistributions/1/backupSystem/powerBank/specifications$externalCount",
                1,
            ),
            (
                "powerDistributions/1/backupSystem/powerBank/specifications$remoteControlEnabled",
                True,
            ),
        ],
    )
    def test_specification_values(self, mock_coordinator, key, expected):
        """Test UPS specification values."""
        desc = SensorEntityDescription(key=key, name="Test")
        sensor = EatonUpsSensor(mock_coordinator, desc)
        assert sensor.native_value == expected

    def test_nested_specification_access(self, mock_coordinator):
        """Test accessing nested specification objects returns dict."""
        # Nested specs like activePower.nominal are accessed as nested dicts
        key = "powerDistributions/1/specifications$activePower"
        desc = SensorEntityDescription(key=key, name="Test")
        sensor = EatonUpsSensor(mock_coordinator, desc)
        assert sensor.native_value == {"nominal": 1500}
