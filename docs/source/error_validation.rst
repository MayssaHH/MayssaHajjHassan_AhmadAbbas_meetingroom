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
     - Input validation failures (invalid time ranges, capacity, rating, etc.).
   * - UnauthorizedError
     - 401
     - UNAUTHORIZED
     - Missing or invalid credentials.
   * - ForbiddenError
     - 403
     - FORBIDDEN
     - Authenticated but lacking permissions/role or not the owner.
   * - NotFoundError
     - 404
     - *_NOT_FOUND
     - Requested resource does not exist.
   * - ConflictError
     - 409
     - BOOKING_CONFLICT
     - State conflicts such as overlapping bookings.
   * - InternalServerError
     - 500
     - INTERNAL_ERROR
     - Catch-all unexpected server errors.

Validation by Service
---------------------

Users
~~~~~
- Case-insensitive username/email uniqueness.
- Password strength/lockout.
- Invalid login → UnauthorizedError (401, INVALID_CREDENTIALS).

Rooms
~~~~~
- capacity > 0 (via schemas), name uniqueness; Room not found → NotFoundError (ROOM_NOT_FOUND).

Bookings
~~~~~~~~
- start_time < end_time with min/max duration, UTC normalized.
- Room/user existence and room active.
- Overlapping bookings → ConflictError (BOOKING_CONFLICT).
- Non-owner updates/cancels → ForbiddenError (NOT_OWNER).

Reviews
~~~~~~~
- rating in [1..5], comment length + sanitization/profanity check.
- Non-owner update/delete → ForbiddenError (NOT_OWNER).
- Review not found → NotFoundError.

Sanitization
------------

The Reviews service sanitizes ``comment`` by stripping HTML tags and
collapsing whitespace to reduce the risk of script injection.
