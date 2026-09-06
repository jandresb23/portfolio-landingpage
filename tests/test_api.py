import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db


@pytest.fixture
def client(fake_db):
    app.dependency_overrides[get_db] = lambda: fake_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# --- Endpoints de lectura --------------------------------------------------

def test_root_ok(client):
    res = client.get("/")
    assert res.status_code == 200
    assert res.json()["brand"] == "cursal"


def test_get_projects_returns_cached_data(client):
    """REQ-F-01, REQ-F-03"""
    res = client.get("/api/v1/projects")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "success"
    assert body["data"][0]["repo_name"] == "cursal-api"
    for key in ("repo_name", "description", "html_url", "language", "updated_at"):
        assert key in body["data"][0]


def test_get_videos_returns_cached_data(client):
    """REQ-F-04, REQ-F-05"""
    res = client.get("/api/v1/videos")
    assert res.status_code == 200
    body = res.json()
    assert body["data"][0]["video_id"] == "abc123"
    for key in ("video_id", "title", "thumbnail_url", "published_at"):
        assert key in body["data"][0]


def test_get_projects_with_empty_cache_returns_empty_list(fake_db):
    """REQ-F-02"""
    fake_db._table_data["github_cache"] = []
    app.dependency_overrides[get_db] = lambda: fake_db
    with TestClient(app) as c:
        res = c.get("/api/v1/projects")
    app.dependency_overrides.clear()
    assert res.status_code == 200
    assert res.json() == {"status": "success", "data": []}


# --- Endpoint de sincronización ---------------------------------------------

def test_sync_without_secret_configured_returns_503(client, monkeypatch):
    """REQ-F-09 / REQ-NF-01: sin SYNC_SECRET_KEY, el endpoint se deshabilita."""
    monkeypatch.setattr("app.config.settings.SYNC_SECRET_KEY", "")
    res = client.post("/api/v1/sync", headers={"Authorization": "Bearer cualquier-cosa"})
    assert res.status_code == 503


def test_sync_missing_auth_header_returns_401(client, monkeypatch):
    """REQ-F-07"""
    monkeypatch.setattr("app.config.settings.SYNC_SECRET_KEY", "top-secret")
    res = client.post("/api/v1/sync")
    assert res.status_code == 401


def test_sync_malformed_auth_header_returns_401(client, monkeypatch):
    """REQ-F-07"""
    monkeypatch.setattr("app.config.settings.SYNC_SECRET_KEY", "top-secret")
    res = client.post("/api/v1/sync", headers={"Authorization": "top-secret"})
    assert res.status_code == 401


def test_sync_wrong_token_returns_403(client, monkeypatch):
    """REQ-F-08"""
    monkeypatch.setattr("app.config.settings.SYNC_SECRET_KEY", "top-secret")
    res = client.post("/api/v1/sync", headers={"Authorization": "Bearer incorrecto"})
    assert res.status_code == 403


def test_sync_success_upserts_projects_and_videos(client, monkeypatch):
    """REQ-F-06, REQ-F-11: éxito extremo a extremo con proveedores mockeados."""
    monkeypatch.setattr("app.config.settings.SYNC_SECRET_KEY", "top-secret")

    async def fake_fetch_repos(self):
        return [{
            "repo_name": "x", "description": "d",
            "html_url": "u", "language": "Python", "updated_at": "now",
        }]

    async def fake_fetch_videos(self):
        return [{
            "video_id": "v1", "title": "t",
            "thumbnail_url": "u", "published_at": "now",
        }]

    monkeypatch.setattr(
        "app.routers.api.GitHubProvider.fetch_user_repositories", fake_fetch_repos
    )
    monkeypatch.setattr(
        "app.routers.api.YouTubeProvider.fetch_playlist_videos", fake_fetch_videos
    )

    res = client.post("/api/v1/sync", headers={"Authorization": "Bearer top-secret"})
    assert res.status_code == 200
    assert res.json()["status"] == "success"


def test_sync_upstream_failure_returns_502_and_does_not_leak_details(client, monkeypatch):
    """REQ-F-10, REQ-NF-06: un fallo de GitHub/YouTube no debe filtrar
    detalles internos en la respuesta al cliente."""
    monkeypatch.setattr("app.config.settings.SYNC_SECRET_KEY", "top-secret")

    async def fake_fetch_repos_raises(self):
        raise Exception("detalle-interno-sensible-XYZ")

    monkeypatch.setattr(
        "app.routers.api.GitHubProvider.fetch_user_repositories", fake_fetch_repos_raises
    )

    res = client.post("/api/v1/sync", headers={"Authorization": "Bearer top-secret"})
    assert res.status_code == 502
    assert "detalle-interno-sensible-XYZ" not in res.text
