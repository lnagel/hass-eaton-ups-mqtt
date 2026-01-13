"""Unit tests for binary sensor functionality."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from homeassistant.components.binary_sensor import BinarySensorEntityDescription

from custom_components.eaton_ups_mqtt.binary_sensor import (
    EatonUpsBinarySensor,
    get_binary_entity_descriptions,
)


@pytest.fixture
def mock_coordinator():
    """Create a minimal coordinator for testing."""
    coordinator = MagicMock()
    coordinator.config_entry.entry_id = "test"
    coordinator.data = {}
    return coordinator


class TestBinarySensorIsOn:
    """Tests for EatonUpsBinarySensor.is_on property."""

    @pytest.mark.parametrize(
        ("data", "key", "expected"),
        [
            # Boolean values
            ({"topic": {"field": True}}, "topic$field", True),
            ({"topic": {"field": False}}, "topic$field", False),
            # String values
            ({"topic": {"field": "true"}}, "topic$field", True),
            ({"topic": {"field": "True"}}, "topic$field", True),
            ({"topic": {"field": "yes"}}, "topic$field", True),
            ({"topic": {"field": "on"}}, "topic$field", True),
            ({"topic": {"field": "1"}}, "topic$field", True),
            ({"topic": {"field": "false"}}, "topic$field", False),
            ({"topic": {"field": "no"}}, "topic$field", False),
            ({"topic": {"field": "off"}}, "topic$field", False),
            ({"topic": {"field": "0"}}, "topic$field", False),
            ({"topic": {"field": "random"}}, "topic$field", False),
            # Numeric values
            ({"topic": {"field": 1}}, "topic$field", True),
            ({"topic": {"field": 5}}, "topic$field", True),
            ({"topic": {"field": 0.5}}, "topic$field", True),
            ({"topic": {"field": 0}}, "topic$field", False),
            ({"topic": {"field": -1}}, "topic$field", False),
            # Invalid types return False
            ({"topic": {"field": []}}, "topic$field", False),
            ({"topic": {"field": {}}}, "topic$field", False),
        ],
    )
    def test_is_on_conversion(self, mock_coordinator, data, key, expected):
        """Test is_on property converts values correctly."""
        mock_coordinator.data = data
        desc = BinarySensorEntityDescription(key=key, name="Test")
        sensor = EatonUpsBinarySensor(mock_coordinator, desc)
        assert sensor.is_on == expected

    def test_is_on_with_empty_data(self, mock_coordinator):
        """Test is_on returns None when coordinator data is empty."""
        mock_coordinator.data = {}
        desc = BinarySensorEntityDescription(key="topic$field", name="Test")
        sensor = EatonUpsBinarySensor(mock_coordinator, desc)
        assert sensor.is_on is None

    def test_is_on_with_none_data(self, mock_coordinator):
        """Test is_on returns None when coordinator data is None."""
        mock_coordinator.data = None
        desc = BinarySensorEntityDescription(key="topic$field", name="Test")
        sensor = EatonUpsBinarySensor(mock_coordinator, desc)
        assert sensor.is_on is None

    def test_is_on_with_missing_topic(self, mock_coordinator):
        """Test is_on returns None when topic is missing."""
        mock_coordinator.data = {"other_topic": {"field": True}}
        desc = BinarySensorEntityDescription(key="missing$field", name="Test")
        sensor = EatonUpsBinarySensor(mock_coordinator, desc)
        assert sensor.is_on is None

    def test_is_on_with_missing_field(self, mock_coordinator):
        """Test is_on returns None when field is missing."""
        mock_coordinator.data = {"topic": {"other_field": True}}
        desc = BinarySensorEntityDescription(key="topic$missing", name="Test")
        sensor = EatonUpsBinarySensor(mock_coordinator, desc)
        assert sensor.is_on is None


class TestGetBinaryEntityDescriptions:
    """Tests for get_binary_entity_descriptions function."""

    def test_returns_base_descriptions(self, mock_coordinator, ups_5px_g2_data):
        """Test returns base descriptions with fixture data."""
        mock_coordinator.data = ups_5px_g2_data
        descriptions = get_binary_entity_descriptions(mock_coordinator)

        # Should have base descriptions + input descriptions + outlet descriptions
        assert len(descriptions) > 25  # Base has 25, plus dynamic

    def test_detects_inputs(self, mock_coordinator):
        """Test detects and adds input descriptions."""
        mock_coordinator.data = {
            "powerDistributions/1/inputs/1/status": {"inRange": True},
            "powerDistributions/1/inputs/2/measures": {"voltage": 230},
        }
        descriptions = get_binary_entity_descriptions(mock_coordinator)

        # Check that input descriptions were added
        input_keys = [d.key for d in descriptions if "inputs/" in d.key]
        assert any("inputs/1/" in key for key in input_keys)
        assert any("inputs/2/" in key for key in input_keys)

    def test_detects_outlets(self, mock_coordinator):
        """Test detects and adds outlet descriptions."""
        mock_coordinator.data = {
            "powerDistributions/1/outlets/1/status": {"supply": True},
            "powerDistributions/1/outlets/3/status": {"switchedOn": False},
        }
        descriptions = get_binary_entity_descriptions(mock_coordinator)

        # Check that outlet descriptions were added
        outlet_keys = [d.key for d in descriptions if "outlets/" in d.key]
        assert any("outlets/1/" in key for key in outlet_keys)
        assert any("outlets/3/" in key for key in outlet_keys)

    def test_empty_data_returns_base_only(self, mock_coordinator):
        """Test returns only base descriptions when no dynamic data."""
        mock_coordinator.data = {}
        descriptions = get_binary_entity_descriptions(mock_coordinator)

        # Should only have base descriptions (no inputs/outlets detected)
        assert len(descriptions) == 25  # Base entity count
