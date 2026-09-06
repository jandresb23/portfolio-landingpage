import pytest

from app.repositories.cache_repository import CacheRepository


@pytest.mark.asyncio
async def test_save_projects_makes_a_single_batched_call(fake_db):
    repo = CacheRepository(fake_db)
    repos = [{"repo_name": "a"}, {"repo_name": "b"}, {"repo_name": "c"}]

    await repo.save_projects(repos)

    # REQ-NF-05: con upsert en lote, table("github_cache") debe invocarse
    # UNA sola vez, sin importar cuántos repos se sincronicen.
    assert fake_db.calls.count("github_cache") == 1


@pytest.mark.asyncio
async def test_save_videos_makes_a_single_batched_call(fake_db):
    repo = CacheRepository(fake_db)
    videos = [{"video_id": "v1"}, {"video_id": "v2"}]

    await repo.save_videos(videos)

    assert fake_db.calls.count("youtube_cache") == 1


@pytest.mark.asyncio
async def test_save_projects_is_noop_on_empty_list(fake_db):
    repo = CacheRepository(fake_db)
    await repo.save_projects([])
    assert "github_cache" not in fake_db.calls


@pytest.mark.asyncio
async def test_get_projects_returns_data_from_fake_db(fake_db):
    repo = CacheRepository(fake_db)
    result = await repo.get_projects()
    assert result[0]["repo_name"] == "cursal-api"
