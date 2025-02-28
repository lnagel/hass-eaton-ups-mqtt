"""Sensor platform for eaton_ups."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

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
)

from .entity import EatonUpsEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import EatonUPSDataUpdateCoordinator
    from .data import EatonUpsConfigEntry

# Define entity descriptions for common UPS metrics
ENTITY_DESCRIPTIONS = (
    # Identification
    SensorEntityDescription(
        key="identification/model",
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
    
    # Input metrics
    SensorEntityDescription(
        key="inputs/1/measures/voltage",
        name="Input Voltage",
        icon="mdi:flash",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="inputs/1/measures/frequency",
        name="Input Frequency",
        icon="mdi:sine-wave",
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="inputs/1/measures/current",
        name="Input Current",
        icon="mdi:current-ac",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    
    # Output metrics
    SensorEntityDescription(
        key="outputs/1/measures/voltage",
        name="Output Voltage",
        icon="mdi:flash",
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="outputs/1/measures/frequency",
        name="Output Frequency",
        icon="mdi:sine-wave",
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="outputs/1/measures/current",
        name="Output Current",
        icon="mdi:current-ac",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="outputs/1/measures/activePower",
        name="Output Power",
        icon="mdi:power-plug",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
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
        state_class=SensorStateClass.MEASUREMENT,
    ),
    
    # Status
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
    
    # Battery measures
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
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),

    # Battery settings
    SensorEntityDescription(
        key="backupSystem/powerBank/settings/lowRuntimeThreshold",
        name="Backup Low Runtime Threshold",
        icon="mdi:timer-alert-outline",
        native_unit_of_measurement=UnitOfTime.SECONDS,
        device_class=SensorDeviceClass.DURATION,
    ),
    SensorEntityDescription(
        key="backupSystem/powerBank/settings/lowStateOfChargeThreshold",
        name