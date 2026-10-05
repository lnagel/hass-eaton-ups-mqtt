# Managers

There is 1 manager with prefix `mbdetnrs/1.0/managers/{managerId}`.

Topic `mbdetnrs/1.0/managers/1/identification` contains the following:

```json
{
  "firmwareVersion": "3.1.15",
  "physicalName": "Eaton Gigabit Network Card",
  "uuid": "390c8c7d-7247-442c-9810-0f2f6f770d65",
  "vendor": "Eaton",
  "product": "Gigabit Network Card",
  "serialNumber": "GZZPQK51FPK",
  "type": "management card",
  "partNumber": "320-Y6514-14",
  "hwVersion": "0",
  "name": "Eaton5PX",
  "contact": "",
  "location": "",
  "firmwareInstallationDate": 1707301493,
  "firmwareActivationDate": 1707301805,
  "firmwareDate": 1695387800,
  "firmwareSha": "cb8f68d",
  "bootloaderVersion": "3.0.2",
  "manufacturer": "Eaton",
  "macAddress": "2F:C2:31:B7:B0:87"
}
```

# Sensors

There are two main sensor topics with prefix `mbdetnrs/1.0/sensors/`.

Topic `mbdetnrs/1.0/sensors/status` contains the following:

```json
{
    "operating": 7,
    "health": 5
}
```

Topic `mbdetnrs/1.0/sensors/devices` contains the following:

```json
{
    "members@count": 0,
    "members": []
}
```

# Protection services

There are two main protection service topics with prefix `mbdetnrs/1.0/protectionService/`.

Topic `mbdetnrs/1.0/protectionService/suppliers` contains the following:

```json
{
    "members@count": 0,
    "members": []
}
```

Topic `mbdetnrs/1.0/protectionService/actions` contains the following:

```json
{
    "#scriptExec": "mbdetnrs/1.0/protectionService/actions/scriptExec??"
}
```

# Alarm services

There are two main alarm topics with prefix `mbdetnrs/1.0/alarmService/`.

Topic `mbdetnrs/1.0/alarmService/activeAlarms` contains the following:

```json
{
    "@id": "/mbdetnrs/1.0/alarmService/activeAlarms",
    "members@count": 0,
    "members": []
}
```

Topic `mbdetnrs/1.0/alarmService/mostCritical` contains the following:

```json
{}
```

# Power Services

## Suppliers

There are 1..n powerService suppliers with prefix `mbdetnrs/1.0/powerService/suppliers/{supplierId}`.

Topic `mbdetnrs/1.0/powerService/suppliers` contains the following:

```json
{
  "members@count": 3,
  "members": [
    {
      "@id": "mbdetnrs/1.0/powerService/suppliers/acWPSUdxWmSxL4f849URrg"
    },
    {
      "@id": "mbdetnrs/1.0/powerService/suppliers/suNLcr7pWISz7bK79b_dkg"
    },
    {
      "@id": "mbdetnrs/1.0/powerService/suppliers/sM_i2O-TVIa87BqzMc3FDA"
    }
  ]
}
```

Topic `mbdetnrs/1.0/powerService/suppliers/acWPSUdxWmSxL4f849URrg/controllers` contains the following:

```json
{
  "members@count": 4,
  "members":
  [
    {
      "@id": "mbdetnrs/1.0/scheduleService/schedulers/6gwp94ddUAGpoYYtmAzyCQ"
    },
    {
      "@id": "mbdetnrs/1.0/protectionService/suppliers/KW7cx1fhUim8rQyhkeS48A/triggers/power"
    },
    {
      "@id": "mbdetnrs/1.0/powerService/suppliers/sM_i2O-TVIa87BqzMc3FDA"
    },
    {
      "@id": "mbdetnrs/1.0/powerService/suppliers/suNLcr7pWISz7bK79b_dkg"
    }
  ]
}
```

Topic `mbdetnrs/1.0/powerService/suppliers/acWPSUdxWmSxL4f849URrg/identification` contains the following:

