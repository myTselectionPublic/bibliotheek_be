"""Shared fixtures for tests that never contact the real portal."""

import pytest


@pytest.fixture(autouse=True)
def enable_integration(enable_custom_integrations):
    """Allow Home Assistant to load this custom integration."""
