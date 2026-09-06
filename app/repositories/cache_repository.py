from supabase import Client


class CacheRepository:
    def __init__(self, db: Client):
        self.db = db

    async def get_projects(self) -> list:
        response = self.db.table("github_cache").select("*").order("updated_at", desc=True).execute()
        return response.data

    async def get_videos(self) -> list:
        response = self.db.table("youtube_cache").select("*").order("published_at", desc=True).execute()
        return response.data

    async def save_projects(self, repos: list):
        # FIX PERFORMANCE: antes se hacía un execute() por cada repo dentro
        # de un for. Ahora se envía la lista completa en un solo upsert.
        if not repos:
            return
        self.db.table("github_cache").upsert(repos, on_conflict="repo_name").execute()

    async def save_videos(self, videos: list):
        if not videos:
            return
        self.db.table("youtube_cache").upsert(videos, on_conflict="video_id").execute()
