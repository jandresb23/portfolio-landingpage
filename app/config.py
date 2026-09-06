import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")

    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
    GITHUB_USERNAME: str = os.getenv("GITHUB_USERNAME", "")

    YOUTUBE_API_KEY: str = os.getenv("YOUTUBE_API_KEY", "")
    YOUTUBE_PLAYLIST_ID: str = os.getenv("YOUTUBE_PLAYLIST_ID", "")

    # FIX SEGURIDAD: ya no hay valor por defecto ("secret-token").
    # Si no se configura, el endpoint /sync se deshabilita explícitamente
    # (ver app/routers/api.py) en lugar de quedar protegido por un
    # token público y adivinable.
    SYNC_SECRET_KEY: str = os.getenv("SYNC_SECRET_KEY", "")

    # FIX SEGURIDAD: orígenes permitidos para CORS. Por defecto "*" (modo
    # desarrollo, sin credenciales). En producción, definir como lista
    # separada por comas, p. ej.:
    #   ALLOWED_ORIGINS=https://cursal.dev,https://www.cursal.dev
    ALLOWED_ORIGINS: str = os.getenv("ALLOWED_ORIGINS", "*")


settings = Settings()
