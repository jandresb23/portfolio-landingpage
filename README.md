# cursal - Plataforma de Portafolio Interactivo

Plataforma profesional para la marca **cursal**, orientada a exhibir proyectos de desarrollo de software, automatización (RPA), inteligencia artificial y demostraciones multimedia en video, optimizada mediante un backend en Python y persistencia en Supabase.

> 📄 Este proyecto sigue **Specification Driven Development (SDD)**. La
> especificación completa vive en [`specs/`](./specs):
> - [`specs/requirements.md`](./specs/requirements.md) — requisitos funcionales y no funcionales (formato EARS).
> - [`specs/design.md`](./specs/design.md) — arquitectura, modelo de datos y contratos de API.
> - [`specs/tasks.md`](./specs/tasks.md) — plan de implementación y trazabilidad a requisitos.

## Arquitectura y Componentes

* **Backend:** FastAPI (Python) con arquitectura en capas (routers → repositories/services → database).
* **Base de Datos & Caché:** Supabase (PostgreSQL).
* **Frontend:** HTML5, Tailwind CSS y Vanilla JS (`frontend/index.html`).
* **Integraciones:** GitHub REST API y YouTube Data API v3.

```
app/
├── main.py                    # App FastAPI + CORS
├── config.py                  # Variables de entorno (única fuente de verdad)
├── database.py                # Cliente Supabase (singleton)
├── routers/
│   └── api.py                 # Endpoints /projects, /videos, /sync
├── repositories/
│   └── cache_repository.py    # Acceso a las tablas de caché en Supabase
└── services/
    ├── github_service.py      # Adaptador de la API de GitHub
    └── youtube_service.py     # Adaptador de la API de YouTube
frontend/
├── index.html                  # Portafolio estático
└── assets/
    ├── logo_minimal_v1.png      # Isotipo (fondo transparente) — header y favicon
    └── cursal_logo.jpg          # Logo completo con wordmark — sección Hero
specs/
├── requirements.md
├── design.md
└── tasks.md
```

## Variables de entorno

Copia `_env.example` a `.env` y completa los valores:

| Variable | Obligatoria | Descripción |
|---|---|---|
| `SUPABASE_URL` | Sí | URL del proyecto de Supabase. |
| `SUPABASE_KEY` | Sí | Service role o anon key de Supabase. |
| `GITHUB_TOKEN` | No* | Personal access token de GitHub (recomendado para evitar rate limits bajos). |
| `GITHUB_USERNAME` | Sí | Usuario de GitHub del cual leer repositorios. |
| `YOUTUBE_API_KEY` | Sí | API key de Google con YouTube Data API v3 habilitada. |
| `YOUTUBE_PLAYLIST_ID` | Sí | ID de la playlist a sincronizar. |
| `SYNC_SECRET_KEY` | Sí (para usar `/sync`) | Token bearer para autorizar `POST /api/v1/sync`. **Sin valor por defecto**: si no se define, el endpoint responde `503`. Genera uno con: `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `ALLOWED_ORIGINS` | No | Orígenes permitidos para CORS, separados por comas. Por defecto `*` (sin credenciales). En producción, usar el dominio real del frontend. |

## Despliegue en Render (backend)

1. Conecta tu repositorio de GitHub a Render como un **Web Service**.
2. Configura el entorno de Python: `pip install -r requirements.txt`.
3. Comando de inicio: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
4. Configura todas las variables de entorno de la tabla anterior en el panel de Render.
5. Verifica que existan constraints `UNIQUE` en Supabase sobre
   `github_cache.repo_name` y `youtube_cache.video_id` (necesario para que
   el `upsert` con `on_conflict` funcione).

## Despliegue del frontend

`frontend/index.html` es un archivo estático sin build step, e incluye la
carpeta `frontend/assets/` con el logo del sitio (isotipo en el header y
favicon, logo completo en la sección Hero) — asegúrate de subir esa carpeta
junto con el HTML al hosting que elijas. Puede alojarse
en Render Static Site, Vercel, Netlify o GitHub Pages. Antes de publicar,
actualiza la constante `API_BASE` dentro del `<script>` con la URL real de
tu backend en Render:

```js
const API_BASE = "https://tu-backend.onrender.com/api/v1";
```

## Sincronizar el caché

No hay panel de administración; la sincronización se dispara con una
petición HTTP autenticada, por ejemplo:

```bash
curl -X POST https://tu-backend.onrender.com/api/v1/sync \
  -H "Authorization: Bearer $SYNC_SECRET_KEY"