```json
{
  "uuid": "69c58f49-4771-5a64-b12f-87fce3d511ae",
  "manufacturer": "Eaton",
  "model": "Power Supplier",
  "serial": "",
  "physicalName": "PRIMARY",
  "name": "PRIMARY",
  "interface": "mbdetnrs/1.0/powerService/suppliers/acWPSUdxWmSxL4f849URrg",
  "version": "01.00.0000",
  "location": "",
  "contact": ""
}
```

Topic `mbdetnrs/1.0/powerService/suppliers/acWPSUdxWmSxL4f849URrg/configuration` contains the following:

```json
{
  "canProtect": true,
  "canSelfProtect": true,
  "connectorType": "unknown",
  "isControllable": true,
  "isSwitchable": true,
  "automaticSwitchOnEnabled": true,
  "automaticSwitchOnDelay": 0,
  "nominalActivePower": 1500.0,
  "nominalApparentPower": 1500.0,
  "nominalCurrent": 6.52173901,
  "nominalFrequency": 50.0,
  "nominalVoltage": 230.0,
  "powerCycleDuration": 10
}
```

Topic `mbdetnrs/1.0/powerService/suppliers/acWPSUdxWmSxL4f849URrg/summary` contains the following:

```json
{
  "mode": 4,
  "quality": 4,
  "poweringFor": -1,
  "estimatedPoweringFor": -1,
  "protectingFor": 15636,
  "loadPercent": 17.0,
  "protectionCapacityPercent": 99.0,
  "protectionLowCapacityAlarm": false,
  "protectionCapacityRuntime": 15636
}
```

Topic `mbdetnrs/1.0/powerService/suppliers/acWPSUdxWmSxL4f849URrg/schedule` contains the following:

```json
{
  "delayBeforePowerDown": -1,
  "delayBeforePowerUp": -1
}
```

Topic `mbdetnrs/1.0/powerService/suppliers/acWPSUdxWmSxL4f849URrg/powerDownMinimumDurations` contains the following:

```json
{
  "normal": 0,
  "critical": 0,
  "emergency": 0
}
```

Topic `mbdetnrs/1.0/powerService/suppliers/acWPSUdxWmSxL4f849URrg/measures` contains the following:

```json
{
  "activePower": 0.0,
  "apparentPower": 0.0,
  "current": 0.0,
  "frequency": 50.0,
  "powerFactor": 0.0,
  "voltage": 231.900009
}
```

Topic `mbdetnrs/1.0/powerService/suppliers/suNLcr7pWISz7bK79b_dkg/shutdownDurations` contains the following:

```json
{
  "normal": 0,
  "critical": 0
}
```

Topic `mbdetnrs/1.0/powerService/suppliers/suNLcr7pWISz7bK79b_dkg/estimatedPowerdownCommand` contains the following:

```json
{
  "timepoint": 4294967295,
  "severity": 0,
  "delay": -1
}
```

# Power Distributions

There are 1..n powerDistributions with prefix `mbdetnrs/1.0/powerDistributions/{powerDistributionId}/`.

## Backup system

Topic `mbdetnrs/1.0/powerDistributions/1/backupSystem/powerBank/chargers/1/status` contains the following:

```json
{
  "operating": "in service",
  "health": "ok",
  "active": true,
  "chargerStatus": "on not charging",
  "enabled": true,
  "installed": true,
  "internalFailure": false,
  "supply": true,
  "voltageTooHigh": false,
  "voltageTooLow": false,
  "mode": "abm"
}
```

Topic `mbdetnrs/1.0/powerDistributions/1/backupSystem/powerBank/measures` contains the following:

```json
{
  "remainingTime": 15636,
  "stateOfCharge": 99,
  "voltage": 52
}
```

Topic `mbdetnrs/1.0/powerDistributions/1/backupSystem/powerBank/settings` contains the following:

```json
{
  "replacementAlarmEnabled": true,
  "lowRuntimeThreshold": 900,
  "lowStateOfChargeThreshold": 20
}
```

Topic `mbdetnrs/1.0/powerDistributions/1/backupSystem/powerBank/specifications` contains the following:

