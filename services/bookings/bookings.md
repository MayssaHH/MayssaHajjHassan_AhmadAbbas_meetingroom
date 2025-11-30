# Bookings Service Documentation

## Overview
The Bookings service manages room reservations: create/update/cancel bookings for users, detect conflicts, and provide admin overrides. All endpoints use the shared error schema `{error_code, message, details}`.

## Endpoints
Base URL: `http://bookings-service:8003` (container) or `http://localhost:8003` (local). JWT required unless noted.

### Health
- `GET /health` → `{ "status": "ok", "service": "bookings" }`

### Create Booking (User)
- `POST /bookings/`
  - Access: any authenticated user.
  - Input (JSON):
    ```json
    {
      "room_id": 1,
      "start_time": "2025-01-01T10:00:00Z",
      "end_time": "2025-01-01T11:00:00Z"
    }
    ```
  - Output: `201` Booking object.
  - Errors: `INVALID_TIME_RANGE`, `ROOM_NOT_FOUND`, `ROOM_INACTIVE`, `USER_NOT_FOUND`, `BOOKING_CONFLICT`, `UNAUTHORIZED`, `FORBIDDEN`.

### List My Bookings
- `GET /bookings/me`
  - Access: authenticated user.
  - Query (optional): `offset`, `limit`.
  - Output: `200` list of bookings owned by caller.

### Update My Booking
- `PUT /bookings/{booking_id}`
  - Access: owner or admin; regular users only on their own bookings.
  - Input: start/end times required.
  - Output: `200` updated booking.
  - Errors: `BOOKING_NOT_FOUND`, `NOT_OWNER`, `BOOKING_CONFLICT`, `INVALID_TIME_RANGE`.

### Cancel My Booking
- `DELETE /bookings/{booking_id}`
  - Access: owner.
  - Output: `204` (status set to `cancelled`).
  - Errors: `BOOKING_NOT_FOUND`, `NOT_OWNER`.

### Check Availability
- `GET /bookings/check-availability`
  - Access: authenticated (used by other services).
  - Query: `room_id`, `start_time`, `end_time`.
  - Output: `200` `{ "room_id": ..., "available": true/false }`.
  - Errors: `INVALID_TIME_RANGE`, `ROOM_NOT_FOUND`, `ROOM_INACTIVE`.

### List All Bookings (Admin/FM/Auditor/Service Account)
- `GET /admin/bookings/`
  - Access: `admin`, `facility_manager`, `auditor`, `service_account`.
  - Query (optional): `offset`, `limit`.
  - Output: `200` list of all bookings.

### Create Booking with Override (Admin)
- `POST /admin/bookings/override`
  - Access: `admin`.
  - Input: same as create; conflicts are force-cancelled first.
  - Output: `201` booking.
  - Errors: `INVALID_TIME_RANGE`, `ROOM_NOT_FOUND`, `ROOM_INACTIVE`.

### Force-Cancel Booking (Admin)
- `POST /admin/bookings/{booking_id}/force-cancel`
  - Access: `admin`.
  - Output: `200` cancelled booking.
  - Errors: `BOOKING_NOT_FOUND`.

### List Bookings by User (Admin/FM/Auditor/Service Account)
- `GET /admin/bookings/user/{user_id}`
  - Access: `admin`, `facility_manager`, `auditor`, `service_account`.
  - Query (optional): `offset`, `limit`.
  - Output: `200` list of bookings for the user.

### List Bookings by User and Room (Admin/FM/Auditor/Service Account)
- `GET /admin/bookings/user/{user_id}/room/{room_id}`
  - Access: `admin`, `facility_manager`, `auditor`, `service_account`.
  - Output: `200` list of bookings for the user filtered to room.

## Auth & Roles
- JWT via `Authorization: Bearer <token>`.
- Roles: `admin`, `facility_manager`, `auditor`, `regular`, `service_account`.
- Regular users: only their own bookings; no overrides.
- Admin: full override/cancel/list-all.
- Facility Manager/Auditor: read all bookings; no overrides.
- Service Account: read endpoints for inter-service use.

## Data Model
- Fields:
  - `id`: int
  - `user_id`: int
  - `room_id`: int
  - `start_time`: datetime (UTC normalized)
  - `end_time`: datetime (UTC normalized)
  - `status`: `confirmed` or `cancelled`
  - `created_at`: datetime

## Validation & Errors
- Time range: `start_time < end_time`, duration between 5 minutes and 24 hours, UTC normalization.
- Room must exist and be `active`; user must exist.
- Conflict detection: overlapping confirmed bookings in same room → `BOOKING_CONFLICT`.
- Ownership: non-owner update/cancel → `NOT_OWNER`.
- Standard error schema examples:
  ```json
  {
    "error_code": "BOOKING_CONFLICT",
    "message": "The room is already booked in the requested time range.",
    "details": { "room_id": 1 }
  }
  ```
- Common error codes: `INVALID_TIME_RANGE`, `BOOKING_CONFLICT`, `BOOKING_NOT_FOUND`, `ROOM_NOT_FOUND`, `ROOM_INACTIVE`, `USER_NOT_FOUND`, `NOT_OWNER`, `FORBIDDEN`, `UNAUTHORIZED`, `INTERNAL_ERROR`.

## Error Handling
- Global handlers map `AppError`/HTTP exceptions to standard error JSON; logging via `common.logging_utils.log_error`.

## Service Internals (quick map)
- Schemas: `services/bookings/app/schemas.py` (create/update/read models).
- Repository: `services/bookings/app/repository/booking_repository.py` (CRUD, conflicts, pagination).
- Service layer: `services/bookings/app/service_layer/booking_service.py` (validation, conflicts, overrides, availability).
- Routers: `services/bookings/app/routers/bookings_routes.py` (user endpoints) and `admin_routes.py` (admin/FM/auditor/service account).
- Dependencies: `services/bookings/app/dependencies.py` (JWT decode, role guards).
