"""BlueprintEntity class."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DOMAIN
from .coordinator import EatonUPSDataUpdateCoordinator


class EatonUpsEntity(CoordinatorEntity[EatonUPSDataUpdateCoordinator]):
    """EatonUpsEntity class."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(self, coordinator: EatonUPSDataUpdateCoordinator) -> None:
        """Initialize."""
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.config_entry.entry_id)},
            name=f"Eaton UPS ({coordinator.config_entry.data.get('host')})",
            manufacturer="Eaton",
            model=self._get_model_info(),
            sw_version=self._get_firmware_version(),
        )

    def _get_model_info(self) -> str:
        """Get model information from the coordinator data."""
        if not self.coordinator.data:
            return "Eaton UPS"

        # Try to find model information in the data
        model = self.coordinator.data.get("device", {}).get("model")
        if model:
            return model

        return "Eaton UPS"

    def _get_firmware_version(self) -> str:
        """Get firmware version from the coordinator data."""
        if not self.coordinator.data:
            return None

        # Try to find firmware information in the data
        firmware = self.coordinator.data.get("device", {}).get("firmware")
        if firmware:
            return firmware

        return None