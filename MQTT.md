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
	"voltage": 52.9
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
	"lcmInstallationDate": "2022-10-18T12:26:32.000Z",
	"lcmReplacementDate": "2026-10-17T12:26:32.000Z",
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
	"voltage": 231.5
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
	"current": 1.1,
	"voltage": 231.9
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
	"activePower": 91,
	"apparentPower": 151,
	"averageEnergy": 83,
	"cumulatedEnergy": 1120826.0059357,
	"current": 0.5,
	"frequency": 49.9,
	"powerFactor": 0.6,
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

## Outputs

There are 1..n outputs with prefix `mbdetnrs/1.0/powerDistributions/{powerDistributionId}/outputs/{outputId}/`.

Topic `mbdetnrs/1.0/powerDistributions/1/outputs/1/measures` contains the following:

```json
{
	"activePower": 152,
	"apparentPower": 226,
	"averageEnergy": 155,
	"cumulatedEnergy": 3195829.9875259,
	"current": 1,
	"efficiency": 99,
	"frequency": 50,
	"percentLoad": 15,
	"powerFactor": 0.64,
	"voltage": 232.2
}
```

There are 1..n phases with prefix `mbdetnrs/1.0/powerDistributions/{powerDistributionId}/outputs/{outputId}/phases/{phaseId}/`.

Topic `mbdetnrs/1.0/powerDistributions/1/outputs/1/phases/1/measures` contains the following:

```json
{
	"activePower": 149,
	"apparentPower": 244,
	"current": 1,
	"percentLoad": 16,
	"powerFactor": 0.61,
	"voltage": 232.2
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
