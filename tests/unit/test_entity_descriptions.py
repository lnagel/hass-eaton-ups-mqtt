"""Unit tests for entity description generators."""

from __future__ import annotations

import pytest

from custom_components.eaton_ups_mqtt.binary_sensor import (
    _generate_input_binary_descriptions,
    _generate_outlet_binary_descriptions,
)
from custom_components.eaton_ups_mqtt.sensor import (
    _generate_input_descriptions,
    _generate_outlet_descriptions,
    _generate_output_descriptions,
)


class TestSensorDescriptionGenerators:
    """Tests for sensor description generator functions."""

    @pytest.mark.parametrize(
        ("generator", "input_num", "min_count"),
        [
            (_generate_input_descriptions, 1, 3),  # voltage, current, frequency
            (_generate_input_descriptions, 2, 3),
            (_generate_output_descriptions, 1, 8),  # Multiple output sensors
            (_generate_output_descriptions, 3, 8),
            (_generate_outlet_descriptions, 1, 8),  # Multiple outlet sensors
            (_generate_outlet_descriptions, 2, 8),
        ],
    )
    def test_generator_returns_descriptions(self, generator, input_num, min_count):
        """Test generators return expected number of descriptions."""
        descriptions = generator(input_num)
        assert len(descriptions) >= min_count

    @pytest.mark.parametrize("input_num", [1, 2, 3])
    def test_input_descriptions_have_correct_keys(self, input_num):
        """Test input descriptions contain input number in keys."""
        descriptions = _generate_input_descriptions(input_num)
        for desc in descriptions:
            assert f"inputs/{input_num}/" in desc.key

    @pytest.mark.parametrize("output_num", [1, 2])
    def test_output_descriptions_have_correct_keys(self, output_num):
        """Test output descriptions contain output number in keys."""
        descriptions = _generate_output_descriptions(output_num)
        for desc in descriptions:
            assert f"outputs/{output_num}/" in desc.key

    @pytest.mark.parametrize("outlet_num", [1, 2, 3])
    def test_outlet_descriptions_have_correct_keys(self, outlet_num):
        """Test outlet descriptions contain outlet number in keys."""
        descriptions = _generate_outlet_descriptions(outlet_num)
        for desc in descriptions:
            assert f"outlets/{outlet_num}/" in desc.key


class TestBinarySensorDescriptionGenerators:
    """Tests for binary sensor description generator functions."""

    @pytest.mark.parametrize(
        ("generator", "input_num", "min_count"),
        [
            (_generate_input_binary_descriptions, 1, 8),
            (_generate_input_binary_descriptions, 2, 8),
            (_generate_outlet_binary_descriptions, 1, 2),  # supply, switchedOn
            (_generate_outlet_binary_descriptions, 3, 2),
        ],
    )
    def test_binary_generator_returns_descriptions(
        self, generator, input_num, min_count
    ):
        """Test binary generators return expected number of descriptions."""
        descriptions = generator(input_num)
        assert len(descriptions) >= min_count


class TestDescriptionUniqueness:
    """Tests that all description keys are unique."""

    def test_all_sensor_keys_unique(self):
        """Test all generated sensor keys are unique within their type."""
        all_keys = []
        for i in range(1, 4):
            all_keys.extend(d.key for d in _generate_input_descriptions(i))
            all_keys.extend(d.key for d in _generate_output_descriptions(i))
            all_keys.extend(d.key for d in _generate_outlet_descriptions(i))
        assert len(all_keys) == len(set(all_keys))

    def test_all_binary_sensor_keys_unique(self):
        """Test all generated binary sensor keys are unique within their type."""
        all_keys = []
        for i in range(1, 4):
            all_keys.extend(d.key for d in _generate_input_binary_descriptions(i))
            all_keys.extend(d.key for d in _generate_outlet_binary_descriptions(i))
        assert len(all_keys) == len(set(all_keys))