```json
{
  "externalCount": 1,
  "remoteControlEnabled": true,
  "technology": "PbAc",
  "capacityAh": {
    "nominal": 27
  },
  "voltage": {
    "nominal": 48
  },
  "type": "batteries"
}
```

Topic `mbdetnrs/1.0/powerDistributions/1/backupSystem/powerBank/status` contains the following:

```json
{
  "operating": "stopped",
  "health": "ok",
  "criticalLowStateOfCharge": false,
  "internalFailure": false,
  "lastTestResult": "success",
  "lastTestResultDate": "2025-01-04T14:17:36.000Z",
  "lastSuccessfulTestDate": "2025-01-04T14:17:36.000Z",
  "lcmInstallationDate": "2021-10-26T11:11:46.000Z",
  "lcmReplacementDate": "2025-10-25T11:11:46.000Z",
  "lcmExpired": false,
  "lowStateOfCharge": false,
  "storagePresent": "present",
  "supplied": true,
  "supply": false,
  "testFailed": false,
  "testStatus": 3
}
```

## Identification

Topic `mbdetnrs/1.0/powerDistributions/1/identification` contains the following:

```json
{
  "uuid": "b9622317-7494-4877-b3c2-8ee8ba53bdb5",
  "physicalName": "Eaton 5PX 1500i RT2U G2",
  "friendlyName": "Eaton 5PX 1500i RT2U G2",
  "partNumber": "5PX1500IRT2UG2",
  "referenceNumber": "9910",
  "vendor": "EATON",
  "model": "Eaton 5PX 1500i RT2U G2",
  "serialNumber": "GFHJ7XVG0FN9",
  "type": "PowerDistribution",
  "productName": "Eaton 5PX",
  "firmwareVersion": "01.12.0024",
  "name": "Eaton 5PX 1500i RT2U G2"
}
```

## Inputs

There are 1..n inputs with prefix `mbdetnrs/1.0/powerDistributions/{powerDistributionId}/inputs/{inputId}/`.

Topic `mbdetnrs/1.0/powerDistributions/1/inputs/1/measures` contains the following:

```json
{
  "current": 1.1,
  "frequency": 50,
  "voltage": 230.8
}
```

Topic `mbdetnrs/1.0/powerDistributions/1/inputs/1/status` contains the following:

```json
{
  "operating": "in service",
  "health": "ok",
  "frequencyOutOfRange": false,
  "inRange": true,
  "internalFailure": false,
  "supplied": true,
  "supply": true,
  "voltageOutOfRange": false,
  "voltageTooHigh": false,
  "voltageTooLow": false,
  "wiringFault": false
}
```

There are 1..n phases with prefix `mbdetnrs/1.0/powerDistributions/{powerDistributionId}/inputs/{inputId}/phases/{phaseId}/`.

Topic `mbdetnrs/1.0/powerDistributions/1/inputs/1/phases/1/measures` contains the following:

```json
{
  "current": 1.1,
  "voltage": 230.8
}
```

## Outlets

There are 1..n outlets with prefix `mbdetnrs/1.0/powerDistributions/{powerDistributionId}/outlets/{outletId}/`.

Topic `mbdetnrs/1.0/powerDistributions/1/outlets/1/identification` contains the following:

```json
{
  "uuid": "70a61c75-10a1-4d89-a16c-a16cffcaea49",
  "physicalName": "PRIMARY",
  "friendlyName": "PRIMARY"
}
```

Topic `mbdetnrs/1.0/powerDistributions/1/outlets/1/measures` contains the following:

```json
{
  "activePower": 0,
  "apparentPower": 0,
  "averageEnergy": 1,
  "cumulatedEnergy": 1257753.0741692,
  "current": 0,
  "frequency": 50,
  "powerFactor": 0,
  "voltage": 231.9
}
```

Topic `mbdetnrs/1.0/powerDistributions/1/outlets/1/specifications` contains the following:

```json
{
  "feed": "Outputs.1",
  "switchable": false
}
```

