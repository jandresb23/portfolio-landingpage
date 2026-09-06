import httpx
import pytest
import respx

from app.services.youtube_service import YouTubeProvider
from app.config import settings


@pytest.mark.asyncio
@respx.mock
async def test_fetch_playlist_videos_prefers_high_thumbnail(monkeypatch):
    monkeypatch.setattr(settings, "YOUTUBE_PLAYLIST_ID", "PL123")
    monkeypatch.setattr(settings, "YOUTUBE_API_KEY", "key123")

    respx.get("https://www.googleapis.com/youtube/v3/playlistItems").mock(
        return_value=httpx.Response(
            200,
            json={
                "items": [
                    {
                        "snippet": {
                            "resourceId": {"videoId": "vid1"},
                            "title": "Video de prueba",
                            "publishedAt": "2026-01-01T00:00:00Z",
                            "thumbnails": {
                                "default": {"url": "https://img/default.jpg"},
                                "medium": {"url": "https://img/medium.jpg"},
                                "high": {"url": "https://img/high.jpg"},
                            },
                        }
                    }
                ]
            },
        )
    )

    videos = await YouTubeProvider().fetch_playlist_videos()

    assert videos[0]["video_id"] == "vid1"
    assert videos[0]["thumbnail_url"] == "https://img/high.jpg"


@pytest.mark.asyncio
@respx.mock
async def test_fetch_playlist_videos_falls_back_to_default_thumbnail(monkeypatch):
    monkeypatch.setattr(settings, "YOUTUBE_PLAYLIST_ID", "PL123")
    monkeypatch.setattr(settings, "YOUTUBE_API_KEY", "key123")

    respx.get("https://www.googleapis.com/youtube/v3/playlistItems").mock(
        return_value=httpx.Response(
            200,
            json={
                "items": [
                    {
                        "snippet": {
                            "resourceId": {"videoId": "vid2"},
                            "title": "Sin thumbnails grandes",
                            "publishedAt": "2026-01-01T00:00:00Z",
                            "thumbnails": {"default": {"url": "https://img/default.jpg"}},
                        }
                    }
                ]
            },
        )
    )

    videos = await YouTubeProvider().fetch_playlist_videos()
    assert videos[0]["thumbnail_url"] == "https://img/default.jpg"


@pytest.mark.asyncio
@respx.mock
async def test_fetch_playlist_videos_raises_on_error_status(monkeypatch):
    monkeypatch.setattr(settings, "YOUTUBE_PLAYLIST_ID", "PL123")
    monkeypatch.setattr(settings, "YOUTUBE_API_KEY", "key123")

    respx.get("https://www.googleapis.com/youtube/v3/playlistItems").mock(
        return_value=httpx.Response(400, text="invalid playlist id")
    )

    with pytest.raises(Exception):
        await YouTubeProvider().fetch_playlist_videos()
