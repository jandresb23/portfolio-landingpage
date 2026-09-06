# Especificación de Requisitos — cursal

**Versión:** 1.1.0
**Estado:** Aprobado
**Metodología:** Specification Driven Development (SDD)
**Notación de requisitos:** EARS (Easy Approach to Requirements Syntax)

## 1. Propósito

`cursal` es una plataforma de portafolio profesional que expone, mediante una
API propia, los repositorios de GitHub y los videos de una playlist de
YouTube de un desarrollador, cacheados en Supabase para evitar exceder los
límites de tasa (rate limits) de las APIs externas y para servir contenido
de forma rápida y estable al frontend.

## 2. Alcance

Incluye:
- Backend API (FastAPI) con endpoints de lectura de caché y sincronización.
- Persistencia de caché en Supabase (PostgreSQL).
- Integración server-to-server con la API REST de GitHub y la API de
  YouTube Data v3.
- Frontend estático (HTML/Tailwind/JS) que consume la API para renderizar
  el portafolio.

No incluye (fuera de alcance en esta versión):
- Autenticación de usuarios finales del portafolio (es un sitio público de
  solo lectura).
- Panel de administración visual para disparar la sincronización (se hace
  vía llamada HTTP autenticada, p. ej. cron job o llamada manual).
- Internacionalización del frontend (actualmente solo en español).

## 3. Actores

| Actor | Descripción |
|---|---|
| Visitante | Usuario anónimo que navega el portafolio público. |
| Proceso de sincronización | Cliente autenticado (cron/job externo o el propio operador) que dispara `/api/v1/sync`. |
| GitHub API | Proveedor externo de datos de repositorios. |
| YouTube Data API | Proveedor externo de datos de videos. |
| Supabase | Almacén de persistencia/caché. |

## 4. Requisitos funcionales

### 4.1 Consulta de proyectos

- **REQ-F-01:** CUANDO un visitante solicite `GET /api/v1/projects`, EL
  sistema DEBERÁ devolver la lista de repositorios cacheados ordenada por
  `updated_at` descendente.
- **REQ-F-02:** SI la tabla `github_cache` está vacía, ENTONCES EL sistema
  DEBERÁ devolver `{"status": "success", "data": []}` (no un error).
- **REQ-F-03:** CADA elemento de la respuesta DEBERÁ incluir `repo_name`,
  `description`, `html_url`, `language` y `updated_at`.

### 4.2 Consulta de videos

- **REQ-F-04:** CUANDO un visitante solicite `GET /api/v1/videos`, EL
  sistema DEBERÁ devolver la lista de videos cacheados ordenada por
  `published_at` descendente.
- **REQ-F-05:** CADA elemento de la respuesta DEBERÁ incluir `video_id`,
  `title`, `thumbnail_url` y `published_at`.

### 4.3 Sincronización de caché

- **REQ-F-06:** CUANDO se reciba `POST /api/v1/sync` con un header
  `Authorization: Bearer <token>` válido, EL sistema DEBERÁ: (1) obtener los
  6 repositorios más recientemente actualizados desde GitHub, (2) obtener
  hasta 10 videos de la playlist configurada de YouTube, y (3) hacer upsert
  de ambos conjuntos en Supabase.
- **REQ-F-07:** SI el header `Authorization` está ausente o no tiene el
  prefijo `Bearer `, ENTONCES EL sistema DEBERÁ responder `401 Unauthorized`.
- **REQ-F-08:** SI el token no coincide con `SYNC_SECRET_KEY`, ENTONCES EL
  sistema DEBERÁ responder `403 Forbidden`.
- **REQ-F-09:** SI `SYNC_SECRET_KEY` no está configurado en el entorno,
  ENTONCES EL sistema DEBERÁ responder `503 Service Unavailable` sin
  intentar comparar tokens (no debe existir un secreto por defecto).
- **REQ-F-10:** SI GitHub o YouTube responden con un error o no responden
  dentro del tiempo de espera configurado, ENTONCES EL sistema DEBERÁ
  responder `502 Bad Gateway` con un mensaje genérico, y DEBERÁ registrar el
  detalle técnico solo en los logs del servidor (nunca en la respuesta al
  cliente).
