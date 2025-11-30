Bookings Service
================

Overview
--------

The **Bookings** service is responsible for managing reservations of
meeting rooms. It owns the lifecycle of a booking:

* creation
* update (change time window or room)
* cancellation by the booking owner
* force-cancellation / conflict resolution by admins

The service never trusts raw IDs coming from clients. Instead, it:

* validates the user via the Users service (service-to-service call),
* validates the room via the Rooms service,
* enforces a **no–overlapping-confirmed-bookings** rule per room and
  time interval.

Roles and responsibilities
--------------------------

Regular user
~~~~~~~~~~~~

A regular authenticated user can:

* create a booking for an available room.
* view only **his/her own** bookings.
* update his/her own booking (e.g., change time window).
* cancel his/her own booking.

Facility Manager / Auditor
~~~~~~~~~~~~~~~~~~~~~~~~~~

Facility managers and auditors can:

* list **all** bookings in the system for monitoring and planning.
* inspect bookings per room or per user (read-only).

Administrator
~~~~~~~~~~~~~

Administrators can do everything above, plus:

* force-cancel any booking (even if it conflicts with another one).
* optionally perform conflict-resolution operations such as
  re-scheduling a booking.

Endpoints summary
-----------------

Public endpoints (regular user)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* ``GET /bookings/my``  
  Return the list of bookings that belong to the current user.

* ``POST /bookings``  
  Create a new booking for a specific room and time window.  
  Request body includes:

  - ``room_id``
  - ``start_time`` (ISO-8601)
  - ``end_time`` (ISO-8601)
  - optional ``title`` / ``notes``

* ``PUT /bookings/{booking_id}``  
  Update a booking owned by the current user (time window, room, or
  metadata). Fails with ``403`` if the booking does not belong to the
  caller.

* ``POST /bookings/{booking_id}/cancel``  
  Cancel a booking owned by the current user. Marks the booking as
  ``cancelled`` but keeps it in history.

Administrative endpoints
~~~~~~~~~~~~~~~~~~~~~~~~

* ``GET /bookings``  
  List all bookings in the system. Accessible to admins, facility
  managers, and auditors.

* ``POST /bookings/{booking_id}/force-cancel``  
  Admin-only endpoint. Force-cancels an existing booking regardless of
  its current state. This is used to resolve conflicts or free rooms in
  exceptional situations.

* ``GET /bookings/check-availability``  
  Check if a given room is free for a specific time window. Returns a
  flag and optionally a list of conflicting bookings.

Booking lifecycle and status
----------------------------

Each booking has a **status** field:

* ``pending`` – (optional) used if you later implement multi-step
  approval flows.
* ``confirmed`` – normal active booking state.
* ``cancelled`` – booking has been cancelled by its owner or by an
  administrator.

For Commit 5, user-created bookings can directly enter the
``confirmed`` state as long as there is no conflict. Admins may
force-cancel a ``confirmed`` booking at any time.

Conflict detection
------------------

For a given room, the service must prevent two **confirmed** bookings
from overlapping in time.

A simplified conflict rule:

*Bookings A and B conflict if:*

* they refer to the same ``room_id``, and
* their time intervals overlap
  (``A.start_time < B.end_time`` **and**
  ``B.start_time < A.end_time``).

On create / update:

* if a conflicting **confirmed** booking exists and the caller is not
  using an admin override, the service returns HTTP ``409 Conflict``.
* if the caller is an admin using a force operation, the service is
  allowed to cancel or modify the conflicting booking.

Inter-service communication
---------------------------

The Bookings service talks to other services via HTTP calls using a
dedicated **service account**:

* **Users service**

  - Validate that the ``user_id`` from the JWT still exists.
  - Inspect the user role to decide whether admin-only endpoints are
    allowed.

* **Rooms service**

  - Ensure that the ``room_id`` exists.
  - Ensure that the room is in an ``active`` state before confirming a
    booking.

These calls are implemented through thin client modules
(e.g. ``users_client`` and ``rooms_client``) which hide the HTTP details
and use a shared ``ServiceHTTPClient`` abstraction from ``common``.

Documentation notes
-------------------

The actual Python implementation of the Bookings service (routers,
schemas, business logic, repository) will include detailed docstrings
describing:

* how a booking is created and validated,
* how conflicts are detected,
* when and how admins can override conflicts.

This ``bookings_service.rst`` file summarises the behaviour at a high
level and will be complemented by Sphinx autodoc for the corresponding
modules.

Error Handling and Validation
-----------------------------

This service uses the shared error schema (:doc:`error_validation`).
Typical error codes include:

* ``INVALID_TIME_RANGE``
* ``ROOM_NOT_FOUND`` / ``USER_NOT_FOUND`` / ``ROOM_INACTIVE``
* ``BOOKING_CONFLICT``
* ``NOT_OWNER`` (for non-owner update/cancel)

Notifications (Part II)
---------------------------------

When a booking is created or cancelled, the Bookings service triggers an
email notification through a third-party provider (SendGrid). The service
uses internal HTTP clients to fetch the user's email address from the Users
service and the room name from the Rooms service, using a service-account
token.

Notification sending is implemented in ``common.notifications`` and is
controlled by configuration options (``NOTIFICATIONS_ENABLED``,
``SENDGRID_API_KEY``, ``SENDGRID_FROM_EMAIL``). Failures in the external
provider are logged but do not affect the success of the booking operation.
If enabled, these failures would surface as a ``NOTIFICATION_FAILED`` error
with a standardized ``{error_code, message, details}`` response.