Topic `mbdetnrs/1.0/powerDistributions/1/outlets/1/status` contains the following:

```json
{
  "operating": "in service",
  "health": "ok",
  "delayBeforeSwitchOff": -1,
  "delayBeforeSwitchOn": -1,
  "supply": true,
  "switchedOn": true,
  "supplierPowerQuality": "protecting"
}
```

There are also the actions possible for each outlet. For example, for outlet 1:

MQTT topic for cancelSwitchOff: `mbdetnrs/1.0/powerDistributions/1/outlets/1/actions/cancelSwitchOff`
MQTT topic for cancelSwitchOn: `mbdetnrs/1.0/powerDistributions/1/outlets/1/actions/cancelSwitchOn`
MQTT topic for switchOff: `mbdetnrs/1.0/powerDistributions/1/outlets/1/actions/switchOff`
MQTT topic for switchOn: `mbdetnrs/1.0/powerDistributions/1/outlets/1/actions/switchOn`

## Outputs

There are 1..n outputs with prefix `mbdetnrs/1.0/powerDistributions/{powerDistributionId}/outputs/{outputId}/`.

Topic `mbdetnrs/1.0/powerDistributions/1/outputs/1/measures` contains the following:

```json
{
  "activePower": 174,
  "apparentPower": 267,
  "averageEnergy": 179,
  "cumulatedEnergy": 4686421.1559296,
  "current": 1.1,
  "efficiency": 99,
  "frequency": 50,
  "percentLoad": 17,
  "powerFactor": 0.65,
  "voltage": 231.9
}
```

There are 1..n phases with prefix `mbdetnrs/1.0/powerDistributions/{powerDistributionId}/outputs/{outputId}/phases/{phaseId}/`.

Topic `mbdetnrs/1.0/powerDistributions/1/outputs/1/phases/1/measures` contains the following:

```json
{
  "activePower": 174,
  "apparentPower": 267,
  "current": 1.1,
  "percentLoad": 17,
  "powerFactor": 0.65,
  "voltage": 231.9
}
```

## Settings

Topic `mbdetnrs/1.0/powerDistributions/1/settings` contains the following:

```json
{
  "audibleAlarm": "disabled on battery",
  "automaticRestartEnabled": true,
  "automaticRestartLevel": 0,
  "forcedRebootEnabled": true,
  "nominalVoltage": 230,
  "remoteControlEnabled": true,
  "sensitivityMode": "high sensitivity",
  "voltageHighDetection": 294,
  "voltageLowDetection": 160
}
```

## Specifications

Topic `mbdetnrs/1.0/powerDistributions/1/specifications` contains the following:

```json
{
  "powerCycleDuration": 10,
  "supported": true,
  "topology": "line interactive",
  "voltageRange": "high voltage",
  "activePower": {
    "nominal": 1500
  },
  "apparentPower": {
    "nominal": 1500
  },
  "current": {
    "nominal": 6.5217
  },
  "frequency": {
    "nominal": 50
  },
  "percentLoad": {
    "highWarningThreshold": 102
  },
  "voltage": {
    "nominal": 230
  },
  "type": "ups"
}
```

## Status

Topic `mbdetnrs/1.0/powerDistributions/1/status` contains the following:

```json
{
  "operating": "in service",
  "health": "ok",
  "bootloaderMode": false,
  "communicationFault": false,
  "configurationFault": false,
  "delayBeforeSwitchOff": -1,
  "delayBeforeSwitchOn": -1,
  "emergencySwitchOff": false,
  "fanFault": false,
  "internalFailure": false,
  "shutdownImminent": false,
  "systemAlarm": false,
  "temperatureOutOfRange": false,
  "mode": "on line interactive normal"
}
```

## Environment

Topic `mbdetnrs/1.0/powerDistributions/1/environment/status` contains the following:

```json
{
  "health": "ok",
  "buildingAlarm1": false,
  "temperatureTooHigh": false
}
```

Topic `mbdetnrs/1.0/powerDistributions/1/environment/measures` contains the following:

```json
{}
```