```

Se recomienda automatizar esta llamada con un cron externo (GitHub Actions
scheduled workflow, cron-job.org, etc.) con la frecuencia deseada.

## Pruebas

Instala las dependencias de desarrollo y ejecuta la suite con `pytest`:

```bash
pip install -r requirements-dev.txt
pytest -v
```

La suite (`tests/`) cubre, sin depender de una red real ni de Supabase:

- **`test_api.py`** — endpoints `/projects`, `/videos` y todos los casos de
  `/sync` (sin header, token inválido, secreto no configurado, éxito, fallo
  upstream sin fuga de detalles).
- **`test_cache_repository.py`** — confirma que el upsert de caché se hace
  en lote (una sola llamada), no en un loop.
- **`test_github_service.py`** / **`test_youtube_service.py`** — adaptadores
  externos con `httpx` mockeado vía `respx` (formato de respuesta, header de
  autorización, manejo de errores).

Ver `specs/tasks.md` para la matriz de trazabilidad entre estos tests y los
requisitos (`specs/requirements.md`).

## Seguridad

- `/sync` requiere `SYNC_SECRET_KEY`; sin esa variable configurada, el
  endpoint queda deshabilitado (`503`) en vez de aceptar un secreto por
  defecto.
- La comparación del token se hace en tiempo constante
  (`secrets.compare_digest`).
- CORS solo habilita `allow_credentials` cuando se configuran orígenes
  explícitos en `ALLOWED_ORIGINS` (nunca junto con `*`).
- Ninguna API key ni token se expone al frontend; todas las llamadas a
  GitHub/YouTube ocurren server-side.
- Los errores de sincronización se registran en los logs del servidor; la
  respuesta al cliente es siempre un mensaje genérico.

## Validación end-to-end

Este proyecto fue validado de punta a punta (backend real contra Supabase,
GitHub y YouTube, más frontend en el navegador) — ver el detalle completo,
incluyendo las incidencias de configuración encontradas y su solución, en
`specs/tasks.md` → "Fase 4 — Validación end-to-end manual".

## Changelog reciente

- **Fix crítico:** corregido `SyntaxError` en `app/database.py` que impedía
  el arranque de la aplicación.
- **Seguridad:** eliminado el valor por defecto del secreto de
  sincronización; corregida la configuración de CORS; comparación de
  tokens en tiempo constante; respuestas de error sin detalles internos.
- **Robustez:** timeouts explícitos en las llamadas a GitHub y YouTube.
- **Rendimiento:** upserts en lote en lugar de un round-trip por registro.
- **Frontend:** manejo visible de errores de carga; cierre del modal con
  `Escape`.
- **Documentación:** especificación completa en `specs/` siguiendo SDD.
- **Higiene de repositorio:** agregado `.gitignore` para excluir `.env`,
  entornos virtuales, caché de Python/pytest y archivos de editor/SO.
- **Validación:** suite completa (backend + frontend) verificada en un
  entorno real; ver `specs/tasks.md` para el detalle y las incidencias de
  configuración resueltas (tablas de Supabase, permisos de `service_role`,
  token de GitHub, embed de YouTube).
- **Branding:** logo de Cursal insertado en el frontend (isotipo en el
  header/favicon, logo completo en el Hero); imágenes optimizadas de
  ~1 MB cada una a ~30-70 KB.
