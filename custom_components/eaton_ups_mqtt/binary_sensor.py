"""Binary sensor platform for eaton_ups_mqtt."""

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

BASE_ENTITY_DESCRIPTIONS = (
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
)


def _generate_input_binary_descriptions(
    input_num: int,
) -> tuple[BinarySensorEntityDescription, ...]:
    """Generate binary sensor descriptions for a specific input."""
    return (
        BinarySensorEntityDescription(
            key=f"powerDistributions/1/inputs/{input_num}/status$frequencyOutOfRange",
            name=f"Input {input_num} Frequency Out Of Range",
            device_class=BinarySensorDeviceClass.PROBLEM,
        ),
        BinarySensorEntityDescription(
            key=f"powerDistributions/1/inputs/{input_num}/status$inRange",
            name=f"Input {input_num} In Range",
            device_class=BinarySensorDeviceClass.POWER,
        ),
        BinarySensorEntityDescription(
            key=f"powerDistributions/1/inputs/{input_num}/status$internalFailure",
            name=f"Input {input_num} Internal Failure",
            device_class=BinarySensorDeviceClass.PROBLEM,
        ),
        BinarySensorEntityDescription(
            key=f"powerDistributions/1/inputs/{input_num}/status$supplied",
            name=f"Input {input_num} Supplied",
        ),
        BinarySensorEntityDescription(
            key=f"powerDistributions/1/inputs/{input_num}/status$supply",
            name=f"Input {input_num} Supply",
            device_class=BinarySensorDeviceClass.POWER,
        ),
        BinarySensorEntityDescription(
            key=f"powerDistributions/1/inputs/{input_num}/status$voltageOutOfRange",
            name=f"Input {input_num} Voltage Out Of Range",
            device_class=BinarySensorDeviceClass.PROBLEM,
        ),
        BinarySensorEntityDescription(
            key=f"powerDistributions/1/inputs/{input_num}/status$voltageTooHigh",
            name=f"Input {input_num} Voltage Too High",
            device_class=BinarySensorDeviceClass.PROBLEM,
        ),
        BinarySensorEntityDescription(
            key=f"powerDistributions/1/inputs/{input_num}/status$voltageTooLow",
            name=f"Input {input_num} Voltage Too Low",
            device_class=BinarySensorDeviceClass.PROBLEM,
        ),
        BinarySensorEntityDescription(
            key=f"powerDistributions/1/inputs/{input_num}/status$wiringFault",
            name=f"Input {input_num} Wiring Fault",
            device_class=BinarySensorDeviceClass.PROBLEM,
        ),
    )


def _generate_outlet_binary_descriptions(
    outlet_num: int,
) -> tuple[BinarySensorEntityDescription, ...]:
    """Generate binary sensor descriptions for a specific outlet."""
    return (
        BinarySensorEntityDescription(
            key=f"powerDistributions/1/outlets/{outlet_num}/status$supply",
            name=f"Outlet {outlet_num} Supply",
            device_class=BinarySensorDeviceClass.POWER,
        ),
        BinarySensorEntityDescription(
            key=f"powerDistributions/1/outlets/{outlet_num}/status$switchedOn",
            name=f"Outlet {outlet_num} Switched On",
            device_class=BinarySensorDeviceClass.POWER,
        ),
    )


def get_binary_entity_descriptions(
    coordinator: EatonUPSDataUpdateCoordinator,
) -> tuple[BinarySensorEntityDescription, ...]:
    """Get binary entity descriptions based on available MQTT topics."""
    descriptions = list(BASE_ENTITY_DESCRIPTIONS)

    # Detect inputs
    for input_num in range(1, 10):  # Check reasonable range
        if any(
            key.startswith(f"powerDistributions/1/inputs/{input_num}/")
            for key in coordinator.data
        ):
            descriptions.extend(_generate_input_binary_descriptions(input_num))

    # Detect outlets
    for outlet_num in range(1, 10):
        if any(
            key.startswith(f"powerDistributions/1/outlets/{outlet_num}/")
            for key in coordinator.data
        ):
            descriptions.extend(_generate_outlet_binary_descriptions(outlet_num))

    return tuple(descriptions)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: EatonUpsConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the binary_sensor platform."""
    coordinator = entry.runtime_data.coordinator

    # Wait for initial data
    await coordinator.async_config_entry_first_refresh()

    # Generate descriptions based on available data
    entity_descriptions = get_binary_entity_descriptions(coordinator)

    async_add_entities(
        EatonUpsBinarySensor(
            coordinator=coordinator,
            entity_description=entity_description,
        )
        for entity_description in entity_descriptions
    )


class EatonUpsBinarySensor(EatonUpsEntity, BinarySensorEntity):
    """eaton_ups_mqtt binary_sensor class."""

    def __init__(
        self,
        coordinator: EatonUPSDataUpdateCoordinator,
        entity_description: BinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary_sensor class."""
        super().__init__(coordinator)
        self.entity_description = entity_description
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}_{entity_description.key}"
        )

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
        if isinstance(value, int | float):
            return value > 0
        return False
