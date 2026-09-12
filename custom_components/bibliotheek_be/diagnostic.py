"""Shared account diagnostics."""

from homeassistant.const import CONF_USERNAME, EntityCategory
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import NAME


class AccountDiagnosticEntity(CoordinatorEntity):
    """Keep refresh diagnostics visible when a portal request fails."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, config_entry, key):
        super().__init__(coordinator)
        self._attr_unique_id = f"{config_entry.entry_id}_{key}"
        device_name = f"{NAME} {config_entry.data[CONF_USERNAME]}"
        self._attr_device_info = DeviceInfo(
            identifiers={(NAME, device_name)}, name=device_name, manufacturer=NAME
        )

    @property
    def available(self):
        """Report failures as status rather than becoming unavailable."""
        return True
