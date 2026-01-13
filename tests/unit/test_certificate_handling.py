"""Unit tests for certificate file handling."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from custom_components.eaton_ups_mqtt.api import EatonUpsMqttClient, EatonUpsMqttConfig


@pytest.fixture
def mqtt_config():
    """Create a test MQTT config."""
    return EatonUpsMqttConfig(
        host="test.example.com",
        port="8883",
        server_cert="-----BEGIN CERTIFICATE-----\nSERVER\n-----END CERTIFICATE-----",
        client_cert="-----BEGIN CERTIFICATE-----\nCLIENT\n-----END CERTIFICATE-----",
        client_key="-----BEGIN PRIVATE KEY-----\nKEY\n-----END PRIVATE KEY-----",
    )


@pytest.fixture
def mqtt_client(mqtt_config):
    """Create a client instance for testing."""
    session = MagicMock()
    return EatonUpsMqttClient(mqtt_config, session)


class TestCertificateFileManagement:
    """Tests for certificate temp file creation and cleanup."""

    def test_create_temp_files(self, mqtt_client):
        """Test temp files are created with correct content."""
        temp_files = mqtt_client._create_temp_files()

        assert len(temp_files) == 3

        # Verify files exist and contain expected content
        contents = ["SERVER", "CLIENT", "KEY"]
        for path, expected in zip(temp_files, contents, strict=False):
            assert Path(path).exists()
            assert expected in Path(path).read_text()

        # Cleanup
        mqtt_client._temp_files = temp_files
        mqtt_client._cleanup_temp_files()

    def test_cleanup_temp_files(self, mqtt_client):
        """Test temp files are deleted on cleanup."""
        temp_files = mqtt_client._create_temp_files()
        mqtt_client._temp_files = temp_files

        # Verify files exist
        for path in temp_files:
            assert Path(path).exists()

        mqtt_client._cleanup_temp_files()

        # Verify files are deleted
        for path in temp_files:
            assert not Path(path).exists()
        assert mqtt_client._temp_files == []

    def test_cleanup_handles_missing_files(self, mqtt_client):
        """Test cleanup handles already-deleted files gracefully."""
        mqtt_client._temp_files = ["/nonexistent/file1", "/nonexistent/file2"]
        # Should not raise
        mqtt_client._cleanup_temp_files()
        assert mqtt_client._temp_files == []

    def test_cleanup_empty_list(self, mqtt_client):
        """Test cleanup with empty file list."""
        mqtt_client._temp_files = []
        mqtt_client._cleanup_temp_files()
        assert mqtt_client._temp_files == []
