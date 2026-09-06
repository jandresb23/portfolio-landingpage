# Plan de Tareas — cursal

**Deriva de:** `requirements.md`, `design.md`
**Convención:** cada tarea referencia el/los requisito(s) que satisface.

## Fase 0 — Correcciones críticas (completadas en esta iteración)

- [x] **T-01** Corregir `SyntaxError` en `database.py` (faltaba `def` en
      `get_client`). _Bloqueaba el arranque de toda la aplicación._
      → REQ-NF-08
- [x] **T-02** Eliminar el valor por defecto inseguro de `SYNC_SECRET_KEY` y
      responder `503` cuando no esté configurado. → REQ-F-09, REQ-NF-01
- [x] **T-03** Reemplazar la comparación de tokens por
      `secrets.compare_digest`. → REQ-NF-02
- [x] **T-04** Corregir configuración de CORS (`allow_credentials` solo con
      orígenes explícitos vía `ALLOWED_ORIGINS`). → REQ-NF-03
- [x] **T-05** Agregar timeout explícito a `GitHubProvider` y
      `YouTubeProvider`. → REQ-NF-04
- [x] **T-06** Cambiar upserts en bucle por upsert en lote en
      `CacheRepository`. → REQ-NF-05, REQ-F-11
- [x] **T-07** Registrar errores de `/sync` con `logger.exception` y dejar
      de exponer `str(e)` al cliente. → REQ-F-10, REQ-NF-06
- [x] **T-08** Frontend: mostrar mensaje de error visible cuando falla el
      fetch de `/projects` o `/videos`, en vez de dejar el skeleton
      indefinidamente. → REQ-F-13
- [x] **T-09** Frontend: permitir cerrar el modal de video con `Escape`.
      → REQ-F-15
- [x] **T-10** Actualizar `_env.example` con `ALLOWED_ORIGINS` y comentarios
      de seguridad para `SYNC_SECRET_KEY`.
- [x] **T-11** Actualizar `README.md` con instrucciones de despliegue,
      variables de entorno y notas de seguridad.
- [x] **T-12** Generar documentos SDD (`requirements.md`, `design.md`,
      `tasks.md`).

## Fase 1 — Higiene de repositorio

- [ ] **T-13** Mover o eliminar `test_httpx.py` (script manual, no es parte
      de una suite de tests real). Sugerencia: `scripts/check_httpx.py` o
      borrarlo si ya cumplió su propósito de diagnóstico.
- [x] **T-14** Agregar `.gitignore` para excluir `.env`, `__pycache__/`,
      `.venv/` y demás artefactos locales. → `.gitignore`.
- [x] **T-15** Confirmar que existen constraints `UNIQUE`/`PRIMARY KEY` en
      `github_cache.repo_name` y `youtube_cache.video_id` en Supabase.
      Verificado en la validación E2E: las tablas se crearon con
      `repo_name`/`video_id` como `primary key`, y el upsert de `/sync`
      corrido dos veces seguidas no generó duplicados.

## Fase 2 — Pruebas automatizadas

- [x] **T-16** Suite de tests unitarios para `GitHubProvider` y
      `YouTubeProvider` con `httpx` mockeado vía `respx`. →
      `tests/test_github_service.py`, `tests/test_youtube_service.py`.
- [x] **T-17** Tests de integración para `/api/v1/sync` cubriendo los casos:
      sin header, token inválido, `SYNC_SECRET_KEY` no configurado, éxito y
      fallo upstream sin fuga de detalles. → `tests/test_api.py`.
- [x] **T-18** Test de contrato para `/projects` y `/videos` verificando el
      shape de la respuesta y el caso de caché vacía (REQ-F-02, REQ-F-03,
      REQ-F-05). → `tests/test_api.py`.
- [x] **T-18b** Test unitario que verifica que el upsert de caché es en
      lote (una sola llamada) y no un loop (REQ-NF-05). →
      `tests/test_cache_repository.py`.

> ⚠️ Nota: estos tests fueron escritos y verificados sintácticamente
> (`python -m py_compile`), pero no pudieron **ejecutarse** en este entorno
> porque no tiene acceso a red para instalar `fastapi`, `httpx`, `pytest`,
> `pytest-asyncio` ni `respx`. Ejecútalos en tu máquina o en CI con:
> ```bash
> pip install -r requirements-dev.txt
> pytest -v
> ```