- **REQ-F-11:** LA sincronización DEBERÁ hacer upsert por lote (no una
  llamada por registro) usando `repo_name` y `video_id` como claves de
  conflicto respectivamente, de forma que ejecuciones repetidas no generen
  duplicados.

### 4.4 Frontend

- **REQ-F-12:** CUANDO la página cargue, EL frontend DEBERÁ solicitar
  `/projects` y `/videos` y renderizar los resultados en sus respectivas
  secciones.
- **REQ-F-13:** SI una petición al backend falla, ENTONCES EL frontend
  DEBERÁ mostrar un mensaje de error visible al usuario en la sección
  correspondiente, en lugar de dejar el estado de carga (skeleton)
  indefinidamente.
- **REQ-F-14:** CUANDO el visitante haga clic en una tarjeta de video, EL
  frontend DEBERÁ abrir un modal con el reproductor embebido de YouTube en
  autoplay.
- **REQ-F-15:** EL frontend DEBERÁ permitir cerrar el modal de video tanto
  con el botón de cierre como con la tecla `Escape`.

## 5. Requisitos no funcionales

- **REQ-NF-01 (Seguridad):** EL sistema NO DEBERÁ tener valores por defecto
  inseguros para secretos (`SYNC_SECRET_KEY`); su ausencia debe deshabilitar
  la funcionalidad protegida, no habilitarla con un valor conocido.
- **REQ-NF-02 (Seguridad):** LA comparación del token de sincronización
  DEBERÁ hacerse en tiempo constante para mitigar ataques de temporización.
- **REQ-NF-03 (Seguridad):** LA configuración de CORS NO DEBERÁ combinar
  `allow_origins=["*"]` con `allow_credentials=True`.
- **REQ-NF-04 (Confiabilidad):** TODA llamada HTTP saliente (GitHub,
  YouTube) DEBERÁ tener un timeout explícito (máximo 10s totales, 5s de
  conexión) para evitar que una dependencia externa cuelgue el proceso de
  sincronización indefinidamente.
- **REQ-NF-05 (Rendimiento):** LAS operaciones de escritura en caché
  DEBERÁN minimizar el número de round-trips a Supabase (upsert en lote).
- **REQ-NF-06 (Observabilidad):** LOS errores durante la sincronización
  DEBERÁN quedar registrados en los logs del servidor con suficiente detalle
  para diagnóstico, sin exponer ese detalle en la respuesta HTTP.
- **REQ-NF-07 (Disponibilidad):** LOS endpoints de lectura (`/projects`,
  `/videos`) DEBERÁN seguir funcionando aunque `/sync` esté deshabilitado
  por falta de configuración.
- **REQ-NF-08 (Mantenibilidad):** EL código DEBERÁ seguir una arquitectura
  en capas (routers → repositories/services → database), sin lógica de
  negocio en los routers.

## 6. Fuera de alcance / trabajo futuro

- Borrado de registros obsoletos en `github_cache`/`youtube_cache` cuando un
  repo o video deja de existir en el origen (actualmente el caché solo
  crece).
- Autenticación real de administración (hoy es un bearer token estático).
- Paginación en `/projects` y `/videos`.
- Pruebas automatizadas (actualmente solo existe un script manual,
  `test_httpx.py`, que no forma parte de una suite real).

## 7. Criterios de aceptación globales

- [x] La aplicación arranca sin errores de sintaxis o importación con
      `uvicorn app.main:app`. — Validado.
- [x] Con `SYNC_SECRET_KEY` sin definir, `/sync` responde `503` y el resto
      de endpoints funciona con normalidad. — Validado.
- [x] Con `SYNC_SECRET_KEY` definido y un token correcto, `/sync` puebla
      `github_cache` y `youtube_cache` sin duplicados al ejecutarse dos
      veces seguidas. — Validado.
- [x] El frontend muestra un mensaje de error visible si el backend no
      responde. — Validado.

> Validación end-to-end completa realizada contra un proyecto real de
> Supabase, GitHub y YouTube. Ver `tasks.md` → "Fase 4 — Validación
> end-to-end manual" para la tabla de resultados y las incidencias de
> configuración encontradas (ninguna fue un bug de código).
