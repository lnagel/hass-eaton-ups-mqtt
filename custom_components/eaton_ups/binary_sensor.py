"""Binary sensor platform for eaton_ups."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)

from .entity import EatonUpsEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import EatonUPSDataUpdateCoordinator
    from .data import EatonUpsConfigEntry

ENTITY_DESCRIPTIONS = (
    # UPS Status
    BinarySensorEntityDescription(
        key="powerDistributions/1/status$bootloaderMode",
        name="Bootloader Mode",
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    BinarySensorEntityDescription(
        key="powerDistributions/1/status$communicationFault",
        name="Communication Fault",
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    BinarySensorEntityDescription(
        key="powerDistributions/1/status$configurationFault",
        name="Configuration Fault",
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    BinarySensorEntityDescription(
        key="powerDistributions/1/status$emergencySwitchOff",
        name="Emergency Switch Off",
        device_class=BinarySensorDeviceClass.SAFETY,
    ),
    BinarySensorEntityDescription(
        key="powerDistributions/1/status$fanFault",
        name="Fan Fault",
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    BinarySensorEntityDescription(
        key="powerDistributions/1/status$internalFailure",
        name="Internal Failure",
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    BinarySensorEntityDescription(
        key="powerDistributions/1/status$shutdownImminent",
        name="Shutdown Imminent",
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    BinarySensorEntityDescription(
        key="powerDistributions/1/status$systemAlarm",
        name="System Alarm",
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    BinarySensorEntityDescription(
        key="powerDistributions/1/status$temperatureOutOfRange",
        name="Temperature Out Of Range",
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    # Input Status
    BinarySensorEntityDescription(
        key="powerDistributions/1/inputs/1/status$frequencyOutOfRange",
        name="Input Frequency Out Of Range",
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    BinarySensorEntityDescription(
        key="powerDistributions/1/inputs/1/status$inRange",
        name="Input In Range",
        device_class=BinarySensorDeviceClass.POWER,
    ),
    BinarySensorEntityDescription(
        key="powerDistributions/1/inputs/1/status$internalFailure",
        name="Input Internal Failure",
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    BinarySensorEntityDescription(
        key="powerDistributions/1/inputs/1/status$supplied",
        name="Input Supplied",
    ),
    BinarySensorEntityDescription(
        key="powerDistributions/1/inputs/1/status$supply",
        name="Input Supply",
        device_class=BinarySensorDeviceClass.POWER,
    ),
    BinarySensorEntityDescription(
        key="powerDistributions/1/inputs/1/status$voltageOutOfRange",
        name="Input Voltage Out Of Range",
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    BinarySensorEntityDescription(
        key="powerDistributions/1/inputs/1/status$voltageTooHigh",
        name="Input Voltage Too High",
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    BinarySensorEntityDescription(
        key="powerDistributions/1/inputs/1/status$voltageTooLow",
        name="Input Voltage Too Low",
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    BinarySensorEntityDescription(
        key="powerDistributions/1/inputs/1/status$wiringFault",
        name="Input Wiring Fault",
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    # Battery Status
    BinarySensorEntityDescription(
        key="powerDistributions/1/backupSystem/powerBank/status$criticalLowStateOfCharge",
        name="Critical Low Battery",
        device_class=BinarySensorDeviceClass.BATTERY,
    ),
    BinarySensorEntityDescription(
        key="powerDistributions/1/backupSystem/powerBank/status$internalFailure",
        name="Battery Internal Failure",
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    BinarySensorEntityDescription(
        key="powerDistributions/1/backupSystem/powerBank/status$lcmExpired",
        name="Battery Expired",
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    BinarySensorEntityDescription(
        key="powerDistributions/1/backupSystem/powerBank/status$lowStateOfCharge",
        name="Low Battery",
        device_class=BinarySensorDeviceClass.BATTERY,
    ),
    BinarySensorEntityDescription(
        key="powerDistributions/1/backupSystem/powerBank/status$supplied",
        name="Battery Supplied",
    ),
    BinarySensorEntityDescription(
        key="powerDistributions/1/backupSystem/powerBank/status$supply",
        name="Battery Supply",
        device_class=BinarySensorDeviceClass.POWER,
    ),
    BinarySensorEntityDescription(
        key="powerDistributions/1/backupSystem/powerBank/status$testFailed",
        name="Battery Test Failed",
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    # Charger Status
    BinarySensorEntityDescription(
        key="powerDistributions/1/backupSystem/powerBank/chargers/1/status$active",
        name="Charger Active",
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
    ),
    BinarySensorEntityDescription(
        key="powerDistributions/1/backupSystem/powerBank/chargers/1/status$enabled",
        name="Charger Enabled",
    ),
    BinarySensorEntityDescription(
        key="powerDistributions/1/backupSystem/powerBank/chargers/1/status$installed",
        name="Charger Installed",
    ),
    BinarySensorEntityDescription(
        key="powerDistributions/1/backupSystem/powerBank/chargers/1/status$internalFailure",
        name="Charger Internal Failure",
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    BinarySensorEntityDescription(
        key="powerDistributions/1/backupSystem/powerBank/chargers/1/status$supply",
        name="Charger Supply",
        device_class=BinarySensorDeviceClass.POWER,
    ),
    BinarySensorEntityDescription(
        key="powerDistributions/1/backupSystem/powerBank/chargers/1/status$voltageTooHigh",
        name="Charger Voltage Too High",
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    BinarySensorEntityDescription(
        key="powerDistributions/1/backupSystem/powerBank/chargers/1/status$voltageTooLow",
        name="Charger Voltage Too Low",
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    # Environment Status
    BinarySensorEntityDescription(
        key="powerDistributions/1/environment/status$buildingAlarm1",
        name="Building Alarm",
        device_class=BinarySensorDeviceClass.SAFETY,
    ),
    BinarySensorEntityDescription(
        key="powerDistributions/1/environment/status$temperatureTooHigh",
        name="Temperature Too High",
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
    # Outlet Status
    BinarySensorEntityDescription(
        key="powerDistributions/1/outlets/1/status$supply",
        name="Outlet 1 Supply",
        device_class=BinarySensorDeviceClass.POWER,
    ),
    BinarySensorEntityDescription(
        key="powerDistributions/1/outlets/1/status$switchedOn",
        name="Outlet 1 Switched On",
        device_class=BinarySensorDeviceClass.POWER,
    ),
    BinarySensorEntityDescription(
        key="powerDistributions/1/outlets/2/status$supply",
        name="Outlet 2 Supply",
        device_class=BinarySensorDeviceClass.POWER,
    ),
    BinarySensorEntityDescription(
        key="powerDistributions/1/outlets/2/status$switchedOn",
        name="Outlet 2 Switched On",
        device_class=BinarySensorDeviceClass.POWER,
    ),
    BinarySensorEntityDescription(
        key="powerDistributions/1/outlets/3/status$supply",
        name="Outlet 3 Supply",
        device_class=BinarySensorDeviceClass.POWER,
    ),
    BinarySensorEntityDescription(
        key="powerDistributions/1/outlets/3/status$switchedOn",
        name="Outlet 3 Switched On",
        device_class=BinarySensorDeviceClass.POWER,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: EatonUpsConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the binary_sensor platform."""
    async_add_entities(
        EatonUpsBinarySensor(
            coordinator=entry.runtime_data.coordinator,
            entity_description=entity_description,
        )
        for entity_description in ENTITY_DESCRIPTIONS
    )


class EatonUpsBinarySensor(EatonUpsEntity, BinarySensorEntity):
    """eaton_ups binary_sensor class."""

    def __init__(
        self,
        coordinator: EatonUPSDataUpdateCoordinator,
        entity_description: BinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary_sensor class."""
        super().__init__(coordinator)
        self.entity_description = entity_description
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{entity_description.key}"

    @property
    def is_on(self) -> bool:
        """Return true if the binary_sensor is on."""
        if not self.coordinator.data:
            return False

        # Parse the key to extract topic and lookup path within the topic's data
        topic, lookup = self.entity_description.key.split("$", 1)
        lookup_parts = lookup.split("/")

        # Navigate through the data structure
        value = self.coordinator.data.get(topic, {})
        for part in lookup_parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return None

        # Convert to boolean
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ("true", "yes", "on", "1")
        if isinstance(value, (int, float)):
            return value > 0
        return False
