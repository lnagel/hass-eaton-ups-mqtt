# Managers

There is 1 manager with prefix `mbdetnrs/1.0/managers/{managerId}`.

Topic `mbdetnrs/1.0/managers/1/identification` contains the following:

```json
{
	"firmwareVersion": "3.1.15",
	"physicalName": "Eaton Gigabit Network Card",
	"uuid": "9c7ee7d3-d046-5120-a766-b2c11ce7fafa",
	"vendor": "Eaton",
	"product": "Gigabit Network Card",
	"serialNumber": "G312N07BB4",
	"type": "management card",
	"partNumber": "744-A3983-02",
	"hwVersion": "0",
	"name": "Eaton5PX",
	"contact": "",
	"location": "",
	"firmwareInstallationDate": 1738146293,
	"firmwareActivationDate": 1738146605,
	"firmwareDate": 1726232600,
	"firmwareSha": "f21a1ed",
	"bootloaderVersion": "3.0.2",
	"manufacturer": "Eaton",
	"macAddress": "00:20:85:D2:23:E8"
}
```

# Sensors

To be documented.

# Protection services

To be documented.

# Alarm services

To be documented.

# Power Services

## Suppliers

There are 1..n powerService suppliers with prefix `mbdetnrs/1.0/powerService/suppliers/{supplierId}`.

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
  "nominalActivePower": 1.50000000e+03,
  "nominalApparentPower": 1.50000000e+03,
  "nominalCurrent": 6.52173901e+00,
  "nominalFrequency": 5.00000000e+01,
  "nominalVoltage": 2.30000000e+02,
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
  "protectingFor": 18971,
  "loadPercent": 1.50000000e+01,
  "protectionCapacityPercent": 1.00000000e+02,
  "protectionLowCapacityAlarm": false,
  "protectionCapacityRuntime": 18971
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
  "activePower": 8.80000000e+01,
  "apparentPower": 1.61000000e+02,
  "current": 5.00000000e-01,
  "frequency": 4.99000015e+01,
  "powerFactor": 5.40000021e-01,
  "voltage": 2.32900009e+02
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
	"remainingTime": 18971,
	"stateOfCharge": 100,
	"voltage": 52.8
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
	"lastTestResultDate": "2025-02-25T12:40:02.000Z",
	"lastSuccessfulTestDate": "2025-02-25T12:40:02.000Z",
	"lcmInstallationDate": "2022-10-18T12:26:28.000Z",
	"lcmReplacementDate": "2026-10-17T12:26:28.000Z",
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
	"uuid": "50c6eedb-7666-5e51-a07c-5fcf3eae6085",
	"physicalName": "Eaton 5PX 1500i RT2U G2",
	"friendlyName": "Eaton 5PX 1500i RT2U G2",
	"partNumber": "5PX1500IRT2UG2",
	"referenceNumber": "9910",
	"vendor": "EATON",
	"model": "Eaton 5PX 1500i RT2U G2",
	"serialNumber": "GF21N13275",
	"type": "PowerDistribution",
	"productName": "Eaton 5PX",
	"firmwareVersion": "01.12.0024",
	"name": "Eaton 5PX 1500i RT2U G2"
}
```

## Inputs

There are 1..n inputs with prefix `mbdetnrs/1.0/powerDistributions/{powerDistributionId}/outlets/{inputId}/`.

Topic `mbdetnrs/1.0/powerDistributions/1/inputs/1/measures` contains the following:

```json
{
	"current": 1,
	"frequency": 49.9,
	"voltage": 234.0
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

There are 1..n phases with prefix `mbdetnrs/1.0/powerDistributions/{powerDistributionId}/outlets/{inputId}/phases/{phaseId}/`.

Topic `mbdetnrs/1.0/powerDistributions/1/inputs/1/phases/1/measures` contains the following:

```json
{
	"current": 1.0,
	"voltage": 234.0
}
```

## Outlets

There are 1..n outlets with prefix `mbdetnrs/1.0/powerDistributions/{powerDistributionId}/outlets/{outletId}/`.

Topic `mbdetnrs/1.0/powerDistributions/1/outlets/1/identification` contains the following:

```json
{
	"uuid": "48d4d642-82c3-594e-b830-9004677d8bbd",
	"physicalName": "PRIMARY",
	"friendlyName": "PRIMARY"
}
```

Topic `mbdetnrs/1.0/powerDistributions/1/outlets/1/measures` contains the following:

```json
{
	"activePower": 85,
	"apparentPower": 146,
	"averageEnergy": 83,
	"cumulatedEnergy": 1123102.9778719,
	"current": 0.5,
	"frequency": 49.9,
	"powerFactor": 0.59,
	"voltage": 234.0
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
	"activePower": 146,
	"apparentPower": 226,
	"averageEnergy": 158,
	"cumulatedEnergy": 3201624.1550446,
	"current": 1,
	"efficiency": 99,
	"frequency": 49.9,
	"percentLoad": 15,
	"powerFactor": 0.65,
	"voltage": 234.0
}
```

There are 1..n phases with prefix `mbdetnrs/1.0/powerDistributions/{powerDistributionId}/outputs/{outputId}/phases/{phaseId}/`.

Topic `mbdetnrs/1.0/powerDistributions/1/outputs/1/phases/1/measures` contains the following:

```json
{
	"activePower": 146,
	"apparentPower": 226,
	"current": 1,
	"percentLoad": 15,
	"powerFactor": 0.65,
	"voltage": 234.0
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
