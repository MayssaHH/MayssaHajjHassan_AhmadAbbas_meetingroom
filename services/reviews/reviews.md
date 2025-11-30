# Reviews Service Documentation

## Overview
The Reviews service manages user feedback about rooms. It allows authenticated users to create, update, delete, and list reviews, while moderators/admins can flag/unflag and list flagged reviews. All endpoints return the shared error schema `{error_code, message, details}`.

## Endpoints
Base URL: `http://reviews-service:8004` (container) or `http://localhost:8004` (local). JWT required unless noted.

### Health
- `GET /health` → `{ "status": "ok" }`.

### Create Review
- `POST /reviews`
  - Roles: any authenticated user except auditors (auditors are read-only).
  - Body:
    ```json
    {
      "room_id": 1,
      "rating": 5,
      "comment": "Great room!"
    }
    ```
  - Responses: `201` with review payload; errors: `INVALID_RATING`, `INVALID_COMMENT`, `ROOM_NOT_FOUND`, `USER_NOT_FOUND`, `BOOKING_REQUIRED_FOR_REVIEW` (if enforced), `FORBIDDEN`, `UNAUTHORIZED`.

### List Reviews for a Room
- `GET /reviews/room/{room_id}`
  - Roles: any authenticated user (auditors included).
  - Responses: `200` list of reviews; errors: `UNAUTHORIZED`, `FORBIDDEN`.

### Update Review
- `PUT /reviews/{review_id}`
  - Roles: owner OR admin/moderator.
  - Body: any subset of `rating`, `comment`.
  - Responses: `200` updated review; errors: `REVIEW_NOT_FOUND`, `NOT_OWNER`, `INVALID_RATING`, `INVALID_COMMENT`.

### Delete Review
- `DELETE /reviews/{review_id}`
  - Roles: owner OR admin/moderator.
  - Responses: `204` on success; errors: `REVIEW_NOT_FOUND`, `NOT_OWNER`.

### Flag / Unflag Review (Moderation)
- `POST /reviews/{review_id}/flag`
  - Roles: `moderator` or `admin`.
  - Responses: `200` flagged review; errors: `REVIEW_NOT_FOUND`, `FORBIDDEN`.
- `POST /reviews/{review_id}/unflag`
  - Roles: `moderator` or `admin`.
  - Responses: `200` unflagged review; errors: `REVIEW_NOT_FOUND`, `FORBIDDEN`.

### List Flagged Reviews
- `GET /reviews/flagged`
  - Roles: `moderator` or `admin`.
  - Responses: `200` list; errors: `FORBIDDEN`.

### List All Reviews (Admin)
- `GET /admin/reviews`
  - Roles: `admin`.
  - Responses: `200` list of all reviews (regardless of flag/visibility); errors: `FORBIDDEN`, `UNAUTHORIZED`.

## Auth & Roles
- JWT required via `Authorization: Bearer <token>`.
- Roles: `admin`, `moderator`, `regular`, `auditor`, `facility_manager`, `service_account`.
- Auditors: read-only; cannot create reviews.
- Moderators/Admins: can flag/unflag and override ownership checks.

## Data Model
- Fields:
  - `id`: int
  - `user_id`: int (owner)
  - `room_id`: int
  - `rating`: int (1–5)
  - `comment`: str (sanitized)
  - `is_flagged`: bool
  - `created_at`: datetime

## Validation & Errors
- `rating` must be between 1 and 5.
- `comment` sanitized: HTML tags stripped, whitespace collapsed; basic profanity check.
- Optional rule: require prior booking (`require_booking_for_review` flag).
- Standard error schema examples:
  ```json
  {
    "error_code": "INVALID_RATING",
    "message": "rating must be between 1 and 5.",
    "details": null
  }
  ```
- Common error codes: `INVALID_RATING`, `INVALID_COMMENT`, `REVIEW_NOT_FOUND`, `NOT_OWNER`, `FORBIDDEN`, `UNAUTHORIZED`, `INTERNAL_ERROR`.

## Inter-Service Calls
- Users: ensure reviewer exists.
- Rooms: ensure room exists and is active.
- Bookings: optionally ensure user has a booking for the room.
- Auth: service-account JWT used for these validations; fallback allowed if configured.

## Error Handling
- Global handlers map `AppError`/HTTP exceptions to the standard error JSON; logging via `common.logging_utils.log_error`.

## Notes for Consumers
- Always include Bearer token (except `/health`).
- Auditors may read but cannot create.
- Moderators/Admins can flag/unflag and bypass ownership for moderation actions.

## Service Internals (quick map)
- Schemas: `services/reviews/app/schemas.py` (rating bounds, comment length).
- Repository: `services/reviews/app/repository/reviews_repository.py` (CRUD, list by room, list flagged).
- Service layer: `services/reviews/app/service_layer/reviews_service.py` (sanitization, validation, booking check).
- Routers: `services/reviews/app/routers/reviews_routes.py` (user CRUD) and `moderation_routes.py` (flag/unflag/list flagged).
- Dependencies: `services/reviews/app/dependencies.py` (JWT decode, role guards, read access).
- Clients: `services/reviews/app/clients/*.py` (Users/Rooms/Bookings via service-account).
