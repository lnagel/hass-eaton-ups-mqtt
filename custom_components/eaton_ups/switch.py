"""Switch platform for eaton_ups."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription

from .entity import EatonUpsEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import EatonUPSDataUpdateCoordinator
    from .data import EatonUpsConfigEntry

ENTITY_DESCRIPTIONS = (
    SwitchEntityDescription(
        key="control/outlet1",
        name="Outlet 1",
        icon="mdi:power-socket",
    ),
    SwitchEntityDescription(
        key="control/outlet2",
        name="Outlet 2",
        icon="mdi:power-socket",
    ),
    SwitchEntityDescription(
        key="control/test",
        name="Battery Test",
        icon="mdi:battery-check",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: EatonUpsConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the switch platform."""
    async_add_entities(
        EatonUpsSwitch(
            coordinator=entry.runtime_data.coordinator,
            entity_description=entity_description,
        )
        for entity_description in ENTITY_DESCRIPTIONS
    )


class EatonUpsSwitch(EatonUpsEntity, SwitchEntity):
    """eaton_ups switch class."""

    def __init__(
        self,
        coordinator: EatonUPSDataUpdateCoordinator,
        entity_description: SwitchEntityDescription,
    ) -> None:
        """Initialize the switch class."""
        super().__init__(coordinator)
        self.entity_description = entity_description
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{entity_description.key}"

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""
        if not self.coordinator.data:
            return False

        # Parse the key path
        key_parts = self.entity_description.key.split('/')

        # Get value from status path
        # (assuming control paths have corresponding status indicators)
        status_parts = ["status"] + key_parts[1:]

        # Navigate through the data structure
        value = self.coordinator.data
        for part in status_parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return False

        # Convert to boolean
        if isinstance(value, bool):
            return value
        elif isinstance(value, str):
            return value.lower() in ("true", "yes", "on", "1")
        elif isinstance(value, (int, float)):
            return value > 0
        else:
            return False

    async def async_turn_on(self, **_: Any) -> None:
        """Turn on the switch."""
        key_parts = self.entity_description.key.split('/')
        command = f"{key_parts[-1]}_on"

        await self.coordinator.config_entry.runtime_data.client.async_set_title(command)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **_: Any) -> None:
        """Turn off the switch."""
        key_parts = self.entity_description.key.split('/')
        command = f"{key_parts[-1]}_off"

        await self.coordinator.config_entry.runtime_data.client.async_set_title(command)
        await self.coordinator.async_request_refresh()