## Latest Changes (Nov 25, 2025)

### Project Reset
- Removed local SQLite test databases (`test_bookings_api.db`, `test_bookings_core.db`, `test_rooms.db`, `test_users.db`) to start fresh.
- Re-ran `python -m db.init_db` to recreate the schema against the configured Postgres instance.

### Booking Service
- Hardened `booking_service.create_booking()` to ensure both the user and room exist before checking conflicts. This prevents DB-level foreign key violations.
- Added new service-layer tests covering invalid time ranges, nonexistent entities, cross-room updates, conflict detection, and cancellation permissions (`services/bookings/tests/test_booking_services.py`).
- Expanded endpoint tests for `/bookings` to cover listing, updates, deletion, conflict responses, and bookings for missing rooms (`services/bookings/tests/test_booking_endpoints.py`).

### Rooms Service
- Added helper `_create_room` in tests to make setup cleaner.
- Introduced new endpoint tests verifying that facility managers can update/delete rooms while regular users are blocked (`services/rooms/tests/test_rooms_endpoints.py`).

### Users Service
- Added regression tests ensuring profile updates reject duplicate usernames/emails and that admin role changes surface validation errors properly (`services/users/tests/test_user_endpoint.py`).

### Tooling / Docs
- Updated Postman collection (`postman/SmartMeetingRoom.postman_collection.json`) so booking requests match actual API routes (corrected cancel/update bodies, admin override paths, etc.).

### Commands
- Run service-specific test suites:
  - `pytest services/bookings/tests -vv`
  - `pytest services/rooms/tests -vv`
  - `pytest services/users/tests -vv`
