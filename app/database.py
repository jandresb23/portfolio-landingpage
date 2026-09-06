from supabase import create_client, Client
from app.config import settings


class SupabaseClient:
    _instance: Client = None

    @classmethod
    def get_client(cls) -> Client:
        # FIX BUG CRÍTICO: faltaba la palabra clave "def" antes de
        # get_client, lo cual provocaba un SyntaxError al importar el
        # módulo e impedía que la aplicación arrancara.
        if cls._instance is None:
            if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
                raise ValueError("Supabase URL and Key must be provided in environment variables.")
            cls._instance = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        return cls._instance


def get_db() -> Client:
    return SupabaseClient.get_client()