## Fase 3 — Mejoras funcionales (backlog, fuera del alcance actual)

- [ ] **T-19** Borrado de registros obsoletos en cada sincronización (repos
      eliminados de GitHub o videos removidos de la playlist).
- [ ] **T-20** Paginación en `/projects` y `/videos`.
- [ ] **T-21** Endpoint de salud (`/health`) que verifique conectividad con
      Supabase, útil para el monitor de Render.
- [ ] **T-22** Reemplazar el bearer token estático de `/sync` por un
      mecanismo con expiración/rotación si el proceso se automatiza vía un
      servicio de terceros.
- [ ] **T-23** Conectar la suite de `pytest` a un workflow de GitHub
      Actions para que corra en cada push/PR. _(Pospuesto a propósito;
      ver conversación — retomar cuando se desee CI automatizado.)_

## Fase 4 — Validación end-to-end manual (completada)

Ejecutada por el usuario en un entorno local (Windows) contra un proyecto
real de Supabase, GitHub y YouTube. Resultados:

| # | Prueba | Resultado |
|---|---|---|
| 1 | Arranque limpio del servidor (`uvicorn app.main:app`) | ✅ |
| 2 | `GET /`, `GET /api/v1/projects`, `GET /api/v1/videos` | ✅ |
| 3 | `POST /api/v1/sync` sin header → `401` | ✅ |
| 4 | `POST /api/v1/sync` con token incorrecto → `403` | ✅ |
| 5 | `POST /api/v1/sync` con `SYNC_SECRET_KEY` real, GitHub y YouTube reales → `200` | ✅ |
| 6 | Repetir `/sync` sin generar filas duplicadas (upsert por PK) | ✅ |
| 7 | Headers de CORS (`access-control-allow-origin: *`, sin `allow-credentials`) | ✅ |
| 8 | Frontend: carga de tarjetas con datos reales | ✅ |
| 9 | Frontend: modal de video (abrir/cerrar con botón y `Escape`) | ✅ |
| 10 | Frontend: mensaje de error visible con el backend caído | ✅ |
| 11 | Frontend: sin errores de CORS en consola del navegador | ✅ |
| — | Suite automatizada `pytest` (17 tests) | ✅ (11 warnings inofensivos de Starlette/httpx, dejados visibles a propósito) |

**Incidencias encontradas y resueltas durante la validación** (no eran
bugs del código, sino de configuración del entorno — documentadas aquí
porque son errores comunes al desplegar este proyecto por primera vez):

1. `.env` no se cargaba → causa: `uvicorn` se ejecutaba desde un directorio
   distinto al que contenía el `.env`, o el archivo tenía formato inválido.
   Solución: correr `uvicorn` desde la raíz del proyecto donde vive el `.env`.
2. `PGRST205 — Could not find the table 'public.github_cache'` → las
   tablas nunca se crearon en Supabase (este repo no incluye una
   migración). Solución: DDL manual, ver `design.md §2` y §9 (nueva).
3. `42501 — permission denied for table github_cache` → el rol
   `service_role` no tenía privilegios sobre las tablas recién creadas.
   Solución: `GRANT SELECT, INSERT, UPDATE, DELETE ... TO service_role;`,
   ver `design.md §9`.
4. `GitHub 401 Bad credentials` → `GITHUB_TOKEN` en el `.env` tenía un
   valor inválido/expirado. Solución: quitar la variable (es opcional; sin
   ella igual funciona, con rate limit más bajo) o generar un token nuevo.
5. YouTube embed `Error 153` en el modal de video → causa: el frontend se
   abría con doble clic (`file://`), y el reproductor embebido de YouTube
   no acepta ese origen. Solución: servir `frontend/` con un servidor HTTP
   local (`python -m http.server`) en vez de abrir el archivo directamente.


## Matriz de trazabilidad (resumen)

| Requisito | Tarea(s) |
|---|---|
| REQ-F-09 | T-02 |
| REQ-F-10 | T-07 |
| REQ-F-11 | T-06 |
| REQ-F-13 | T-08 |
| REQ-F-15 | T-09 |
| REQ-NF-01 | T-02 |
| REQ-NF-02 | T-03 |
| REQ-NF-03 | T-04 |
| REQ-NF-04 | T-05 |
| REQ-NF-05 | T-06 |
| REQ-NF-06 | T-07 |
| REQ-NF-08 | T-01 |
