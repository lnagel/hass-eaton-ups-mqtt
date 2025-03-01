# Eaton UPS Integration for Home Assistant

A Home Assistant integration that connects to Eaton UPS devices through their Network-M2/M3 management card via MQTT to monitor power status and battery levels. This integration provides:

- Device Information
  - Model, serial number, firmware details
  - UPS operating mode and health status
  - System alarms and fault conditions

- Power Metrics
  - Input/Output voltage, current, and frequency
  - Active and apparent power measurements
  - Power factor and load percentage
  - Energy consumption statistics

- Battery Information
  - Charge level and remaining runtime
  - Charging status and mode (e.g., ABM)
  - Battery test results and health
  - Installation and replacement dates

- Environmental Monitoring
  - Temperature status
  - Fan and system alerts

## Requirements

- An Eaton UPS device with Network-M2 or Network-M3 management card
- TLS certificates (mandatory):
  - Server certificate for the Network-M card
  - Client certificate and private key for authentication
  - These must be uploaded to the Network-M card's web interface
- Home Assistant 2023.8.0 or newer

## Installation

1. Add this repository to HACS or copy the `custom_components/eaton_ups` folder to your Home Assistant configuration directory
2. Restart Home Assistant
3. Add the integration through the Home Assistant UI
4. Configure with your UPS's MQTT connection details and certificates

## What?

This repository contains multiple files, here is a overview:

File | Purpose | Documentation
-- | -- | --
`.devcontainer.json` | Used for development/testing with Visual Studio Code. | [Documentation](https://code.visualstudio.com/docs/remote/containers)
`.github/ISSUE_TEMPLATE/*.yml` | Templates for the issue tracker | [Documentation](https://help.github.com/en/github/building-a-strong-community/configuring-issue-templates-for-your-repository)
`custom_components/eaton_ups/*` | Integration files, this is where everything happens. | [Documentation](https://developers.home-assistant.io/docs/creating_component_index)
`CONTRIBUTING.md` | Guidelines on how to contribute. | [Documentation](https://help.github.com/en/github/building-a-strong-community/setting-guidelines-for-repository-contributors)
`LICENSE` | The license file for the project. | [Documentation](https://help.github.com/en/github/creating-cloning-and-archiving-repositories/licensing-a-repository)
`README.md` | The file you are reading now, should contain info about the integration, installation and configuration instructions. | [Documentation](https://help.github.com/en/github/writing-on-github/basic-writing-and-formatting-syntax)
`requirements.txt` | Python packages used for development/lint/testing this integration. | [Documentation](https://pip.pypa.io/en/stable/user_guide/#requirements-files)

## Next steps

These are some next steps you may want to look into:
- Add tests to your integration, [`pytest-homeassistant-custom-component`](https://github.com/MatthewFlamm/pytest-homeassistant-custom-component) can help you get started.
- Add brand images (logo/icon) to https://github.com/home-assistant/brands.
- Create your first release.
- Share your integration on the [Home Assistant Forum](https://community.home-assistant.io/).
- Submit your integration to [HACS](https://hacs.xyz/docs/publish/start).
