Rooms Service
=============

Overview
--------

The **Rooms service** is responsible for managing meeting room metadata and
exposing room-related information to other services and clients. It does not
perform the booking logic itself, but it cooperates with the Bookings service
to report availability and status.

Responsibilities
----------------

The main responsibilities of the Rooms service are:

* Create and manage meeting rooms (name, capacity, equipment, location).
* Mark rooms as active or out-of-service.
* Expose searchable lists of rooms (filter by capacity, location, equipment).
* Expose detailed information for a single room.
* Provide a status endpoint that indicates if a room is active and whether it is
  currently booked for a given time range (in coordination with the Bookings
  service later).

API Endpoints (design)
----------------------

The following endpoints are planned for the Rooms service. The exact request and
response bodies will be finalized together with the implementation:

* ``POST /rooms``  
  Create a new room. Restricted to **admin** or **facility manager** roles.

* ``PUT /rooms/{room_id}``  
  Update an existing room's details (capacity, equipment, location, status).
  Restricted to **admin** or **facility manager** roles.

* ``DELETE /rooms/{room_id}``  
  Delete an existing room. Restricted to **admin** or **facility manager** roles.

* ``GET /rooms``  
  Retrieve a list of rooms with optional filters:
  
  * ``capacity`` (minimum capacity)
  * ``location`` (exact or partial match)
  * ``equipment`` (contains specific equipment tags)

  Accessible to any authenticated user.

* ``GET /rooms/{room_id}``  
  Retrieve detailed information about a single room by its identifier.
  Accessible to any authenticated user.

* ``GET /rooms/{room_id}/status``  
  Retrieve the current status of a room. The response should include:

  * Static status: e.g. ``"active"`` or ``"out_of_service"``.
  * Dynamic status: e.g. ``"booked"`` or ``"available"`` for the requested time
    interval (later provided via the Bookings service).

  Accessible to any authenticated user.

Roles and Permissions
---------------------

At a high level, the permissions for this service are:

* **Admin**:
  * Full control over rooms: create, update, delete.
  * Can view all rooms and their statuses.

* **Facility Manager**:
  * Same room management abilities as admin (create, update, delete).
  * Intended for operational management of physical spaces.

* **Regular User**:
  * Can list rooms and search using filters.
  * Can view details and status of specific rooms.

* **Auditor / Read-only**:
  * Can read room information and statuses.
  * Has no write access.

Inter-Service Communication
---------------------------

The Rooms service may contact the **Bookings service** to compute dynamic
availability or to verify whether a room is booked during a specific time
window. This is typically done through a dedicated technical account
(*service account*) and secured inter-service APIs.

Error Handling and Validation
-----------------------------

This service uses the shared error schema (:doc:`error_validation`).
Typical error codes include:

* ``INVALID_CAPACITY``
* ``ROOM_ALREADY_EXISTS``
* ``ROOM_NOT_FOUND``
