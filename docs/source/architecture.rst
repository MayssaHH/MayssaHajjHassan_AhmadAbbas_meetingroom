System Architecture
===================

.. note::

   This page is a placeholder created in Commit 2. It will be expanded
   in later commits with diagrams and detailed explanations.

Overview
--------

The Smart Meeting Room backend is designed as a small microservice
ecosystem built around four main services:

* **Users service** – manages accounts, authentication, and roles.
* **Rooms service** – manages room inventory and static room data.
* **Bookings service** – manages time-based reservations of rooms.
* **Reviews service** – manages user feedback and moderation.

All services share a common relational database schema (implemented in
``db.schema``) and communicate with each other over HTTP using
well-defined APIs and a dedicated ``service_account`` user.

For detailed documentation on each service, see the individual service pages:

* :doc:`users_service` - User accounts, authentication, and roles
* :doc:`rooms_service` - Room inventory and metadata
* :doc:`bookings_service` - Time-based room reservations
* :doc:`reviews_service` - User feedback and moderation

API Versioning
--------------

All business endpoints are versioned under the ``/api/v1/`` prefix:

* **Users service**: ``/api/v1/users/*``
* **Rooms service**: ``/api/v1/rooms/*``
* **Bookings service**: ``/api/v1/bookings/*``, ``/api/v1/admin/bookings/*``
* **Reviews service**: ``/api/v1/reviews/*``, ``/api/v1/admin/reviews/*``

Health check endpoints remain unversioned and are accessible at the root level:

* ``GET /health`` - Returns service health status

Future breaking changes will be introduced under ``/api/v2/``, allowing clients
to migrate gradually while maintaining backward compatibility with v1 endpoints.

Deployment View
---------------

The system is deployed as five Docker containers (database + four services).
For details on ports, container names, and how to run the stack, see
:doc:`deployment_docker`.


