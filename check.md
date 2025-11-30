# Verification Guide (Prof Evidence)

## Task A – Circuit Breaker & Rate Limiting (implemented)
- **Code**: circuit breaker in `common/circuit_breaker.py` + wiring in `common/http_client.py`; rate limiter in `common/rate_limiter.py`.
- **Where applied**:
  - Rate limit: Users `POST /users/register`, `POST /users/login`; Bookings `POST /bookings/`; Reviews `POST /reviews`.
  - Errors: `CIRCUIT_OPEN` (503), `RATE_LIMIT_EXCEEDED` (429), `DOWNSTREAM_ERROR` (502) in `common/exceptions.py`.
- **How to demo/screenshot**:
  1) Circuit breaker: stop downstream (e.g., `docker stop bookings_service`) or point `BOOKINGS_SERVICE_URL` to bad host. Hit `/rooms/{id}/status` 4 times with a valid token: calls 1–3 → 502 `DOWNSTREAM_ERROR`; call 4 → 503 `CIRCUIT_OPEN` (threshold=3). Restart bookings, wait ~30s (open timeout), call again to show recovery. Capture the 502/503 bodies and a log line with `CIRCUIT_OPEN`.
  2) Rate limiting: default 10 req/60s. Call `/users/login` 11 times quickly (bad creds are fine); last call → 429 `RATE_LIMIT_EXCEEDED`. Same pattern for `/users/register`, `/bookings/`, `/reviews`. Screenshot the 429 and a log line with `RATE_LIMIT_EXCEEDED`.
  3) Logs: grab any global-handler log showing service name, path, and `error_code`.

## Task B – Bookings & Reviews Analytics (implemented)
- **Endpoints**:
  - Bookings: `GET /analytics/bookings/summary`, `GET /analytics/bookings/by-room` (roles: admin/FM/auditor/service_account).
  - Reviews: `GET /analytics/reviews/average-rating-by-room` (roles: admin/mod/facility_manager/auditor).
- **Code**: bookings analytics in `services/bookings/app/routers/analytics_routes.py` + repo/service helpers; reviews analytics in `services/reviews/app/routers/analytics_routes.py` + helpers; response schemas in `services/bookings/app/schemas.py`.
- **How to demo/screenshot**:
  - Seed a few bookings/reviews (or reuse existing data).
  - Call each endpoint in Postman with an admin token; capture JSON responses showing counts/averages.
  - Grafana dashboard (done) — include screenshots of panels + data-source test (details below).

## Tests to Run (for your screenshots)
- `pytest tests/test_circuit_breaker.py`
- `pytest tests/test_rate_limiter.py`
- `pytest services/bookings/tests/test_analytics_endpoints.py`
- `pytest services/reviews/tests/test_analytics_endpoints.py`

## Grafana evidence (completed dashboard)
- Start Grafana on the compose network:
  - `docker run -d --name grafana --network mayssahajjhassan_ahmadabbas_meetingroom_default -p 3000:3000 -e GF_SECURITY_ADMIN_PASSWORD=admin grafana/grafana:10.4.5`
- Add Postgres data source (UI http://localhost:3000, admin/admin):
  - Host `smart_meeting_room_db:5432`, DB `smart_meeting_room`, User `postgres`, Password `postgres`, SSL disabled; click “Save & test” (screenshot success).
- Panels (bar or table):
  - Bookings per room: `SELECT room_id, COUNT(*) AS total FROM bookings GROUP BY room_id;`
  - Avg rating per room: `SELECT room_id, AVG(rating) AS avg_rating FROM reviews GROUP BY room_id;`
- Save dashboard; screenshot both panels and the data-source test success.
