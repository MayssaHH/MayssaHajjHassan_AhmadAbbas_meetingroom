In this commit we standardized how all four microservices (Users, Rooms, Bookings, Reviews) handle and report errors, and we documented the validation and sanitization rules across the system. We introduced a shared error model in common/exceptions.py and wired global exception handlers in each service so that all API errors are returned in a single, consistent JSON format (error_code, message, optional details).

We then reviewed each service’s business logic and dependencies to ensure that input validation and permission checks raise the appropriate shared exceptions: invalid input (400), authentication failures (401), authorization violations (403), missing resources (404), and booking conflicts (409). We extended the test suites of all services to assert both the correct HTTP status codes and the unified error response shape for typical failure cases (invalid rating, overlapping bookings, negative capacity, non-admin access, etc.).

Finally, we updated the Postman collection with example error responses for key endpoints and added a dedicated Sphinx page (error_validation.rst) describing the global error schema, the main error types, and the validation/sanitization logic per service—especially review sanitization and booking time-range validation. This commit doesn’t add new features, but it makes the API behavior predictable, well-documented, and easier to consume by a frontend or other clients.
1. Define the **standard error JSON** for the whole system
2. Refine `common/exceptions.py`
3. (Optionally) tune `common/logging_utils.py`
4. Add **global exception handlers** in each `app/main.py`
5. Make dependencies + service-layer raise the right exceptions
6. Extend tests in each service to assert error *shape + status*
7. Update Postman collection with error examples
8. Write/finish `error_validation.rst` + tiny edits to service docs

No “who does what”, just what must be done.

---

## 1️⃣ Decide & freeze the standard error JSON format

**Goal:** Any error from any service should come back with the *same* JSON structure.

Pick a canonical shape (write this in your notes and in docs):

```json
{
  "error_code": "BOOKING_CONFLICT",
  "message": "Room is already booked in this time range.",
  "details": {
    "field": "start_time",
    "reason": "overlaps with another booking"
  }
}
```

Rules:

* `error_code`

  * Short machine-friendly ID (UPPER_SNAKE_CASE).
  * Examples:

    * `VALIDATION_ERROR`
    * `UNAUTHORIZED`
    * `FORBIDDEN`
    * `USER_NOT_FOUND`
    * `ROOM_NOT_FOUND`
    * `BOOKING_CONFLICT`
    * `REVIEW_NOT_FOUND`
    * `INTERNAL_ERROR`
* `message`

  * Human-readable English sentence.
  * Safe to show in frontend & report.
* `details` (optional)

  * Dict with contextual info:

    * For validation errors: `field`, `expected`, `actual`.
    * For conflicts: `room_id`, `start_time`, `end_time`.

This is the **contract** all handlers will use.

You will:

* Write this formally in `docs/source/error_validation.rst`.
* Keep it in your head when writing tests and Postman examples.

---

## 2️⃣ Refine `common/exceptions.py`

You already have custom exception classes; Commit 7 is where we standardize them around the JSON format.

### 2.1 Define a base app exception

Design concept (not code):

* A base class, e.g. `AppError`, with at least:

  * `http_status: int`
  * `error_code: str`
  * `message: str`
  * `details: dict | None`

All custom exceptions will:

* Inherit from this.
* Set a default `http_status` + `error_code`.
* Optionally accept a `details` dict when raised.

### 2.2 Define the main exception types

You should end up with something *like* (conceptually):

* `BadRequestError`

  * `http_status = 400`, `error_code = "VALIDATION_ERROR"`.
* `UnauthorizedError`

  * `http_status = 401`, `error_code = "UNAUTHORIZED"`.
* `ForbiddenError`

  * `http_status = 403`, `error_code = "FORBIDDEN"`.
* `NotFoundError`

  * `http_status = 404`, `error_code = "NOT_FOUND"` or more specific when instantiated.
* `ConflictError`

  * `http_status = 409`, `error_code = "BOOKING_CONFLICT"` or more generic `"CONFLICT"` depending on context.
