from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import api
from app.config import settings

app = FastAPI(
    title="cursal API",
    description="Backend API for cursal interactive portfolio, managing GitHub and YouTube cache.",
    version="1.0.0"
)

# FIX SEGURIDAD: allow_origins=["*"] junto con allow_credentials=True es una
# combinación inválida según la especificación CORS (los navegadores la
# rechazan) y además expone la API a cualquier origen con credenciales.
# Ahora las credenciales solo se habilitan cuando se configuran orígenes
# concretos vía la variable de entorno ALLOWED_ORIGINS.
_origins_raw = settings.ALLOWED_ORIGINS
_wildcard = _origins_raw.strip() == "*"
_origins = ["*"] if _wildcard else [o.strip() for o in _origins_raw.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=not _wildcard,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(api.router)


@app.get("/")
def root():
    return {"brand": "cursal", "status": "active", "docs": "/docs"}
