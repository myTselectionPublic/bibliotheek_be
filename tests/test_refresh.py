"""Test refresh actions and retained data using the real coordinator."""

from datetime import timedelta
from unittest.mock import AsyncMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.bibliotheek_be import async_setup_entry, register_services
from custom_components.bibliotheek_be.binary_sensor import ConnectionStatusSensor
from custom_components.bibliotheek_be.button import RefreshAllAccountsButton, RefreshDataButton
from custom_components.bibliotheek_be.const import DOMAIN, CONF_REFRESH_INTERVAL
from custom_components.bibliotheek_be.coordinator import MyDataUpdateCoordinator
from custom_components.bibliotheek_be.sensor import LastSuccessfulRefreshSensor, RetainedDataSensor


def make_entry(**kwargs):
    return MockConfigEntry(domain=DOMAIN, data={"username": "test-user", "password": "test-password"}, **kwargs)


async def test_update_action_refreshes_current_accounts(hass):
    """The legacy action needs no warning entity and includes later accounts."""
    first, second = AsyncMock(), AsyncMock()
    entry = make_entry()
    hass.data[DOMAIN] = {entry.entry_id: {"coordinator": first}, "reloading": True}
    register_services(hass, entry)
    hass.data[DOMAIN]["second"] = {"coordinator": second}
    await hass.services.async_call(DOMAIN, "update", {}, blocking=True)
    first.async_request_refresh.assert_awaited_once()
    second.async_request_refresh.assert_awaited_once()
    hass.data[DOMAIN].pop(entry.entry_id)
    await hass.services.async_call(DOMAIN, "update", {}, blocking=True)
    assert first.async_request_refresh.await_count == 1
    assert second.async_request_refresh.await_count == 2


async def test_refresh_buttons(hass):
    first, second = AsyncMock(), AsyncMock()
    entry = make_entry()
    hass.data[DOMAIN] = {"first": {"coordinator": first}, "second": {"coordinator": second}}
    await RefreshDataButton(first, entry).async_press()
    first.async_request_refresh.assert_awaited_once()
    second.async_request_refresh.assert_not_awaited()
    button = RefreshAllAccountsButton(first, entry)
    button.hass = hass
    await button.async_press()
    assert first.async_request_refresh.await_count == 2
    second.async_request_refresh.assert_awaited_once()


@pytest.mark.parametrize("options, expected", [({}, 30), ({CONF_REFRESH_INTERVAL: 12}, 12)])
async def test_setup_interval(hass, options, expected):
    entry = make_entry(options=options)
    entry.add_to_hass(hass)
    with (
        patch("custom_components.bibliotheek_be.MyDataUpdateCoordinator") as coordinator,
        patch.object(hass.config_entries, "async_forward_entry_setups", new=AsyncMock()),
    ):
        coordinator.return_value.async_config_entry_first_refresh = AsyncMock()
        assert await async_setup_entry(hass, entry)
        assert coordinator.call_args.args[2] == expected


async def test_failed_refresh_retains_data_and_recovers(hass):
    entry = make_entry()
    entry.add_to_hass(hass)
    session = AsyncMock()
    session.login.return_value = {"userdetails": {}, "loandetails": [], "reservationdetails": []}
    session.user_lists.return_value = {"list-1": {"name": "Reading list", "num_items": 2}}
    with patch("custom_components.bibliotheek_be.coordinator.ComponentSession", return_value=session):
        coordinator = MyDataUpdateCoordinator(hass, entry, 12)
    assert coordinator.update_interval == timedelta(minutes=12)
    status = ConnectionStatusSensor(coordinator, entry)
    timestamp = LastSuccessfulRefreshSensor(coordinator, entry)
    sensor = RetainedDataSensor(coordinator)
    assert not sensor.available
    await coordinator.async_refresh()
    snapshot = coordinator.data
    successful_at = timestamp.native_value
    assert successful_at.tzinfo is not None
    assert status.is_on and sensor.available
    session.login.side_effect = RuntimeError("Portal offline")
    await coordinator.async_refresh()
    assert coordinator.data is snapshot
    assert coordinator.data["userLists"]["list-1"]["num_items"] == 2
    assert timestamp.native_value == successful_at
    assert timestamp.available and status.available and sensor.available
    assert not status.is_on
    # The session may mutate its own cached objects before a later step fails.
    session.login.side_effect = None
    session.user_lists.return_value["list-1"]["num_items"] = 99
    session.user_lists.side_effect = RuntimeError("Lists unavailable")
    await coordinator.async_refresh()
    assert coordinator.data is snapshot
    assert coordinator.data["userLists"]["list-1"]["num_items"] == 2
    assert timestamp.native_value == successful_at
    assert not status.is_on
    session.login.side_effect = None
    session.user_lists.side_effect = None
    session.user_lists.return_value = {}
    await coordinator.async_refresh()
    assert status.is_on
    assert coordinator.data["userLists"] == {}
    assert timestamp.native_value >= successful_at
