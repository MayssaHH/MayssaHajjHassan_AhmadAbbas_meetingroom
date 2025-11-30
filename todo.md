## (1) Enhanced Inter-Service Communication

### (Circuit Breaker + Rate Limiting & Throttling)

### A. What the prof expects + what to show in the report

* Show that:

  * **Outgoing HTTP calls between services** are protected by a **circuit breaker** so a failing service doesn’t spam another one.
  * Sensitive endpoints (e.g., login, booking creation) have **rate limiting** / throttling to prevent misuse.
* In the **report**, you should have:

  1. A short explanation of the circuit breaker logic (states, thresholds, reset timeout).
  2. A diagram or bullet list showing **which services call which** and how the breaker wraps these calls.
  3. Postman screenshots:

     * One normal call to a downstream service.
     * One scenario where the downstream keeps failing and the circuit transitions to *open* → immediate `CIRCUIT_OPEN` error.
  4. Description + screenshots for rate limiting:

     * Example: 5 login attempts in 10 seconds → the 6th returns 429 `RATE_LIMIT_EXCEEDED`.
  5. Mention where the code lives (`common/circuit_breaker.py`, `common/rate_limiter.py`, changes in clients/dependencies).

---

### B. Implementation plan in our repo

#### 1) Circuit Breaker

**Goal**: wrap all inter-service HTTP calls (Users ↔ Bookings, Rooms → Bookings, Reviews → Users/Rooms/Bookings) with a small in-memory circuit breaker.

**New files / changes:**

* `common/circuit_breaker.py`

  * Define:

    * `CircuitState = Enum("CLOSED", "OPEN", "HALF_OPEN")`
    * `CircuitBreaker` class holding:

      * `state`
      * `failure_count`
      * `last_failure_ts`
      * config: `failure_threshold`, `open_timeout`, `half_open_max_calls`
    * Methods:

      * `before_call(service_name)` → either allow or raise `CircuitOpenError`.
      * `record_success(service_name)` → reset state to CLOSED.
      * `record_failure(service_name)` → increment failure_count, possibly move to OPEN and store timestamp.
  * Keep a **dict per service**: `"users"`, `"rooms"`, `"bookings"`, `"reviews"`.

* `common/exceptions.py`

  * Add `CircuitOpenError(AppError)` with:

    * `http_status = 503`
    * `error_code = "CIRCUIT_OPEN"`

* `common/config.py`

  * Add config fields:

    * `CB_FAILURE_THRESHOLD` (e.g., 3)
    * `CB_OPEN_TIMEOUT_SECONDS` (e.g., 30)
    * `CB_HALF_OPEN_MAX_CALLS` (e.g., 1–3)
  * Optional feature flag: `CB_ENABLED`.

* `common/http_client.py`

  * Extend `ServiceHTTPClient` to accept a `service_name` and **use the circuit breaker**:

    * Before every request: `circuit_breaker.before_call(service_name)`.
    * If `httpx` raises connection/timeout or returns 5xx:

      * call `circuit_breaker.record_failure(service_name)`
      * raise an appropriate `AppError` (e.g., `DownstreamServiceError` or reuse `InternalServerError` with `details`).
    * On success: `circuit_breaker.record_success(service_name)`.

* Update all **client modules**:

  * `services/rooms/app/clients/bookings_client.py`
  * `services/users/app/clients/bookings_client.py`
  * `services/reviews/app/clients/users_client.py`, `rooms_client.py`, `bookings_client.py`
  * Make sure they construct `ServiceHTTPClient(service_name="bookings")` or `"users"` / `"rooms"` accordingly so the breaker state is per target service.

---

#### 2) Rate Limiting & Throttling

**Goal**: simple per-user or per-IP request limit for selected endpoints.

**New files / changes:**

* `common/rate_limiter.py`

  * Use an in-memory dictionary:

    * key = (user_id or IP, endpoint)
    * value = deque of timestamps (requests within the window)
  * Configurable constants from `common/config.py`:

    * `RATE_LIMIT_WINDOW_SEC` (e.g., 60)
    * `RATE_LIMIT_MAX_REQUESTS` (e.g., 10 per minute)
  * Functions:

    * `check_rate_limit(key: str)` → raises `RateLimitExceededError` if over the limit.

* `common/exceptions.py`

  * Add `RateLimitExceededError(AppError)`:

    * `http_status = 429`
    * `error_code = "RATE_LIMIT_EXCEEDED"`

* Each service’s `dependencies.py`

  * Add a **FastAPI dependency** like `rate_limited(key_fn)`:

    * For user-specific limits: use `current_user.id`.
    * For unauthenticated endpoints (like `/users/login`), use `client_ip` from request.
  * Attach this dependency to **important endpoints**:

    * Users service:

      * `POST /users/login`
      * `POST /users/register`
    * Bookings service:

      * `POST /bookings/` (user create)
    * Reviews service:

      * `POST /reviews` (create review)
    * (Optional more if you want.)

* Update **error validation docs** and Sphinx:

  * Add `RATE_LIMIT_EXCEEDED` description in `error_validation.rst`.

---

### C. Testing & screenshots

**Tests (pytest):**