* `InternalServerError` (optional fallback)

  * `http_status = 500`, `error_code = "INTERNAL_ERROR"`.

You can also choose specialized errors that subclass these but reuse the pattern, e.g.:

* `BookingConflictError(ConflictError)` with default `error_code="BOOKING_CONFLICT"`.
* `InvalidRatingError(BadRequestError)` with `error_code="INVALID_RATING"`.

**Important:** this file becomes the **single source of truth** for:

* Which errors exist,
* Their default HTTP status,
* Their error_code.

---

## 3️⃣ `common/logging_utils.py` (light touch)

Commit 7 does *not* require full-blown logging, but we should prep a helper that the global handlers can call.

Conceptually:

* Add a function like:

  * `log_error(request, exc)` – logs method, path, user (if available), error_code, message.
* Or a simpler:

  * `log_exception(exc)`.

You don’t need heavy logic here, just:

* A clear docstring explaining:
  “Used by global exception handlers in each service to log errors in a unified way.”

Later you can instrument more if needed.

---

## 4️⃣ Add global exception handlers in each `app/main.py`

Files to modify:

* `services/users/app/main.py`
* `services/rooms/app/main.py`
* `services/bookings/app/main.py`
* `services/reviews/app/main.py`

For each service:

### 4.1 Register handler for `AppError` (your base error)

* The handler will:

  * Receive `AppError`,

  * Build JSON:

    ```python
    {
      "error_code": exc.error_code,
      "message": exc.message,
      "details": exc.details or None
    }
    ```

  * Return it with `status_code=exc.http_status`.

* Call `logging_utils.log_error` inside to record the error.

### 4.2 Decide what to do with FastAPI’s `HTTPException`

Some places still raise `HTTPException` (401/403) directly. You have two options:

1. **Convert them to your AppError types** in dependencies/service-layer; or
2. Add another handler for `HTTPException` that:

   * Converts them into your JSON shape, with a generic error_code:

     * 401 → `UNAUTHORIZED`
     * 403 → `FORBIDDEN`
     * 404 → `NOT_FOUND`
     * 422 → `VALIDATION_ERROR`

Either way: **the client must always see your standard JSON**.

### 4.3 Optional: catch-all `Exception`

* Add a catch-all handler for plain `Exception`:

  * Logs full details.
  * Returns:

    ```json
    {
      "error_code": "INTERNAL_ERROR",
      "message": "An unexpected error occurred.",
      "details": null
    }
    ```
  * Status code `500`.

This gives you a robust fallback.

---

## 5️⃣ Make dependencies & service-layer raise appropriate exceptions

Now you propagate the new error model throughout the code.

### 5.1 Dependencies `app/dependencies.py`

For each service:

* **Users / Bookings / Rooms / Reviews**

Check functions like:

* `get_db()`
* `get_current_user()`
* `require_roles(...)` or `require_admin`, etc.

Places where you currently:

* Return `HTTPException(status_code=401, ...)`
* Or `HTTPException(status_code=403, ...)`

Change the *logical ones* to throw your custom exceptions:

* No/invalid JWT → `UnauthorizedError(message=...)`.
* Insufficient role → `ForbiddenError(message=...)`.

This ensures that:

* All auth/RBAC errors pass through the global handler and get standardized JSON.

You can keep FastAPI’s auth error for the OAuth2 scheme if it’s messy to swap; just ensure your HTTPException handler maps it into your structure.

---

### 5.2 Service-layer logic per service

Walk through each service-layer file:

* `services/users/app/service_layer/user_service.py`
* `services/rooms/app/service_layer/rooms_service.py`
* `services/bookings/app/service_layer/booking_service.py`
* `services/reviews/app/service_layer/reviews_service.py`

And normalize:

* Where do we raise, and what do we raise?

#### Users

Cases:

* Username or email already exists:

  * Raise `BadRequestError(error_code="USER_ALREADY_EXISTS", message="...")`.
