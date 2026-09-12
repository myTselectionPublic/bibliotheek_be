"""Exercise portal parsing with HTTP responses, without real credentials."""

from unittest.mock import patch

import httpx
import pytest

from custom_components.bibliotheek_be.utils import ComponentSession


async def test_login_existing_session(hass):
    """Read memberships, activities, loans and reservations over mocked HTTP."""
    account = {
        "id": "account-1", "hasError": False, "barcode": "123456",
        "name": "Test Reader", "library": "https://gent.bibliotheek.be",
        "libraryName": "Gent",
    }
    responses = {
        "/mijn-bibliotheek/aanmelden": {},
        "/mijn-bibliotheek/lidmaatschappen": {},
        "/api/my-library/memberships": {"gent": {"library": [account]}},
        "/api/my-library/account-1/activities": {"numberOfLoans": 1},
        "/my-library-overview-loans": [{"itemId": "book-1", "title": "Test Book"}],
        "/my-library-overview-reservations": [],
    }
    requested = []

    def respond(request):
        requested.append(request.url.path)
        return httpx.Response(200, json=responses[request.url.path])

    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
        with patch("custom_components.bibliotheek_be.utils.get_async_client", return_value=client):
            result = await ComponentSession(hass).login("test-user", "test-password")

    assert set(requested) == set(responses)
    assert result["userdetails"]["account-1"]["loans"]["loans"] == 1
    assert result["loandetails"][0]["itemId"] == "book-1"
    assert result["reservationdetails"] == []
    assert result["librarydetails"] == {"gent": "https://gent.bibliotheek.be"}


@pytest.mark.parametrize("status", [401, 500])
async def test_login_http_failure(hass, status):
    """Reject failed responses before trying to parse account data."""
    transport = httpx.MockTransport(lambda request: httpx.Response(status))
    async with httpx.AsyncClient(transport=transport) as client:
        with patch("custom_components.bibliotheek_be.utils.get_async_client", return_value=client):
            with pytest.raises(RuntimeError, match=f"login start: {status}"):
                await ComponentSession(hass).login("test-user", "test-password")
