"""Diagnostics support for Eaton UPS."""
from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant

from . import EatonUpsConfigEntry
from .const import DOMAIN
from .coordinator import EatonUPSDataUpdateCoordinator

async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, config_entry: EatonUpsConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator: EatonUPSDataUpdateCoordinator = config_entry.runtime_data.coordinator

    # Get manager identification data from coordinator
    # The path matches the MQTT topic structure from the documentation
    identification_topic = "mbdetnrs/1.0/managers/1/identification"
    manager_data = coordinator.data.get(identification_topic, {})

    return {
        "manager_identification": {
            "firmware_version": manager_data.get("firmwareVersion"),
            "physical_name": manager_data.get("physicalName"), 
            "uuid": manager_data.get("uuid"),
            "vendor": manager_data.get("vendor"),
            "product": manager_data.get("product"),
            "serial_number": manager_data.get("serialNumber"),
            "type": manager_data.get("type"),
            "part_number": manager_data.get("partNumber"),
            "hw_version": manager_data.get("hwVersion"),
            "name": manager_data.get("name"),
            "contact": manager_data.get("contact"),
            "location": manager_data.get("location"),
            "firmware_installation_date": manager_data.get("firmwareInstallationDate"),
            "firmware_activation_date": manager_data.get("firmwareActivationDate"), 
            "firmware_date": manager_data.get("firmwareDate"),
            "firmware_sha": manager_data.get("firmwareSha"),
            "bootloader_version": manager_data.get("bootloaderVersion"),
            "manufacturer": manager_data.get("manufacturer"),
            "mac_address": manager_data.get("macAddress")
        }
    }