* Invalid login credentials:

  * Raise `UnauthorizedError(error_code="INVALID_CREDENTIALS"... )`.
* User not found by id:

  * Raise `NotFoundError(error_code="USER_NOT_FOUND")`.

#### Rooms

Cases:

* `capacity <= 0`:

  * Raise `BadRequestError(error_code="INVALID_CAPACITY", details={"capacity": value})`.
* Room not found:

  * `NotFoundError(error_code="ROOM_NOT_FOUND")`.

#### Bookings

Cases:

* `start_time >= end_time`:

  * `BadRequestError(error_code="INVALID_TIME_RANGE")`.
* User or room does not exist (if you check via clients):

  * `NotFoundError(error_code="USER_NOT_FOUND")` etc.
* Overlapping booking:

  * `ConflictError(error_code="BOOKING_CONFLICT", details={...})`.
* Non-owner tries to update/cancel:

  * `ForbiddenError(error_code="NOT_OWNER")`.

#### Reviews

Cases:

* `rating` not in [1..5]:

  * `BadRequestError(error_code="INVALID_RATING")`.
* Comment too long:

  * `BadRequestError(error_code="INVALID_COMMENT")`.
* Review not found:

  * `NotFoundError(error_code="REVIEW_NOT_FOUND")`.
* Non-owner trying to edit/delete:

  * `ForbiddenError(error_code="NOT_OWNER")`.

**Also**:

* Where you rely on Pydantic validation (e.g., model fields constraints), it might raise 422 before you; you can:

  * Either let FastAPI handle it and map 422 in the HTTPException handler to `VALIDATION_ERROR`, or
  * Add extra checks in service-layer and throw `BadRequestError`.

### 5.3 Update docstrings

For key service methods, extend docstrings to say:

* “Raises `BadRequestError` if start_time is after end_time.”
* “Raises `ConflictError` if a booking already exists in that interval.”
* “Raises `ForbiddenError` if user tries to modify another user’s review.”

This is important for Sphinx and for you when you’re debugging later.

---

## 6️⃣ Extend tests to cover error shape + RBAC

Add/update tests in each service’s `tests/` folder.

### 6.1 Common checks

For every test that expects a failure, start asserting:

* `response.status_code == expected_status`
* `json["error_code"] == expected_error_code`
* `"message" in json`
* `json` **does not** leak e.g. raw stacktrace.

### 6.2 Users tests

* Bad login:

  * Hit `/users/login` with wrong password.
  * Expect:

    * 401
    * `error_code="UNAUTHORIZED"` or `"INVALID_CREDENTIALS"` depending on design.
* Non-admin hitting admin endpoint:

  * e.g., `/admin/users` as regular user.
  * Expect 403 + `error_code="FORBIDDEN"`.

### 6.3 Rooms tests

* Create room with invalid capacity:

  * `capacity=-1`
  * Expect 400 + `error_code="INVALID_CAPACITY"` or `VALIDATION_ERROR`.
* Non-admin create room:

  * 403 + `error_code="FORBIDDEN"`.

### 6.4 Bookings tests

* Time range invalid:

  * `start_time >= end_time`.
  * 400 + `error_code="INVALID_TIME_RANGE"` or `VALIDATION_ERROR`.
* Conflict booking:

  * Two bookings on same room/time.
  * Second returns 409 + `error_code="BOOKING_CONFLICT"`.
* Non-owner cancel:

  * 403 + `error_code="FORBIDDEN"` or `"NOT_OWNER"`.

### 6.5 Reviews tests

* Rating 0 or 6:

  * 400 + `error_code="INVALID_RATING"`.
* Unauthenticated create:

  * No token.
  * 401 + `error_code="UNAUTHORIZED"`.
* Non-owner update:

  * 403 + `error_code="FORBIDDEN"` or `"NOT_OWNER"`.

This is where you really “lock in” the error contract.

---

## 7️⃣ Postman – add error examples per service

