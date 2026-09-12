"""Test refresh interval options without contacting Bibliotheek.be."""

from unittest.mock import AsyncMock, patch

import pytest
import voluptuous as vol
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.bibliotheek_be.const import DOMAIN, CONF_REFRESH_INTERVAL


async def test_interval_options(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"username": "test-user", "password": "test-password", "opening_hours_libraries": {"gent": {"id": "main"}}},
        options={"other_option": True},
    )
    entry.add_to_hass(hass)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    schema = result["data_schema"]
    assert schema({})[CONF_REFRESH_INTERVAL] == 30
    for invalid in (0, -1, "invalid"):
        with pytest.raises(vol.Invalid):
            schema({CONF_REFRESH_INTERVAL: invalid})
    with patch.object(hass.config_entries, "async_reload", new=AsyncMock()):
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], user_input={CONF_REFRESH_INTERVAL: 10}
        )
    assert result["data"] == {"other_option": True, CONF_REFRESH_INTERVAL: 10}
    assert entry.data["opening_hours_libraries"] == {"gent": {"id": "main"}}
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["data_schema"]({})[CONF_REFRESH_INTERVAL] == 10
