from unittest.mock import MagicMock

import pytest


class FakeQuery:
    """Doble de prueba para el objeto encadenable que devuelve
    supabase_client.table('x'). Soporta select().order().execute() y
    upsert().execute() sin tocar una base de datos real."""

    def __init__(self, data):
        self._data = data

    def select(self, *_, **__):
        return self

    def order(self, *_, **__):
        return self

    def upsert(self, *_args, **_kwargs):
        return self

    def execute(self):
        result = MagicMock()
        result.data = self._data
        return result


class FakeSupabaseClient:
    """Doble de prueba de supabase.Client. Registra cada tabla solicitada
    en self.calls para poder verificar CUÁNTAS veces se llamó table(),
    lo cual es clave para probar que el upsert se hace en lote y no en
    un loop (REQ-NF-05)."""

    def __init__(self, table_data=None):
        self._table_data = table_data or {}
        self.calls = []

    def table(self, name):
        self.calls.append(name)
        return FakeQuery(self._table_data.get(name, []))


@pytest.fixture
def fake_db():
    return FakeSupabaseClient(table_data={
        "github_cache": [
            {
                "repo_name": "cursal-api",
                "description": "Backend de cursal",
                "html_url": "https://github.com/x/cursal-api",
                "language": "Python",
                "updated_at": "2026-01-01T00:00:00Z",
            },
        ],
        "youtube_cache": [
            {
                "video_id": "abc123",
                "title": "Demo cursal",
                "thumbnail_url": "https://img.example/abc123.jpg",
                "published_at": "2026-01-01T00:00:00Z",
            },
        ],
    })
