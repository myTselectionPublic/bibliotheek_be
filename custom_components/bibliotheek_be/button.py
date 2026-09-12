"""Buttons for refreshing Bibliotheek.be portal data."""

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, NAME
from .coordinator import MyDataUpdateCoordinator
from .refresh import async_refresh_all_accounts


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up account and integration-wide refresh buttons."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    async_add_entities(
        [
            RefreshDataButton(coordinator, config_entry),
            RefreshAllAccountsButton(coordinator, config_entry),
        ]
    )


class RefreshDataButton(ButtonEntity):
    """Request fresh portal data for all sensors belonging to an account."""

    _attr_has_entity_name = True
    _attr_name = "Refresh data"
    _attr_icon = "mdi:refresh"

    def __init__(
        self, coordinator: MyDataUpdateCoordinator, config_entry: ConfigEntry
    ) -> None:
        """Attach the button to the account's existing device."""
        self._coordinator = coordinator
        self._attr_unique_id = f"{config_entry.entry_id}_refresh_data"
        device_name = f"{NAME} {config_entry.data[CONF_USERNAME]}"
        self._attr_device_info = DeviceInfo(
            identifiers={(NAME, device_name)},
            name=device_name,
            manufacturer=NAME,
        )

    async def async_press(self) -> None:
        """Fetch portal data without waiting for the scheduled update."""
        await self._coordinator.async_request_refresh()


class RefreshAllAccountsButton(RefreshDataButton):
    """Refresh every loaded account from any account's device."""

    _attr_name = "Refresh all accounts"

    def __init__(
        self, coordinator: MyDataUpdateCoordinator, config_entry: ConfigEntry
    ) -> None:
        """Attach the global refresh action to this account's device."""
        super().__init__(coordinator, config_entry)
        self._attr_unique_id = f"{config_entry.entry_id}_refresh_all_accounts"

    async def async_press(self) -> None:
        """Request fresh data from all currently loaded account coordinators."""
        await async_refresh_all_accounts(self.hass)
