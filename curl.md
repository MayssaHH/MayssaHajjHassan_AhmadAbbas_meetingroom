# Manual cURL/Invoke-RestMethod Checks

Environment: running containers `users_service` (8001), `rooms_service` (8002), `bookings_service` (8003), `reviews_service` (8004) against Postgres (`smart_meeting_room_db`).

## Users
- Login existing admin (`admin1`):  
  `POST http://localhost:8001/users/login` body `{"username":"admin1","password":"Password123"}` → 200, returns `access_token` (HS256).
- Login existing regular (`user1`): same endpoint → 200, returns token.
- Registration endpoints return 400 if the user already exists (as expected).

## Rooms
- Create room (admin token):  
  `POST http://localhost:8002/rooms/` with Bearer admin token, body `{"name":"Room Alpha","location":"HQ","capacity":10,"equipment":["projector","whiteboard"],"status":"active"}` → 201, returns room `id=1`.
- List rooms (regular token):  
  `GET http://localhost:8002/rooms` with Bearer user token → 200, includes `Room Alpha`.
- Room status with booking window:  
  `GET http://localhost:8002/rooms/1/status?start_time=...&end_time=...` with Bearer user token → 200, `is_currently_booked:true` when overlapping a booking.

## Bookings
- Create booking (regular token; note trailing slash matters):  
  `POST http://localhost:8003/bookings/` with Bearer user token, body `{"room_id":1,"start_time":"<ISO>","end_time":"<ISO>"}` → 201, status `confirmed`, returns booking `id=1`.
- List my bookings:  
  `GET http://localhost:8003/bookings/me` with Bearer user token → 200, shows booking.
- Admin list all bookings:  
  `GET http://localhost:8003/admin/bookings/` with Bearer admin token → 200, shows booking.

## Reviews
- Create review (regular token):  
  `POST http://localhost:8004/reviews` body `{"room_id":1,"rating":5,"comment":"Great room via curl"}` → 201, returns review `id=2`.
- List reviews for room:  
  `GET http://localhost:8004/reviews/room/1` with Bearer user token → 200, returns reviews.
- Flag review (admin token):  
  `POST http://localhost:8004/reviews/2/flag` with Bearer admin token → 200, `is_flagged:true`.

## Notes / Gotchas Observed
- Hitting booking and room create endpoints requires the trailing slash (`/bookings/`, `/rooms/`) since the route is defined at `/`.
- DB had to be initialized once in the users container: `docker exec users_service python -m db.init_db`.
- Tokens validate across services after `common.auth` leeway fix; earlier 401s were due to truncated tokens and the leeway parameter issue now resolved.
