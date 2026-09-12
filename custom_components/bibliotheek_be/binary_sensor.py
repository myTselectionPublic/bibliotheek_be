"""Portal connection diagnostics."""

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity

from .const import DOMAIN
from .diagnostic import AccountDiagnosticEntity


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up connection status for this account."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    async_add_entities([ConnectionStatusSensor(coordinator, config_entry)])


class ConnectionStatusSensor(AccountDiagnosticEntity, BinarySensorEntity):
    """Show whether the latest portal refresh succeeded."""

    _attr_name = "Connection status"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, coordinator, config_entry):
        super().__init__(coordinator, config_entry, "connection_status")

    @property
    def is_on(self):
        return self.coordinator.last_update_success
