"""Sensor platform for eaton_ups."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from datetime import datetime
import re

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    UnitOfElectricPotential,
    UnitOfTime,
    UnitOfPower,
    UnitOfElectricCurrent,
    UnitOfFrequency,
    UnitOfEnergy,
)

from .entity import EatonUpsEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import EatonUPSDataUpdateCoordinator
    from .data import EatonUpsConfigEntry

# Define entity descriptions grouped according to MQTT API structure
ENTITY_DESCRIPTIONS = (
    # Power Distribution Identification
    SensorEntityDescription(
        key="powerDistributions/1/identification/model",
        name="UPS Model",
        icon="mdi:information-outline",
    ),
    SensorEntityDescription(
        key="identification/firmwareVersion",
        name="UPS Firmware Version",
        icon="mdi:information-outline",
    ),
    SensorEntityDescription(
        key="identification/serialNumber",
        name="UPS Serial Number",
        icon="mdi:information-outline",
    ),
    # Power Distribution Input Measures
    SensorEntityDescription(
        key="inputs/1/measures/voltage",
        name="Input Voltage",
        icon="mdi:flash",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        suggested_display_precision=1,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="inputs/1/measures/frequency",
        name="Input Frequency",
        icon="mdi:sine-wave",
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        suggested_display_precision=1,
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="inputs/1/measures/current",
        name="Input Current",
        icon="mdi:current-ac",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        suggested_display_precision=1,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # Power Distribution Output Measures
    SensorEntityDescription(
        key="outputs/1/measures/voltage",
        name="Output Voltage",
        icon="mdi:flash",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        suggested_display_precision=1,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="outputs/1/measures/frequency",
        name="Output Frequency",
        icon="mdi:sine-wave",
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        suggested_display_precision=1,
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="outputs/1/measures/current",
        name="Output Current",
        icon="mdi:current-ac",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        suggested_display_precision=1,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="outputs/1/measures/activePower",
        name="Output Active Power",
        icon="mdi:power-plug",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="outputs/1/measures/apparentPower",
        name="Output Apparent Power",
        icon="mdi:power-plug",
        native_unit_of_measurement="VA",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="outputs/1/measures/percentLoad",
        name="Output Load",
        icon="mdi:gauge",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="outputs/1/measures/powerFactor",
        name="Output Power Factor",
        icon="mdi:sine-wave",
        suggested_display_precision=2,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="outputs/1/measures/efficiency",
        name="Output Efficiency",
        icon="mdi:lightning-bolt-outline",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # Output Energy
    SensorEntityDescription(
        key="outputs/1/measures/cumulatedEnergy",
        name="Output Energy",
        icon="mdi:lightning-bolt",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        suggested_display_precision=3,
        suggested_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    SensorEntityDescription(
        key="outputs/1/measures/averageEnergy",
        name="Output Average Power", # fixed name from Average Energy
        icon="mdi:lightning-bolt",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # Power Distribution Status
    SensorEntityDescription(
        key="status/operating",
        name="UPS Operating Status",
        icon="mdi:power-settings",
    ),
    SensorEntityDescription(
        key="status/health",
        name="UPS Health",
        icon="mdi:heart-pulse",
    ),
    SensorEntityDescription(
        key="status/mode",
        name="UPS Mode",
        icon="mdi:power-settings",
    ),
    # Backup System - Power Bank Measures
    SensorEntityDescription(
        key="backupSystem/powerBank/measures/remainingTime",
        name="Backup Remaining Time",
        icon="mdi:timer-outline",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="backupSystem/powerBank/measures/stateOfCharge",
        name="Backup State of Charge",
        icon="mdi:battery",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="backupSystem/powerBank/measures/voltage",
        name="Backup Voltage",
        icon="mdi:flash",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        suggested_display_precision=1,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # Backup System - Power Bank Settings
    SensorEntityDescription(
        key="backupSystem/powerBank/settings/lowRuntimeThreshold",
        name="Backup Low Runtime Threshold",
        icon="mdi:timer-alert-outline",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
    ),
    SensorEntityDescription(
        key="backupSystem/powerBank/settings/lowStateOfChargeThreshold",
        name="Backup Low Charge Threshold",
        icon="mdi:battery-alert",
        native_unit_of_measurement=PERCENTAGE,
    ),
    # Backup System - Power Bank Specifications
    SensorEntityDescription(
        key="backupSystem/powerBank/specifications/externalCount",
        name="Backup External Count",
        icon="mdi:battery-multiple",
    ),
    SensorEntityDescription(
        key="backupSystem/powerBank/specifications/technology",
        name="Backup Technology",
        icon="mdi:battery-heart-variant",
    ),
    SensorEntityDescription(
        key="backupSystem/powerBank/specifications/capacityAh/nominal",
        name="Backup Nominal Capacity",
        icon="mdi:battery-charging",
        native_unit_of_measurement="Ah",
    ),
    SensorEntityDescription(
        key="backupSystem/powerBank/specifications/voltage/nominal",
        name="Backup Nominal Voltage",
        icon="mdi:flash",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
    ),
    # Backup System - Power Bank Status
    SensorEntityDescription(
        key="backupSystem/powerBank/status/operating",
        name="Backup Operating Status",
        icon="mdi:battery-heart-outline",
    ),
    SensorEntityDescription(
        key="backupSystem/powerBank/status/health",
        name="Backup Health",
        icon="mdi:heart-pulse",
    ),
    SensorEntityDescription(
        key="backupSystem/powerBank/status/lastTestResult",
        name="Backup Last Test Result",
        icon="mdi:test-tube",
    ),
    SensorEntityDescription(
        key="backupSystem/powerBank/status/lastTestResultDate",
        name="Backup Last Test Date",
        icon="mdi:calendar-clock",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    SensorEntityDescription(
        key="backupSystem/powerBank/status/lcmInstallationDate",
        name="Backup Installation Date",
        icon="mdi:calendar-plus",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    SensorEntityDescription(
        key="backupSystem/powerBank/status/lcmReplacementDate",
        name="Backup Replacement Date",
        icon="mdi:calendar-refresh",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    # Backup System - Charger Status
    SensorEntityDescription(
        key="backupSystem/powerBank/chargers/1/status/operating",
        name="Charger Operating Status",
        icon="mdi:battery-charging",
    ),
    SensorEntityDescription(
        key="backupSystem/powerBank/chargers/1/status/health",
        name="Charger Health",
        icon="mdi:heart-pulse",
    ),
    SensorEntityDescription(
        key="backupSystem/powerBank/chargers/1/status/chargerStatus",
        name="Charger Status",
        icon="mdi:battery-charging-outline",
    ),
    SensorEntityDescription(
        key="backupSystem/powerBank/chargers/1/status/mode",
        name="Charger Mode",
        icon="mdi:battery-charging-high",
    ),
    # Power Distribution Settings
    SensorEntityDescription(
        key="settings/audibleAlarm",
        name="Audible Alarm",
        icon="mdi:volume-high",
    ),
    SensorEntityDescription(
        key="settings/sensitivityMode",
        name="Sensitivity Mode",
        icon="mdi:tune",
    ),
    SensorEntityDescription(
        key="settings/voltageHighDetection",
        name="Voltage High Detection",
        icon="mdi:flash-alert",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
    ),
    SensorEntityDescription(
        key="settings/voltageLowDetection",
        name="Voltage Low Detection",
        icon="mdi:flash-alert",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
    ),
    # Power Distribution - Outlet 1 Measures
    SensorEntityDescription(
        key="outlets/1/measures/cumulatedEnergy",
        name="Outlet 1 Energy",
        icon="mdi:lightning-bolt",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        suggested_display_precision=3,
        suggested_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    SensorEntityDescription(
        key="outlets/1/measures/averageEnergy",
        name="Outlet 1 Average Power", # fixed name from Average Energy
        icon="mdi:lightning-bolt",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="outlets/1/measures/activePower",
        name="Outlet 1 Active Power",
        icon="mdi:power-plug",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="outlets/1/measures/apparentPower",
        name="Outlet 1 Apparent Power",
        icon="mdi:power-plug",
        native_unit_of_measurement="VA",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="outlets/1/measures/current",
        name="Outlet 1 Current",
        icon="mdi:current-ac",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        suggested_display_precision=1,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="outlets/1/measures/frequency",
        name="Outlet 1 Frequency",
        icon="mdi:sine-wave",
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        suggested_display_precision=1,
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="outlets/1/measures/voltage",
        name="Outlet 1 Voltage",
        icon="mdi:flash",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        suggested_display_precision=1,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="outlets/1/measures/powerFactor",
        name="Outlet 1 Power Factor",
        icon="mdi:sine-wave",
        suggested_display_precision=2,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="outlets/1/status/delayBeforeSwitchOff",
        name="Outlet 1 Delay Before Switch Off",
        icon="mdi:timer-off-outline",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
    ),
    SensorEntityDescription(
        key="outlets/1/status/delayBeforeSwitchOn",
        name="Outlet 1 Delay Before Switch On",
        icon="mdi:timer-outline",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
    ),
    # Power Distribution - Outlet 2 Measures
    SensorEntityDescription(
        key="outlets/2/measures/cumulatedEnergy",
        name="Outlet 2 Energy",
        icon="mdi:lightning-bolt",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        suggested_display_precision=3,
        suggested_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    SensorEntityDescription(
        key="outlets/2/measures/averageEnergy",
        name="Outlet 2 Average Power", # fixed name from Average Energy
        icon="mdi:lightning-bolt",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="outlets/2/measures/activePower",
        name="Outlet 2 Active Power",
        icon="mdi:power-plug",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="outlets/2/measures/apparentPower",
        name="Outlet 2 Apparent Power",
        icon="mdi:power-plug",
        native_unit_of_measurement="VA",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="outlets/2/measures/current",
        name="Outlet 2 Current",
        icon="mdi:current-ac",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        suggested_display_precision=1,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="outlets/2/measures/frequency",
        name="Outlet 2 Frequency",
        icon="mdi:sine-wave",
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        suggested_display_precision=1,
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="outlets/2/measures/voltage",
        name="Outlet 2 Voltage",
        icon="mdi:flash",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        suggested_display_precision=1,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="outlets/2/measures/powerFactor",
        name="Outlet 2 Power Factor",
        icon="mdi:sine-wave",
        suggested_display_precision=2,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="outlets/2/status/delayBeforeSwitchOff",
        name="Outlet 2 Delay Before Switch Off",
        icon="mdi:timer-off-outline",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
    ),
    SensorEntityDescription(
        key="outlets/2/status/delayBeforeSwitchOn",
        name="Outlet 2 Delay Before Switch On",
        icon="mdi:timer-outline",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
    ),
    # Power Distribution - Outlet 3 Measures
    SensorEntityDescription(
        key="outlets/3/measures/cumulatedEnergy",
        name="Outlet 3 Energy",
        icon="mdi:lightning-bolt",
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        suggested_display_precision=3,
        suggested_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    SensorEntityDescription(
        key="outlets/3/measures/averageEnergy",
        name="Outlet 3 Average Power", # fixed name from Average Energy
        icon="mdi:lightning-bolt",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="outlets/3/measures/activePower",
        name="Outlet 3 Active Power",
        icon="mdi:power-plug",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="outlets/3/measures/apparentPower",
        name="Outlet 3 Apparent Power",
        icon="mdi:power-plug",
        native_unit_of_measurement="VA",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="outlets/3/measures/current",
        name="Outlet 3 Current",
        icon="mdi:current-ac",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        suggested_display_precision=1,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="outlets/3/measures/frequency",
        name="Outlet 3 Frequency",
        icon="mdi:sine-wave",
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        suggested_display_precision=1,
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="outlets/3/measures/voltage",
        name="Outlet 3 Voltage",
        icon="mdi:flash",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        suggested_display_precision=1,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="outlets/3/measures/powerFactor",
        name="Outlet 3 Power Factor",
        icon="mdi:sine-wave",
        suggested_display_precision=2,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="outlets/3/status/delayBeforeSwitchOff",
        name="Outlet 3 Delay Before Switch Off",
        icon="mdi:timer-off-outline",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
    ),
    SensorEntityDescription(
        key="outlets/3/status/delayBeforeSwitchOn",
        name="Outlet 3 Delay Before Switch On",
        icon="mdi:timer-outline",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
    ),
    # Power Distribution - Outlet Status
    SensorEntityDescription(
        key="outlets/1/status/operating",
        name="Outlet 1 Operating Status",
        icon="mdi:power-settings",
    ),
    SensorEntityDescription(
        key="outlets/1/status/health",
        name="Outlet 1 Health",
        icon="mdi:heart-pulse",
    ),
    SensorEntityDescription(
        key="outlets/1/status/supplierPowerQuality",
        name="Outlet 1 Power Quality",
        icon="mdi:power-plug",
    ),
    SensorEntityDescription(
        key="outlets/2/status/operating",
        name="Outlet 2 Operating Status",
        icon="mdi:power-settings",
    ),
    SensorEntityDescription(
        key="outlets/2/status/health",
        name="Outlet 2 Health",
        icon="mdi:heart-pulse",
    ),
    SensorEntityDescription(
        key="outlets/2/status/supplierPowerQuality",
        name="Outlet 2 Power Quality",
        icon="mdi:power-plug",
    ),
    SensorEntityDescription(
        key="outlets/3/status/operating",
        name="Outlet 3 Operating Status",
        icon="mdi:power-settings",
    ),
    SensorEntityDescription(
        key="outlets/3/status/health",
        name="Outlet 3 Health",
        icon="mdi:heart-pulse",
    ),
    SensorEntityDescription(
        key="outlets/3/status/supplierPowerQuality",
        name="Outlet 3 Power Quality",
        icon="mdi:power-plug",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: EatonUpsConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    async_add_entities(
        EatonUpsSensor(
            coordinator=entry.runtime_data.coordinator,
            entity_description=entity_description,
        )
        for entity_description in ENTITY_DESCRIPTIONS
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
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{entity_description.key}"

    @property
    def native_value(self) -> Any:
        """Return the native value of the sensor."""
        if not self.coordinator.data:
            return None

        # Parse the key path
        key_parts = self.entity_description.key.split("/")

        # Navigate through the data structure
        value = self.coordinator.data
        for part in key_parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return None

        # Convert string timestamps to datetime objects if this is a timestamp sensor
        if self.entity_description.device_class == SensorDeviceClass.TIMESTAMP and isinstance(value, str):
            try:
                # Handle ISO format timestamps (e.g., "2026-10-17T12:26:32.000Z")
                if re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{3}Z", value):
                    return datetime.fromisoformat(value.replace("Z", "+00:00"))
                # Handle other potential timestamp formats as needed
                return None
            except (ValueError, TypeError):
                # If conversion fails, return None instead of the string
                return None

        return value
