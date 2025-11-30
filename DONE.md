# Project Snapshot

## Repository Layout
- `docker-compose.yml` — Postgres 15 container for local dev.
- `.env` — local settings (DB URL, JWT settings, service URLs, service-account creds).
- `requirements.txt` — shared Python deps (FastAPI, SQLAlchemy, Pydantic v2, jose, passlib, pytest, Sphinx).
- `docs/` — Sphinx docs scaffolding (`index.rst`, service overviews, architecture placeholder).
- `postman/SmartMeetingRoom.postman_collection.json` — HTTP collection aligned with current API routes (includes an Edge Cases folder).
- `screenshots/` — evidence of previous milestones/tests.
- `tests/test_smoke.py` — simple import smoke test.

## Shared Modules (`common/`, `db/`)
- `db/schema.py` — SQLAlchemy models: `User`, `Room`, `Booking`, `Review` with relationships; defaults to UTC timestamps, CASCADE on bookings/rooms for FKs.
- `db/init_db.py` — engine/session factory from `common.config`; `init_db()` creates tables; `get_db()` generator for FastAPI deps.
- `db/seed_data.py` — stub for demo data.
- `common/config.py` — Pydantic `Settings`; service URLs, JWT config (optional issuer/audience/leeway), HTTP client retries/timeouts, service-account toggle, feature flags.
- `common/auth.py` — bcrypt password hashing/verify; JWT create/verify with exp/role and optional iss/aud + leeway.
- `common/rbac.py` — role constants and allow check.
- `common/http_client.py` — httpx wrapper with base URL, default headers, retry/backoff helper.
- `common/logging_utils.py` — minimal logging config helper.
- `common/exceptions.py` — custom error classes.
- `common/service_account.py` — local minting/caching of service-account JWTs for inter-service calls.

## Users Service (`services/users/`)
- `app/main.py` — FastAPI app, mounts auth, users, admin routers; `/health`.
- `app/dependencies.py` — DB dep wrapper; OAuth2 bearer; `get_current_user` via JWT (supports service-account); `require_roles` helper.
- `app/schemas.py` — Pydantic models for user create/update/read, login, token; role literals.
- `app/service_layer/user_service.py` — role normalization, case-insensitive uniqueness, password strength + lockout counters, auth, token issuance, list users, password change helper.
- `app/repository/user_repository.py` — CRUD helpers (case-insensitive lookups, pagination).
- `app/routers/auth_routes.py` — `/users/register`, `/users/login`, `/users/me`.
- `app/routers/users_routes.py` — list users (admin/auditor, paginated), get by username or id (service-account/auditor/admin), update/delete self with duplicate checks, change password.
- `app/routers/admin_routes.py` — admin-only role updates (self-demotion blocked), deletes by id, booking history proxy via Bookings, password reset.
- `app/clients/bookings_client.py` — HTTP client to Bookings (service-account auth, stub fallback) for user booking history.
- Tests: SQLite override fixtures; coverage for registration, login, RBAC, duplicate checks, role update validation.
- Dockerfile — skeleton (base image + workdir).

## Rooms Service (`services/rooms/`)
- `app/main.py` — FastAPI app, mounts `/rooms` router; `/health`.
- `app/dependencies.py` — DB session (config DB URL), JWT bearer decode into `CurrentUser`, role guard for room managers.
- `app/schemas.py` — room create/update/read/status models; equipment list↔CSV normalization validator; status enum.
- `app/repository/rooms_repository.py` — CRUD + filters (min_capacity, location case-insensitive, equipment tokens), pagination, case-insensitive name lookup.
- `app/service_layer/rooms_service.py` — whitespace/name normalization, uniqueness, equipment CSV conversion, create/update/list (pagination, multi-equipment filters), status assembly calling Bookings availability.
- `app/clients/bookings_client.py` — HTTP call to Bookings `/bookings/check-availability` with service-account auth + fallback.
- `app/routers/rooms_routes.py` — CRUD and status endpoints with RBAC (admin/facility_manager for writes; auth for reads) and optional availability window.
- Tests: SQLite override; endpoint tests for RBAC, filters, status shape, CRUD.
- Dockerfile — installs deps, copies repo, runs uvicorn on 8002.

## Bookings Service (`services/bookings/`)
- `app/main.py` — FastAPI app, mounts `/bookings` and `/admin/bookings`; `/health`.
- `app/dependencies.py` — DB dep via `db.init_db`, JWT bearer decode to `CurrentUser`, role guards for admin/admin+FM+auditor/service-account.
- `app/schemas.py` — booking create/update/read models (datetime windows, status).
- `app/repository/booking_repository.py` — CRUD, list by user/all (pagination), conflict finder (overlap per room, excluding cancelled and optionally self).
- `app/service_layer/booking_service.py` — normalize times to UTC, validate duration min/max, ensure user exists and room is active, detect conflicts, admin override cancels conflicts, owner-only update/cancel (idempotent cancel), admin force-cancel; availability helper and user/room filtered list.
- `app/routers/bookings_routes.py` — user-facing create/list own/update/cancel; availability check endpoint.
- `app/routers/admin_routes.py` — list all (admin/FM/auditor/service-account, paginated), create with override (admin), force-cancel (admin), list bookings by user and by user+room.
- Tests: SQLite overrides; service-layer tests for conflicts/overrides/permissions/range validation/nonexistent entities; endpoint tests mirror HTTP behaviors and JWT auth.
- Dockerfile — skeleton (base image + workdir).

## Reviews Service (`services/reviews/`)
- `app/main.py` — FastAPI app, mounts `/reviews` CRUD and moderation; `/health`.
- `app/dependencies.py` — DB session (config DB URL), JWT bearer decode to `CurrentUser`, auth/mode guards (auditor read-only).
- `app/schemas.py` — review create/update/read models; rating 1–5, comment max length.
- `app/repository/reviews_repository.py` — CRUD, list by room, list flagged.
- `app/service_layer/reviews_service.py` — sanitize comments (strip HTML, collapse whitespace), validate rating/comment, optional booking enforcement via config, simple profanity check, flag/unflag, list helpers; uses real clients with service-account auth + fallback.
- `app/clients/users_client.py`, `rooms_client.py`, `bookings_client.py` — HTTP calls to Users/Rooms/Bookings with service-account auth and stub fallback.
- `app/routers/reviews_routes.py` — create/list by room (auditor read-only), update/delete owner OR admin/moderator; auditors blocked from creates.
- `app/routers/moderation_routes.py` — flag/unflag/list flagged (moderator/admin).
- Tests: SQLite override; endpoint tests for auth, rating validation, ownership, moderation, sanitization, listings.
- Dockerfile — installs deps, copies repo, runs uvicorn on 8004.

## Testing/Tooling
- Each service’s tests override DB dependencies to isolated SQLite files and reset schema per test.
- JWT helpers in tests build tokens directly via `common.auth.create_access_token` to bypass full login flows.
- Sphinx docs provide high-level service descriptions and architecture placeholder.
- Postman collection includes Edge Cases covering validation/RBAC scenarios (duplicate usernames, short bookings, availability check, duplicate rooms, auditor create-review denial).
