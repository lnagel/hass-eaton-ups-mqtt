"""Sensor platform for eaton_ups."""

from __future__ import annotations

import re
from datetime import UTC, date, datetime
from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTime,
)
from homeassistant.helpers.entity import EntityCategory

from .entity import EatonUpsEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import EatonUPSDataUpdateCoordinator
    from .data import EatonUpsConfigEntry

# Define base entity descriptions for non-dynamic entities
BASE_ENTITY_DESCRIPTIONS = (
    # Manager Identification
    SensorEntityDescription(
        key="managers/1/identification$firmwareVersion",
        name="Manager Firmware Version",
        icon="mdi:information-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="managers/1/identification$physicalName",
        name="Manager Physical Name",
        icon="mdi:information-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="managers/1/identification$uuid",
        name="Manager UUID",
        icon="mdi:identifier",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="managers/1/identification$vendor",
        name="Manager Vendor",
        icon="mdi:domain",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="managers/1/identification$product",
        name="Manager Product",
        icon="mdi:package-variant",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="managers/1/identification$serialNumber",
        name="Manager Serial Number",
        icon="mdi:barcode",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="managers/1/identification$type",
        name="Manager Type",
        icon="mdi:card-text-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="managers/1/identification$partNumber",
        name="Manager Part Number",
        icon="mdi:numeric",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="managers/1/identification$hwVersion",
        name="Manager Hardware Version",
        icon="mdi:chip",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="managers/1/identification$name",
        name="Manager Name",
        icon="mdi:account-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="managers/1/identification$contact",
        name="Manager Contact",
        icon="mdi:account-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="managers/1/identification$location",
        name="Manager Location",
        icon="mdi:map-marker-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="managers/1/identification$firmwareInstallationDate",
        name="Manager Firmware Installation Date",
        icon="mdi:calendar-clock",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="managers/1/identification$firmwareActivationDate",
        name="Manager Firmware Activation Date",
        icon="mdi:calendar-clock",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="managers/1/identification$firmwareDate",
        name="Manager Firmware Date",
        icon="mdi:calendar-clock",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="managers/1/identification$firmwareSha",
        name="Manager Firmware SHA",
        icon="mdi:checkbox-marked-circle-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="managers/1/identification$bootloaderVersion",
        name="Manager Bootloader Version",
        icon="mdi:information-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="managers/1/identification$manufacturer",
        name="Manager Manufacturer",
        icon="mdi:factory",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="managers/1/identification$macAddress",
        name="Manager MAC Address",
        icon="mdi:ethernet",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    # Power Distribution Identification
    SensorEntityDescription(
        key="powerDistributions/1/identification$uuid",
        name="UPS UUID",
        icon="mdi:identifier",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="powerDistributions/1/identification$physicalName",
        name="UPS Physical Name",
        icon="mdi:label-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="powerDistributions/1/identification$friendlyName",
        name="UPS Friendly Name",
        icon="mdi:label-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="powerDistributions/1/identification$partNumber",
        name="UPS Part Number",
        icon="mdi:numeric",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="powerDistributions/1/identification$referenceNumber",
        name="UPS Reference Number",
        icon="mdi:numeric-9-plus-box-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="powerDistributions/1/identification$vendor",
        name="UPS Vendor",
        icon="mdi:domain",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="powerDistributions/1/identification$model",
        name="UPS Model",
        icon="mdi:information-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="powerDistributions/1/identification$serialNumber",
        name="UPS Serial Number",
        icon="mdi:information-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="powerDistributions/1/identification$type",
        name="UPS Type",
        icon="mdi:card-text-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="powerDistributions/1/identification$productName",
        name="UPS Product Name",
        icon="mdi:package-variant",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="powerDistributions/1/identification$firmwareVersion",
        name="UPS Firmware Version",
        icon="mdi:information-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="powerDistributions/1/identification$name",
        name="UPS Name",
        icon="mdi:label-outline",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    # Power Distribution Status
    SensorEntityDescription(
        key="powerDistributions/1/status$operating",
        name="UPS Operating Status",
        icon="mdi:power-settings",
    ),
    SensorEntityDescription(
        key="powerDistributions/1/status$health",
        name="UPS Health",
        icon="mdi:heart-pulse",
    ),
    SensorEntityDescription(
        key="powerDistributions/1/status$mode",
        name="UPS Mode",
        icon="mdi:power-settings",
    ),
    # Backup System - Power Bank Measures
    SensorEntityDescription(
        key="powerDistributions/1/backupSystem/powerBank/measures$remainingTime",
        name="Backup Remaining Time",
        icon="mdi:timer-outline",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="powerDistributions/1/backupSystem/powerBank/measures$stateOfCharge",
        name="Backup State of Charge",
        icon="mdi:battery",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="powerDistributions/1/backupSystem/powerBank/measures$voltage",
        name="Backup Voltage",
        icon="mdi:flash",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        suggested_display_precision=1,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # Backup System - Power Bank Settings
    SensorEntityDescription(
        key="powerDistributions/1/backupSystem/powerBank/settings$lowRuntimeThreshold",
        name="Backup Low Runtime Threshold",
        icon="mdi:timer-alert-outline",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
    ),
    SensorEntityDescription(
        key="powerDistributions/1/backupSystem/powerBank/settings$lowStateOfChargeThreshold",
        name="Backup Low Charge Threshold",
        icon="mdi:battery-alert",
        native_unit_of_measurement=PERCENTAGE,
    ),
    # Backup System - Power Bank Specifications
    SensorEntityDescription(
        key="powerDistributions/1/backupSystem/powerBank/specifications$externalCount",
        name="Backup External Count",
        icon="mdi:battery-multiple",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="powerDistributions/1/backupSystem/powerBank/specifications$technology",
        name="Backup Technology",
        icon="mdi:battery-heart-variant",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="powerDistributions/1/backupSystem/powerBank/specifications$capacityAh/nominal",
        name="Backup Nominal Capacity",
        icon="mdi:battery-charging",
        native_unit_of_measurement="Ah",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="powerDistributions/1/backupSystem/powerBank/specifications$voltage/nominal",
        name="Backup Nominal Voltage",
        icon="mdi:flash",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    # Backup System - Power Bank Status
    SensorEntityDescription(
        key="powerDistributions/1/backupSystem/powerBank/status$operating",
        name="Backup Operating Status",
        icon="mdi:battery-heart-outline",
    ),
    SensorEntityDescription(
        key="powerDistributions/1/backupSystem/powerBank/status$health",
        name="Backup Health",
        icon="mdi:heart-pulse",
    ),
    SensorEntityDescription(
        key="powerDistributions/1/backupSystem/powerBank/status$lastTestResult",
        name="Backup Last Test Result",
        icon="mdi:test-tube",
    ),
    SensorEntityDescription(
        key="powerDistributions/1/backupSystem/powerBank/status$lastTestResultDate",
        name="Backup Last Test Date",
        icon="mdi:calendar-clock",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    SensorEntityDescription(
        key="powerDistributions/1/backupSystem/powerBank/status$lcmInstallationDate",
        name="Backup Installation Date",
        icon="mdi:calendar-plus",
        device_class=SensorDeviceClass.DATE,
    ),
    SensorEntityDescription(
        key="powerDistributions/1/backupSystem/powerBank/status$lcmReplacementDate",
        name="Backup Replacement Date",
        icon="mdi:calendar-refresh",
        device_class=SensorDeviceClass.DATE,
    ),
    # Backup System - Charger Status
    SensorEntityDescription(
        key="powerDistributions/1/backupSystem/powerBank/chargers/1/status$operating",
        name="Charger Operating Status",
        icon="mdi:battery-charging",
    ),
    SensorEntityDescription(
        key="powerDistributions/1/backupSystem/powerBank/chargers/1/status$health",
        name="Charger Health",
        icon="mdi:heart-pulse",
    ),
    SensorEntityDescription(
        key="powerDistributions/1/backupSystem/powerBank/chargers/1/status$chargerStatus",
        name="Charger Status",
        icon="mdi:battery-charging-outline",
    ),
    SensorEntityDescription(
        key="powerDistributions/1/backupSystem/powerBank/chargers/1/status$mode",
        name="Charger Mode",
        icon="mdi:battery-charging-high",
    ),
    # Power Distribution Settings
    SensorEntityDescription(
        key="powerDistributions/1/settings$audibleAlarm",
        name="Audible Alarm",
        icon="mdi:volume-high",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="powerDistributions/1/settings$nominalVoltage",
        name="Nominal Voltage",
        icon="mdi:flash-alert",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="powerDistributions/1/settings$sensitivityMode",
        name="Sensitivity Mode",
        icon="mdi:tune",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="powerDistributions/1/settings$voltageHighDetection",
        name="Voltage High Detection",
        icon="mdi:flash-alert",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="powerDistributions/1/settings$voltageLowDetection",
        name="Voltage Low Detection",
        icon="mdi:flash-alert",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


def _generate_input_descriptions(input_num: int) -> tuple[SensorEntityDescription, ...]:
    """Generate sensor descriptions for a specific input."""
    return (
        SensorEntityDescription(
            key=f"powerDistributions/1/inputs/{input_num}/measures$voltage",
            name=f"Input {input_num} Voltage",
            icon="mdi:flash",
            native_unit_of_measurement=UnitOfElectricPotential.VOLT,
            suggested_display_precision=1,
            device_class=SensorDeviceClass.VOLTAGE,
            state_class=SensorStateClass.MEASUREMENT,
        ),
        SensorEntityDescription(
            key=f"powerDistributions/1/inputs/{input_num}/measures$frequency",
            name=f"Input {input_num} Frequency",
            icon="mdi:sine-wave",
            native_unit_of_measurement=UnitOfFrequency.HERTZ,
            suggested_display_precision=1,
            device_class=SensorDeviceClass.FREQUENCY,
            state_class=SensorStateClass.MEASUREMENT,
        ),
        SensorEntityDescription(
            key=f"powerDistributions/1/inputs/{input_num}/measures$current",
            name=f"Input {input_num} Current",
            icon="mdi:current-ac",
            native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
            suggested_display_precision=1,
            device_class=SensorDeviceClass.CURRENT,
            state_class=SensorStateClass.MEASUREMENT,
        ),
    )


def _generate_output_descriptions(
    output_num: int,
) -> tuple[SensorEntityDescription, ...]:
    """Generate sensor descriptions for a specific output."""
    return (
        SensorEntityDescription(
            key=f"powerDistributions/1/outputs/{output_num}/measures$voltage",
            name=f"Output {output_num} Voltage",
            icon="mdi:flash",
            native_unit_of_measurement=UnitOfElectricPotential.VOLT,
            suggested_display_precision=1,
            device_class=SensorDeviceClass.VOLTAGE,
            state_class=SensorStateClass.MEASUREMENT,
        ),
        SensorEntityDescription(
            key=f"powerDistributions/1/outputs/{output_num}/measures$frequency",
            name=f"Output {output_num} Frequency",
            icon="mdi:sine-wave",
            native_unit_of_measurement=UnitOfFrequency.HERTZ,
            suggested_display_precision=1,
            device_class=SensorDeviceClass.FREQUENCY,
            state_class=SensorStateClass.MEASUREMENT,
        ),
        SensorEntityDescription(
            key=f"powerDistributions/1/outputs/{output_num}/measures$current",
            name=f"Output {output_num} Current",
            icon="mdi:current-ac",
            native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
            suggested_display_precision=1,
            device_class=SensorDeviceClass.CURRENT,
            state_class=SensorStateClass.MEASUREMENT,
        ),
        SensorEntityDescription(
            key=f"powerDistributions/1/outputs/{output_num}/measures$activePower",
            name=f"Output {output_num} Active Power",
            icon="mdi:power-plug",
            native_unit_of_measurement=UnitOfPower.WATT,
            device_class=SensorDeviceClass.POWER,
            state_class=SensorStateClass.MEASUREMENT,
        ),
        SensorEntityDescription(
            key=f"powerDistributions/1/outputs/{output_num}/measures$apparentPower",
            name=f"Output {output_num} Apparent Power",
            icon="mdi:power-plug",
            native_unit_of_measurement="VA",
            state_class=SensorStateClass.MEASUREMENT,
        ),
        SensorEntityDescription(
            key=f"powerDistributions/1/outputs/{output_num}/measures$percentLoad",
            name=f"Output {output_num} Load",
            icon="mdi:gauge",
            native_unit_of_measurement=PERCENTAGE,
            state_class=SensorStateClass.MEASUREMENT,
        ),
        SensorEntityDescription(
            key=f"powerDistributions/1/outputs/{output_num}/measures$powerFactor",
            name=f"Output {output_num} Power Factor",
            icon="mdi:sine-wave",
            suggested_display_precision=2,
            state_class=SensorStateClass.MEASUREMENT,
        ),
        SensorEntityDescription(
            key=f"powerDistributions/1/outputs/{output_num}/measures$efficiency",
            name=f"Output {output_num} Efficiency",
            icon="mdi:lightning-bolt-outline",
            native_unit_of_measurement=PERCENTAGE,
            state_class=SensorStateClass.MEASUREMENT,
        ),
        SensorEntityDescription(
            key=f"powerDistributions/1/outputs/{output_num}/measures$cumulatedEnergy",
            name=f"Output {output_num} Energy",
            icon="mdi:lightning-bolt",
            native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
            suggested_display_precision=3,
            suggested_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
            device_class=SensorDeviceClass.ENERGY,
            state_class=SensorStateClass.TOTAL_INCREASING,
        ),
        SensorEntityDescription(
            key=f"powerDistributions/1/outputs/{output_num}/measures$averageEnergy",
            name=f"Output {output_num} Average Power",  # fixed name from Average Energy
            icon="mdi:lightning-bolt",
            native_unit_of_measurement=UnitOfPower.WATT,
            device_class=SensorDeviceClass.POWER,
            state_class=SensorStateClass.MEASUREMENT,
        ),
    )


def _generate_outlet_descriptions(
    outlet_num: int,
) -> tuple[SensorEntityDescription, ...]:
    """Generate sensor descriptions for a specific outlet."""
    return (
        SensorEntityDescription(
            key=f"powerDistributions/1/outlets/{outlet_num}/measures$cumulatedEnergy",
            name=f"Outlet {outlet_num} Energy",
            icon="mdi:lightning-bolt",
            native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
            suggested_display_precision=3,
            suggested_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
            device_class=SensorDeviceClass.ENERGY,
            state_class=SensorStateClass.TOTAL_INCREASING,
        ),
        SensorEntityDescription(
            key=f"powerDistributions/1/outlets/{outlet_num}/measures$averageEnergy",
            name=f"Outlet {outlet_num} Average Power",  # fixed name from Average Energy
            icon="mdi:lightning-bolt",
            native_unit_of_measurement=UnitOfPower.WATT,
            device_class=SensorDeviceClass.POWER,
            state_class=SensorStateClass.MEASUREMENT,
        ),
        SensorEntityDescription(
            key=f"powerDistributions/1/outlets/{outlet_num}/measures$activePower",
            name=f"Outlet {outlet_num} Active Power",
            icon="mdi:power-plug",
            native_unit_of_measurement=UnitOfPower.WATT,
            device_class=SensorDeviceClass.POWER,
            state_class=SensorStateClass.MEASUREMENT,
        ),
        SensorEntityDescription(
            key=f"powerDistributions/1/outlets/{outlet_num}/measures$apparentPower",
            name=f"Outlet {outlet_num} Apparent Power",
            icon="mdi:power-plug",
            native_unit_of_measurement="VA",
            state_class=SensorStateClass.MEASUREMENT,
        ),
        SensorEntityDescription(
            key=f"powerDistributions/1/outlets/{outlet_num}/measures$current",
            name=f"Outlet {outlet_num} Current",
            icon="mdi:current-ac",
            native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
            suggested_display_precision=1,
            device_class=SensorDeviceClass.CURRENT,
            state_class=SensorStateClass.MEASUREMENT,
        ),
        SensorEntityDescription(
            key=f"powerDistributions/1/outlets/{outlet_num}/measures$frequency",
            name=f"Outlet {outlet_num} Frequency",
            icon="mdi:sine-wave",
            native_unit_of_measurement=UnitOfFrequency.HERTZ,
            suggested_display_precision=1,
            device_class=SensorDeviceClass.FREQUENCY,
            state_class=SensorStateClass.MEASUREMENT,
        ),
        SensorEntityDescription(
            key=f"powerDistributions/1/outlets/{outlet_num}/measures$voltage",
            name=f"Outlet {outlet_num} Voltage",
            icon="mdi:flash",
            native_unit_of_measurement=UnitOfElectricPotential.VOLT,
            suggested_display_precision=1,
            device_class=SensorDeviceClass.VOLTAGE,
            state_class=SensorStateClass.MEASUREMENT,
        ),
        SensorEntityDescription(
            key=f"powerDistributions/1/outlets/{outlet_num}/measures$powerFactor",
            name=f"Outlet {outlet_num} Power Factor",
            icon="mdi:sine-wave",
            suggested_display_precision=2,
            state_class=SensorStateClass.MEASUREMENT,
        ),
        SensorEntityDescription(
            key=f"powerDistributions/1/outlets/{outlet_num}/status$delayBeforeSwitchOff",
            name=f"Outlet {outlet_num} Delay Before Switch Off",
            icon="mdi:timer-off-outline",
            native_unit_of_measurement=UnitOfTime.SECONDS,
            device_class=SensorDeviceClass.DURATION,
        ),
        SensorEntityDescription(
            key=f"powerDistributions/1/outlets/{outlet_num}/status$delayBeforeSwitchOn",
            name=f"Outlet {outlet_num} Delay Before Switch On",
            icon="mdi:timer-outline",
            native_unit_of_measurement=UnitOfTime.SECONDS,
            device_class=SensorDeviceClass.DURATION,
        ),
        SensorEntityDescription(
            key=f"powerDistributions/1/outlets/{outlet_num}/status$operating",
            name=f"Outlet {outlet_num} Operating Status",
            icon="mdi:power-settings",
        ),
        SensorEntityDescription(
            key=f"powerDistributions/1/outlets/{outlet_num}/status$health",
            name=f"Outlet {outlet_num} Health",
            icon="mdi:heart-pulse",
        ),
        SensorEntityDescription(
            key=f"powerDistributions/1/outlets/{outlet_num}/status$supplierPowerQuality",
            name=f"Outlet {outlet_num} Power Quality",
            icon="mdi:power-plug",
        ),
    )


def get_entity_descriptions(
    coordinator: EatonUPSDataUpdateCoordinator,
) -> tuple[SensorEntityDescription, ...]:
    """Get entity descriptions based on available MQTT topics."""
    descriptions = list(BASE_ENTITY_DESCRIPTIONS)

    # Detect inputs
    for input_num in range(1, 10):  # Check reasonable range
        if any(
            key.startswith(f"powerDistributions/1/inputs/{input_num}/")
            for key in coordinator.data
        ):
            descriptions.extend(_generate_input_descriptions(input_num))

    # Detect outputs
    for output_num in range(1, 10):
        if any(
            key.startswith(f"powerDistributions/1/outputs/{output_num}/")
            for key in coordinator.data
        ):
            descriptions.extend(_generate_output_descriptions(output_num))

    # Detect outlets
    for outlet_num in range(1, 10):
        if any(
            key.startswith(f"powerDistributions/1/outlets/{outlet_num}/")
            for key in coordinator.data
        ):
            descriptions.extend(_generate_outlet_descriptions(outlet_num))

    return tuple(descriptions)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: EatonUpsConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator = entry.runtime_data.coordinator

    # Wait for initial data
    await coordinator.async_config_entry_first_refresh()

    # Generate descriptions based on available data
    entity_descriptions = get_entity_descriptions(coordinator)

    async_add_entities(
        EatonUpsSensor(
            coordinator=coordinator,
            entity_description=entity_description,
        )
        for entity_description in entity_descriptions
    )


class EatonUpsSensor(EatonUpsEntity, SensorEntity):
    """eaton_ups sensor class."""

    def __init__(
        self,
        coordinator: EatonUPSDataUpdateCoordinator,
        entity_description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor class."""
        super().__init__(coordinator)
        self.entity_description = entity_description
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}_{entity_description.key}"
        )

    @property
    def native_value(self) -> Any:
        """Return the native value of the sensor."""
        if not self.coordinator.data:
            return None

        # Parse the key to extract topic and lookup path within the topic's data
        topic, lookup = self.entity_description.key.split("$", 1)
        lookup_parts = lookup.split("/")

        # Navigate through the data structure
        value = self.coordinator.data.get(topic, {})
        for part in lookup_parts:
            if not (isinstance(value, dict) and part in value):
                return None
            value = value[part]

        # Handle date and timestamp conversions if needed
        if self.entity_description.device_class == SensorDeviceClass.DATE:
            return self._convert_date(value)
        if self.entity_description.device_class == SensorDeviceClass.TIMESTAMP:
            return self._convert_timestamp(value)

        return value

    def _convert_date(self, value: Any) -> date | None:
        """Convert value to timestamp if possible."""
        if isinstance(value, int):
            # Handle Unix timestamp (e.g., 1738146293)
            try:
                return datetime.fromtimestamp(value, tz=UTC).date()
            except (ValueError, TypeError, OSError):
                return None

        if isinstance(value, str):
            # Handle ISO format timestamps (e.g., "2026-10-17T12:26:32.000Z")
            try:
                if re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{3}Z", value):
                    return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
            except (ValueError, TypeError):
                pass

        return None

    def _convert_timestamp(self, value: Any) -> datetime | None:
        """Convert value to timestamp if possible."""
        if isinstance(value, int):
            # Handle Unix timestamp (e.g., 1738146293)
            try:
                return datetime.fromtimestamp(value, tz=UTC)
            except (ValueError, TypeError, OSError):
                return None

        if isinstance(value, str):
            # Handle ISO format timestamps (e.g., "2026-10-17T12:26:32.000Z")
            try:
                if re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{3}Z", value):
                    return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass

        return None
