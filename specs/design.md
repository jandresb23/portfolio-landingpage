# Documento de Diseño — cursal

**Versión:** 1.1.0
**Deriva de:** `requirements.md`

## 1. Visión general de arquitectura

```
┌─────────────────┐      HTTPS       ┌──────────────────────┐
│  Frontend        │ ───────────────▶ │  FastAPI Backend      │
│  (index.html,    │ ◀─────────────── │  (Render / uvicorn)   │
│  Tailwind, JS)   │   JSON            │                       │
└─────────────────┘                   │  routers/api.py       │
                                       │      │                │
                                       │      ▼                │
                                       │  repositories/        │
                                       │  cache_repository.py  │
                                       │      │                │
                                       │      ▼                │
                                       │  database.py ─────────┼───▶ Supabase
                                       │                       │     (PostgreSQL)
                                       │  services/            │
                                       │   github_service.py ──┼───▶ GitHub REST API
                                       │   youtube_service.py ─┼───▶ YouTube Data API v3
                                       └──────────────────────┘
```

Patrón: **arquitectura en capas** con inyección de dependencias de FastAPI.

- **routers/**: define los endpoints HTTP, valida entrada (headers, auth) y
  delega a repositories/services. No contiene lógica de negocio.
- **repositories/**: encapsula el acceso a Supabase (lectura/escritura de
  caché). Es la única capa que conoce el esquema de las tablas.
- **services/**: adaptadores hacia APIs externas (GitHub, YouTube).
  Normalizan la respuesta externa al formato interno de caché.
- **database.py**: singleton perezoso del cliente de Supabase.
- **config.py**: única fuente de verdad para variables de entorno.

## 2. Modelo de datos (Supabase)

### Tabla `github_cache`

| Columna | Tipo | Notas |
|---|---|---|
| `repo_name` | text | **Clave de upsert** (`on_conflict`). Debe tener constraint `UNIQUE`. |
| `description` | text | Valor por defecto: "Sin descripción disponible." |
| `html_url` | text | URL pública del repo. |
| `language` | text | Valor por defecto: "General". |
| `updated_at` | timestamptz | Usado para el `order(desc=True)`. |

### Tabla `youtube_cache`

| Columna | Tipo | Notas |
|---|---|---|
| `video_id` | text | **Clave de upsert** (`on_conflict`). Debe tener constraint `UNIQUE`. |
| `title` | text | |
| `thumbnail_url` | text | Prioriza thumbnail `high` > `medium` > `default`. |
| `published_at` | timestamptz | Usado para el `order(desc=True)`. |

> Nota de diseño: ambas tablas requieren un índice único sobre la columna de
> `on_conflict` para que el upsert funcione correctamente en Supabase/Postgres.

## 3. Contratos de API

### `GET /api/v1/projects`
- **Respuesta 200:**
  ```json
  { "status": "success", "data": [ { "repo_name": "...", "description": "...", "html_url": "...", "language": "...", "updated_at": "..." } ] }
  ```

### `GET /api/v1/videos`
- **Respuesta 200:**
  ```json
  { "status": "success", "data": [ { "video_id": "...", "title": "...", "thumbnail_url": "...", "published_at": "..." } ] }
  ```

### `POST /api/v1/sync`
- **Header requerido:** `Authorization: Bearer <SYNC_SECRET_KEY>`
- **Respuestas:**
  | Código | Condición |
  |---|---|
  | 200 | Sincronización exitosa. |
  | 401 | Header ausente o mal formado. |
  | 403 | Token incorrecto. |
  | 502 | Fallo al contactar GitHub o YouTube. |
  | 503 | `SYNC_SECRET_KEY` no configurado en el servidor. |

## 4. Decisiones de diseño y su justificación

| Decisión | Justificación |
|---|---|
| Sin valor por defecto para `SYNC_SECRET_KEY` | Evita que un despliegue sin configurar quede protegido por un secreto público conocido (REQ-NF-01). |
| `secrets.compare_digest` para comparar tokens | Mitiga ataques de temporización sobre la comparación de strings (REQ-NF-02). |
| CORS condicionado a `ALLOWED_ORIGINS` | `allow_origins=["*"]` + `allow_credentials=True` es inválido en la spec CORS; se resuelve activando credenciales solo con orígenes explícitos (REQ-NF-03). |
| `httpx.Timeout(10.0, connect=5.0)` en servicios externos | Evita que una dependencia externa lenta bloquee `/sync` indefinidamente (REQ-NF-04). |
| Upsert en lote (`upsert(list)`) en vez de un `execute()` por elemento | Reduce de N round-trips a Supabase a 1 por sincronización (REQ-NF-05). |
| Logging con `logger.exception` + respuesta genérica 502 | Evita filtrar trazas/errores internos al cliente, manteniendo diagnóstico en el servidor (REQ-NF-06). |
| Singleton perezoso en `database.py` | Reutiliza la conexión de Supabase entre requests sin reinicializarla en cada llamada. |

## 5. Flujo de sincronización (secuencia)

1. Cliente autorizado llama `POST /api/v1/sync` con `Authorization: Bearer <token>`.
2. `api.py` valida que `SYNC_SECRET_KEY` esté configurado → si no, `503`.
3. Valida formato del header → si no, `401`.
4. Compara token con `compare_digest` → si no coincide, `403`.
5. `GitHubProvider.fetch_user_repositories()` llama a la API de GitHub con
   timeout; normaliza los 6 repos más recientes.
6. `CacheRepository.save_projects()` hace upsert en lote en `github_cache`.
7. `YouTubeProvider.fetch_playlist_videos()` llama a la API de YouTube con
   timeout; normaliza hasta 10 videos.
8. `CacheRepository.save_videos()` hace upsert en lote en `youtube_cache`.
9. Si cualquier paso 5-8 lanza excepción, se loggea y se responde `502`.
10. Éxito → `200 {"status": "success", ...}`.

## 6. Seguridad (resumen)

- Autenticación de `/sync` vía bearer token estático comparado en tiempo
  constante; sin valor por defecto.
- CORS restringido a orígenes explícitos cuando se requieren credenciales.
- Ninguna clave (`GITHUB_TOKEN`, `YOUTUBE_API_KEY`, `SUPABASE_KEY`,
  `SYNC_SECRET_KEY`) se expone al frontend; todo el acceso a proveedores
  externos ocurre server-side.
- Los mensajes de error hacia el cliente son genéricos; el detalle técnico
  vive solo en logs del servidor.

## 7. Despliegue

- **Backend:** Render Web Service, `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
- **Variables de entorno:** ver `_env.example`.
- **Frontend:** archivo estático (`frontend/index.html`), puede servirse
  desde cualquier hosting estático (Render Static Site, Vercel, Netlify,
  GitHub Pages). Requiere actualizar `API_BASE` con la URL real del backend.
- **Sincronización periódica:** al no existir panel de administración, se
  recomienda un cron externo (p. ej. GitHub Actions o cron-job.org) que
  llame `POST /sync` con el bearer token, con la frecuencia deseada.

## 9. Puesta en marcha del esquema en Supabase (aprendido en validación E2E)

Este repositorio no incluye migraciones automáticas; las tablas deben
crearse manualmente antes del primer arranque. Ejecutar en el **SQL
Editor** de Supabase:

```sql
create table if not exists github_cache (
    repo_name    text primary key,
    description  text,
    html_url     text,
    language     text,
    updated_at   timestamptz
);

create table if not exists youtube_cache (
    video_id      text primary key,
    title         text,
    thumbnail_url text,
    published_at  timestamptz
);

-- Necesario si el rol service_role no hereda privilegios por defecto
-- sobre el schema public en tu proyecto (error típico: 42501 permission denied).
grant select, insert, update, delete on public.github_cache to service_role;
grant select, insert, update, delete on public.youtube_cache to service_role;

-- Opcional: aplica el mismo grant automáticamente a tablas nuevas futuras.
alter default privileges in schema public
  grant select, insert, update, delete on tables to service_role;
```

`repo_name` y `video_id` deben ser `primary key` (no solo `unique`):
son la clave de `on_conflict` que usa `CacheRepository.save_projects` /
`save_videos`; sin esa restricción, el `upsert` fallaría o insertaría
duplicados.

`SUPABASE_KEY` debe ser la **`service_role` key** del proyecto (no la
`anon` key), porque el backend necesita bypassear RLS para escribir en
caché sin depender de políticas por usuario. Esta key nunca debe
exponerse al frontend ni subirse a control de versiones (ver `.gitignore`).

## 10. Incidencias resueltas durante la validación end-to-end

Ver `tasks.md` → "Fase 4 — Validación end-to-end manual" para el detalle
completo. En resumen, los cinco problemas encontrados al desplegar este
proyecto por primera vez fueron de **configuración de entorno**, no de
código: ruta del `.env`, tablas de Supabase inexistentes, permisos de
`service_role` no otorgados, un `GITHUB_TOKEN` inválido, y el reproductor
de YouTube rechazando el origen `file://` al abrir el frontend con doble
clic en vez de servirlo por HTTP.


## 11. Riesgos conocidos / deuda técnica

- El caché no elimina registros obsoletos (repos borrados o videos
  removidos de la playlist permanecen indefinidamente). Ver `requirements.md §6`.
- No hay pruebas automatizadas; `test_httpx.py` es un script manual y debería
  moverse a una carpeta `scripts/` o eliminarse del repo de producción.
- El token de `/sync` es estático (no rotación, no expiración). Aceptable
  para el tamaño actual del proyecto, pero debería revisarse si el proceso
  de sincronización se expone más ampliamente.
