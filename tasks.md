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

## Fase 1 — Higiene de repositorio (recomendada, no implementada aún)

- [ ] **T-13** Mover o eliminar `test_httpx.py` (script manual, no es parte
      de una suite de tests real). Sugerencia: `scripts/check_httpx.py` o
      borrarlo si ya cumplió su propósito de diagnóstico.
- [ ] **T-14** Agregar `.gitignore` (si no existe) para excluir `.env`,
      `__pycache__/`, `.venv/`.
- [ ] **T-15** Confirmar que existen constraints `UNIQUE` en
      `github_cache.repo_name` y `youtube_cache.video_id` en el esquema de
      Supabase (requerido para que el `on_conflict` del upsert funcione).

## Fase 2 — Pruebas automatizadas (backlog)

- [ ] **T-16** Suite de tests unitarios para `GitHubProvider` y
      `YouTubeProvider` con `httpx` mockeado (p. ej. `respx`).
- [ ] **T-17** Tests de integración para `/api/v1/sync` cubriendo los casos:
      sin header, token inválido, `SYNC_SECRET_KEY` no configurado, y
      sincronización exitosa (con Supabase mockeado).
- [ ] **T-18** Test de contrato para `/projects` y `/videos` verificando el
      shape de la respuesta (REQ-F-03, REQ-F-05).

## Fase 3 — Mejoras funcionales (backlog, fuera del alcance actual)

- [ ] **T-19** Borrado de registros obsoletos en cada sincronización (repos
      eliminados de GitHub o videos removidos de la playlist).
- [ ] **T-20** Paginación en `/projects` y `/videos`.
- [ ] **T-21** Endpoint de salud (`/health`) que verifique conectividad con
      Supabase, útil para el monitor de Render.
- [ ] **T-22** Reemplazar el bearer token estático de `/sync` por un
      mecanismo con expiración/rotación si el proceso se automatiza vía un
      servicio de terceros.

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
