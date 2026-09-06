import httpx
from app.config import settings

# FIX ROBUSTEZ: sin timeout, una llamada colgada a YouTube bloquearía el
# endpoint /sync indefinidamente.
REQUEST_TIMEOUT = httpx.Timeout(10.0, connect=5.0)


class YouTubeProvider:
    BASE_URL = "https://www.googleapis.com/youtube/v3/playlistItems"

    async def fetch_playlist_videos(self) -> list:
        params = {
            "part": "snippet",
            "playlistId": settings.YOUTUBE_PLAYLIST_ID,
            "key": settings.YOUTUBE_API_KEY,
            "maxResults": 10
        }

        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.get(self.BASE_URL, params=params)
            if response.status_code != 200:
                raise Exception(f"Error fetching YouTube playlist: {response.text}")

            data = response.json()
            items = data.get("items", [])
            formatted_videos = []
            for item in items:
                snippet = item.get("snippet", {})
                thumbnails = snippet.get("thumbnails", {})
                high_thumbnail = thumbnails.get("high", thumbnails.get("medium", thumbnails.get("default", {})))

                formatted_videos.append({
                    "video_id": snippet.get("resourceId", {}).get("videoId"),
                    "title": snippet.get("title"),
                    "thumbnail_url": high_thumbnail.get("url"),
                    "published_at": snippet.get("publishedAt")
                })
            return formatted_videos
