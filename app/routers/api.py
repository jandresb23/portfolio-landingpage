import logging
import secrets

from fastapi import APIRouter, Depends, HTTPException, Header
from supabase import Client

from app.database import get_db
from app.repositories.cache_repository import CacheRepository
from app.services.github_service import GitHubProvider
from app.services.youtube_service import YouTubeProvider
from app.config import settings

logger = logging.getLogger("cursal.api")

router = APIRouter(prefix="/api/v1", tags=["API Portfolio cursal"])


@router.get("/projects")
async def get_projects(db: Client = Depends(get_db)):
    repo = CacheRepository(db)
    projects = await repo.get_projects()
    return {"status": "success", "data": projects}


@router.get("/videos")
async def get_videos(db: Client = Depends(get_db)):
    repo = CacheRepository(db)
    videos = await repo.get_videos()
    return {"status": "success", "data": videos}


@router.post("/sync")
async def sync_cache(authorization: str = Header(None), db: Client = Depends(get_db)):
    # FIX SEGURIDAD: si no se configuró SYNC_SECRET_KEY, el endpoint queda
    # deshabilitado en vez de aceptar el valor por defecto público
    # "secret-token" que tenía antes.
    if not settings.SYNC_SECRET_KEY:
        raise HTTPException(
            status_code=503,
            detail="El endpoint de sincronización no está configurado (falta SYNC_SECRET_KEY)."
        )

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization.split(" ", 1)[1]

    # FIX SEGURIDAD: comparación en tiempo constante para evitar timing attacks.
    if not secrets.compare_digest(token, settings.SYNC_SECRET_KEY):
        raise HTTPException(status_code=403, detail="Unauthorized synchronization key")

    try:
        github_provider = GitHubProvider()
        repos = await github_provider.fetch_user_repositories()
        cache_repo = CacheRepository(db)
        await cache_repo.save_projects(repos)

        youtube_provider = YouTubeProvider()
        videos = await youtube_provider.fetch_playlist_videos()
        await cache_repo.save_videos(videos)

        return {"status": "success", "message": "Cache synchronized successfully with GitHub and YouTube."}
    except Exception as e:
        # FIX SEGURIDAD: ya no se devuelve str(e) al cliente (podía filtrar
        # detalles internos); el error completo se registra en el log del
        # servidor y se responde con un mensaje genérico.
        logger.exception("Error synchronizing cache")
        raise HTTPException(
            status_code=502,
            detail="No se pudo sincronizar el caché con un proveedor externo (GitHub/YouTube)."
        ) from e
