"""Shared refresh actions."""

import asyncio

from homeassistant.core import HomeAssistant

from .const import DOMAIN


async def async_refresh_all_accounts(hass: HomeAssistant) -> None:
    """Request fresh data from a snapshot of all loaded accounts."""
    coordinators = [
        entry_data["coordinator"]
        for entry_data in hass.data.get(DOMAIN, {}).values()
        if isinstance(entry_data, dict) and "coordinator" in entry_data
    ]
    await asyncio.gather(
        *(coordinator.async_request_refresh() for coordinator in coordinators)
    )