* Unit tests for `CircuitBreaker`:

  * After `failure_threshold` failures → state becomes OPEN.
  * During OPEN and before timeout → `before_call` raises `CircuitOpenError`.
  * After `open_timeout` → state moves to HALF_OPEN, next success resets to CLOSED.
* Integration tests for one client (e.g., Reviews → Rooms):

  * Monkeypatch `ServiceHTTPClient` to simulate consecutive failures and assert `CircuitOpenError` is raised.
* Rate limiter tests:

  * Call a rate-limited endpoint N+1 times in a tight loop and assert the final response is 429 with `RATE_LIMIT_EXCEEDED`.

**Report / screenshots:**

* Postman:

  * A normal inter-service call working.
  * Same call after simulating several downstream failures, showing immediate 503 `CIRCUIT_OPEN`.
  * Rate-limited endpoint (e.g., login) called multiple times → last one shows 429.
* One snippet of log output showing `error_code` and service name for a circuit open / rate limit event.
* Short paragraph explaining where the code lives and how it connects to the rest of the system.

---

## (5) Analytics and Insights

### (Real-Time Dashboards + Data Analytics)

### A. What the prof expects + report content

* Show **aggregate insights** from your data:

  * Total bookings, bookings per room, average ratings per room, etc.
* Show at least **one simple real-time dashboard** built with Grafana or Kibana reading from your Postgres DB.
* In the report:

  1. Describe new analytics endpoints (URLs, roles, sample JSON).
  2. Explain how these queries can be used by dashboards.
  3. Include **Grafana dashboard screenshots** (panels for bookings & reviews).

---

### B. Implementation plan in our repo

#### 1) Data Analytics Endpoints

**Bookings service:**

* New schemas in `services/bookings/app/schemas.py`:

  * `BookingsSummaryResponse` → `{ total, confirmed, cancelled }`
  * `BookingsByRoomItem` → `{ room_id, total, confirmed, cancelled }`
  * `BookingsByRoomResponse` → `list[BookingsByRoomItem]`

* Repository additions in `services/bookings/app/repository/booking_repository.py`:

  * `get_bookings_summary(db)`:

    * Use SQL `COUNT(*)` grouped by status.
  * `get_bookings_by_room(db)`:

    * `SELECT room_id, status, COUNT(*) FROM bookings GROUP BY room_id, status`.

* Service layer additions in `services/bookings/app/service_layer/booking_service.py`:

  * Functions wrapping those repository calls and transforming them into the Pydantic responses.

* Router additions in `services/bookings/app/routers/admin_routes.py` (admin/FM/auditor/service_account):

  * `GET /admin/analytics/bookings/summary`
  * `GET /admin/analytics/bookings/by-room`
  * Restrict to roles: `admin`, `facility_manager`, `auditor`, `service_account`.

---

**Reviews service:**

* Schemas (`services/reviews/app/schemas.py`):

  * `AverageRatingByRoomItem` → `{ room_id, average_rating, review_count }`

* Repository (`services/reviews/app/repository/reviews_repository.py`):

  * `get_average_rating_by_room(db)`:

    * `SELECT room_id, AVG(rating), COUNT(*) FROM reviews GROUP BY room_id`.

* Service layer (`services/reviews/app/service_layer/reviews_service.py`):

  * Wrapper returning `list[AverageRatingByRoomItem]`.

* Router (`services/reviews/app/routers/moderation_routes.py` or new `analytics_routes.py`):

  * `GET /admin/analytics/reviews/average-rating-by-room` (admin/moderator/auditor).

---

#### 2) Real-Time Dashboards with Grafana

**docker-compose:**

* Add a `grafana` service:

  * Image: `grafana/grafana:latest`
  * Ports: expose `3000:3000`.
  * Environment:

    * `GF_SECURITY_ADMIN_USER=admin`
    * `GF_SECURITY_ADMIN_PASSWORD=admin` (or something simple for local).
  * Link / network: same Docker network and point it to the Postgres `db` service.

**Grafana configuration (manual, not code):**

1. Open `http://localhost:3000`, login as admin.
2. Add a **PostgreSQL data source**:

   * Host = name of DB service inside compose (`smart_meeting_room_db:5432`).
   * Database name, username, password same as compose.
3. Create a **“Bookings & Reviews Overview”** dashboard:

   * Panel 1:

     * Query: bookings count per room.
       `SELECT room_id AS "Room", COUNT(*) AS "Bookings" FROM bookings GROUP BY room_id;`
   * Panel 2:

     * Query: average rating per room.
       `SELECT room_id AS "Room", AVG(rating) AS "AvgRating" FROM reviews GROUP BY room_id;`
   * Optional Panel 3:

     * Bookings per day: group by `DATE(start_time)`.

Take screenshots showing these panels with data.

---

### C. Testing & screenshots

**Tests:**

* For each new analytics endpoint:

  * Create some test rows in the SQLite test DB.
  * Assert that the JSON matches expected aggregated results.
* Check RBAC:

  * Regular user hitting `/admin/analytics/...` gets 403.
  * Admin/FM/auditor can access.

**Screenshots for report:**

* Postman responses for:

  * `/admin/analytics/bookings/summary`
  * `/admin/analytics/bookings/by-room`
  * `/admin/analytics/reviews/average-rating-by-room`
* Grafana dashboard screenshot with:

  * A bar chart of bookings per room.
  * A bar chart or table with average rating per room.

