import httpx
import pytest
import respx

from app.services.github_service import GitHubProvider
from app.config import settings


@pytest.mark.asyncio
@respx.mock
async def test_fetch_user_repositories_formats_response(monkeypatch):
    monkeypatch.setattr(settings, "GITHUB_USERNAME", "octocat")
    monkeypatch.setattr(settings, "GITHUB_TOKEN", "")

    respx.get("https://api.github.com/users/octocat/repos").mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "name": "repo1",
                    "description": None,
                    "html_url": "https://github.com/octocat/repo1",
                    "language": None,
                    "updated_at": "2026-01-01T00:00:00Z",
                }
            ],
        )
    )

    repos = await GitHubProvider().fetch_user_repositories()

    assert repos[0]["repo_name"] == "repo1"
    # Valores por defecto cuando GitHub no provee descripción/lenguaje.
    assert repos[0]["description"] == "Sin descripción disponible."
    assert repos[0]["language"] == "General"


@pytest.mark.asyncio
@respx.mock
async def test_fetch_user_repositories_sends_auth_header_when_token_set(monkeypatch):
    monkeypatch.setattr(settings, "GITHUB_USERNAME", "octocat")
    monkeypatch.setattr(settings, "GITHUB_TOKEN", "ghp_test123")

    route = respx.get("https://api.github.com/users/octocat/repos").mock(
        return_value=httpx.Response(200, json=[])
    )

    await GitHubProvider().fetch_user_repositories()

    sent_request = route.calls.last.request
    assert sent_request.headers["Authorization"] == "Bearer ghp_test123"


@pytest.mark.asyncio
@respx.mock
async def test_fetch_user_repositories_raises_on_error_status(monkeypatch):
    monkeypatch.setattr(settings, "GITHUB_USERNAME", "octocat")

    respx.get("https://api.github.com/users/octocat/repos").mock(
        return_value=httpx.Response(403, text="rate limit exceeded")
    )

    with pytest.raises(Exception):
        await GitHubProvider().fetch_user_repositories()
