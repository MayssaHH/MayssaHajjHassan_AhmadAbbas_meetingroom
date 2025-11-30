# Rooms Service Documentation

## Overview
The Rooms service manages meeting room metadata and exposes room-related APIs to clients and other services. It supports creation, updates, deletion, listing with filters, and status checks (including a dynamic availability flag via the Bookings service). All endpoints use a shared error schema `{error_code, message, details}`.

## Endpoints
All endpoints require a valid JWT (see Auth/Roles below). Base URL defaults to `http://rooms-service:8002` (container) or `http://localhost:8002` (local).

### Health
- `GET /health`
  - Returns `{ "status": "ok" }`.

### Create Room
- `POST /rooms`
  - Roles: `admin` or `facility_manager`.
  - Body:
    ```json
    {
      "name": "Room Alpha",
      "location": "HQ",
      "capacity": 10,
      "equipment": ["projector", "whiteboard"],
      "status": "active"
    }
    ```
  - Responses:
    - `201` with room payload.
    - Errors: `FORBIDDEN`, `ROOM_ALREADY_EXISTS`, `VALIDATION_ERROR`.

### List Rooms
- `GET /rooms`
  - Roles: any authenticated user (admin, facility_manager, regular, auditor, moderator).
  - Query params (optional):
    - `min_capacity`: int
    - `location`: str (case-insensitive exact match)
    - `equipment`: str (substring match)
    - `equipment_list`: repeated tokens (all must match)
    - `offset`, `limit`: pagination
  - Responses:
    - `200` list of rooms.
    - Errors: auth errors (`UNAUTHORIZED`, `FORBIDDEN`).

### List Rooms
- `GET /rooms`
  - Roles: any authenticated user (admin, facility_manager, regular, auditor, moderator).
  - Query params (optional):
    - `min_capacity`: int
    - `location`: str (case-insensitive exact match)
    - `equipment`: str (substring match)
    - `equipment_list`: repeated tokens (all must match)
    - `offset`, `limit`: pagination
  - Responses:
    - `200` list of rooms.
    - Errors: auth errors (`UNAUTHORIZED`, `FORBIDDEN`).

### Get Room by ID
- `GET /rooms/{room_id}`
  - Roles: any authenticated user.
  - Responses:
    - `200` room payload.
    - `404 ROOM_NOT_FOUND`.

### Update Room
- `PUT /rooms/{room_id}`
  - Roles: `admin` or `facility_manager`.
  - Body: any subset of `name`, `location`, `capacity`, `equipment`, `status` (`active` or `out_of_service`).
  - Responses:
    - `200` updated room.
    - Errors: `ROOM_NOT_FOUND`, `ROOM_ALREADY_EXISTS` (name clash), `FORBIDDEN`.

### Delete Room
- `DELETE /rooms/{room_id}`
  - Roles: `admin` or `facility_manager`.
  - Responses:
    - `204` on success.
    - Errors: `ROOM_NOT_FOUND`, `FORBIDDEN`.

### Room Status (Static + Dynamic)
- `GET /rooms/{room_id}/status`
  - Roles: any authenticated user.
  - Query params (optional): `start_time`, `end_time` (ISO 8601). Defaults to now..now+5m.
  - Response:
    ```json
    {
      "room_id": 1,
      "static_status": "active",
      "is_currently_booked": false
    }
    ```
  - Dynamic availability is determined via the Bookings service (`/bookings/check-availability`); if the downstream check fails and fallback is enabled, it returns `false`.
  - Errors: `ROOM_NOT_FOUND`, auth errors.

## Auth & Roles
- JWT required; parsed via `Authorization: Bearer <token>`.
- Supported roles: `admin`, `facility_manager`, `regular`, `auditor`, `moderator`, `service_account`.
- Write operations (create/update/delete) restricted to `admin`/`facility_manager`.
- Reads/status allowed for all authenticated roles (including auditors).

## Data Model
- Fields:
  - `id`: int
  - `name`: str (unique, case-insensitive)
  - `location`: str
  - `capacity`: int (>=1)
  - `equipment`: list[str] exposed; stored as CSV
  - `status`: `active` | `out_of_service`
  - `created_at`: datetime

## Validation & Errors
- Name uniqueness (case-insensitive).
- Capacity enforced via schema (>=1).
- Status restricted to enum values.
- Standard error schema returned everywhere:
  ```json
  {
    "error_code": "ROOM_NOT_FOUND",
    "message": "Room not found.",
    "details": null
  }
  ```
- Common error codes: `ROOM_ALREADY_EXISTS`, `ROOM_NOT_FOUND`, `INVALID_CAPACITY` (422/400), `FORBIDDEN`, `UNAUTHORIZED`, `VALIDATION_ERROR`, `INTERNAL_ERROR`.

## Inter-Service Calls
- Bookings service used for availability checks:
  - Client: `services.rooms.app.clients.bookings_client.is_room_currently_booked(room_id, start_time, end_time)`
  - Auth: service-account JWT
  - Endpoint called: `/bookings/check-availability`
  - Fallback: returns `False` if downstream is unavailable and `client_stub_fallback` is enabled.

## Error Handling
- Global exception handlers map `AppError`/HTTP exceptions to the standard error JSON.
- Errors are logged via `common.logging_utils.log_error`.

## Notes for Consumers
- Always include a Bearer token.
- Use trailing slashless paths except where defined (`/rooms` is fine without a trailing slash).
- Expect consistent error payloads for all failures.

## Permissions Matrix (summarized)
- Admin: create/update/delete, list/get, status.
- Facility Manager: create/update/delete, list/get, status.
- Regular: list/get, status.
- Auditor/Moderator: list/get, status.
- Service Account: intended for inter-service calls (read/status).

## Validation Rules
- `capacity` must be >= 1.
- `status` must be `active` or `out_of_service`.
- `name` unique (case-insensitive), trimmed of whitespace.
- `equipment` stored as CSV, exposed as list.

## Error Codes (common)
- `ROOM_ALREADY_EXISTS`, `ROOM_NOT_FOUND`
- `INVALID_CAPACITY`, `VALIDATION_ERROR`
- `FORBIDDEN`, `UNAUTHORIZED`
- `INTERNAL_ERROR`

## Example Error Response
```json
{
  "error_code": "ROOM_NOT_FOUND",
  "message": "Room not found.",
  "details": null
}
```

## Service Internals (quick map)
- Schemas: `services/rooms/app/schemas.py` (Pydantic, equipment list<->CSV, status enum).
- Repository: `services/rooms/app/repository/rooms_repository.py` (CRUD, filters, pagination).
- Service layer: `services/rooms/app/service_layer/rooms_service.py` (validation, normalization, availability call).
- Router: `services/rooms/app/routers/rooms_routes.py` (RBAC, endpoints).
- Client to Bookings: `services/rooms/app/clients/bookings_client.py` (service-account auth + retry/fallback).
- Global error handler: `services/rooms/app/main.py` (maps exceptions to standard error JSON).