Update `postman/SmartMeetingRoom.postman_collection.json`:

For each service folder, pick at least 1–2 key endpoints and save an **Error Example** response.

### Users

* For `/users/login`:

  * Example “Invalid credentials”:

    * Status: 401
    * Body:

      ```json
      {
        "error_code": "INVALID_CREDENTIALS",
        "message": "Incorrect username or password.",
        "details": null
      }
      ```

* For an admin-only endpoint:

  * Example of regular user calling it, 403.

### Rooms

* For `/rooms` (create):

  * Invalid capacity example:

    * 400 + `INVALID_CAPACITY`.

### Bookings

* For `/bookings`:

  * Overlapping booking:

    * 409 + `BOOKING_CONFLICT` with sample `details`.

* For `/bookings/{id}/cancel`:

  * Non-owner:

    * 403 + `NOT_OWNER`.

### Reviews

* For `/reviews`:

  * `rating=6` example:

    * 400 + `INVALID_RATING`.

In the **description** of each endpoint in Postman, add a line:

> “On error, this endpoint returns the standard error schema `{ error_code, message, details }`. See documentation for error codes.”

---

## 8️⃣ Sphinx – `error_validation.rst` + small tweaks in service docs

### 8.1 Create / complete `docs/source/error_validation.rst`

Structure idea:

```rst
Error Handling and Validation
=============================

Standard Error Schema
---------------------

All services return errors using the same JSON structure:

.. code-block:: json

   {
     "error_code": "BOOKING_CONFLICT",
     "message": "Room is already booked in this time range.",
     "details": {
       "room_id": 3,
       "start_time": "...",
       "end_time": "..."
     }
   }

Error Types
-----------

.. list-table::
   :header-rows: 1

   * - Exception
     - HTTP Status
     - Default error_code
     - Description
   * - BadRequestError
     - 400
     - VALIDATION_ERROR
     - Input validation errors, ...
   * - UnauthorizedError
     - 401
     - UNAUTHORIZED
     - Missing/invalid credentials, ...
   * - ForbiddenError
     - 403
     - FORBIDDEN
     - Insufficient permissions, ...
   * - NotFoundError
     - 404
     - *_NOT_FOUND
     - Resource not found, ...
   * - ConflictError
     - 409
     - BOOKING_CONFLICT
     - Overlapping bookings, ...


Validation by Service
---------------------

Users
~~~~~
- Username/email uniqueness.
- Password length constraints.
- Invalid login → UnauthorizedError (401, INVALID_CREDENTIALS).

Rooms
~~~~~
- capacity > 0.
- Room not found → NotFoundError (404, ROOM_NOT_FOUND).

Bookings
~~~~~~~~
- start_time < end_time.
- Room/user existence.
- Overlapping bookings → ConflictError (409, BOOKING_CONFLICT).

Reviews
~~~~~~~
- rating in [1..5].
- comment max length and HTML sanitization.
- Non-owner update/delete → ForbiddenError (...).

Sanitization
------------

Reviews service sanitizes the `comment` field by stripping HTML tags and
collapsing whitespace to reduce risk of script injection.
```

(You’ll adapt to your exact naming, but that’s the shape.)

### 8.2 Update each service doc

In:

* `docs/source/users_service.rst`
* `docs/source/rooms_service.rst`
* `docs/source/bookings_service.rst`
* `docs/source/reviews_service.rst`

Add a small section like:

```rst
Error Handling and Validation
-----------------------------

This service uses the shared error schema described in
:doc:`error_validation`.

Typical error codes include:

- INVALID_CREDENTIALS, USER_ALREADY_EXISTS (Users)
- INVALID_CAPACITY, ROOM_NOT_FOUND (Rooms)
- INVALID_TIME_RANGE, BOOKING_CONFLICT (Bookings)
- INVALID_RATING, REVIEW_NOT_FOUND (Reviews)
```

Just a few lines per service, no need to repeat the big table.
