Deployment & Docker Setup
=========================

Overview
--------

This project is deployed as five Docker containers that run together on a shared
Docker network:

- One PostgreSQL database container.
- Four FastAPI microservices: Users, Rooms, Bookings, and Reviews.

Each service reads its configuration (database URL, other service URLs, JWT
secrets, etc.) from environment variables via ``common.config.Settings``.

Services and Ports
------------------

.. list-table::
   :header-rows: 1
   :widths: 20 30 20

   * - Service
     - Container name
     - Host port
   * - Database
     - ``smart_meeting_room_db``
     - ``5432``
   * - Users
     - ``users_service``
     - ``8001``
   * - Rooms
     - ``rooms_service``
     - ``8002``
   * - Bookings
     - ``bookings_service``
     - ``8003``
   * - Reviews
     - ``reviews_service``
     - ``8004``

Running the Stack
-----------------

To build and start all containers:

.. code-block:: bash

   docker-compose up --build

This command starts:

- PostgreSQL on port ``5432``.
- Users service on ``http://localhost:8001``.
- Rooms service on ``http://localhost:8002``.
- Bookings service on ``http://localhost:8003``.
- Reviews service on ``http://localhost:8004``.

To stop all containers:

.. code-block:: bash

   docker-compose down

Inter-Service Communication
---------------------------

Inside the Docker network, services communicate using container names instead of
``localhost``. For example:

- Users service URL: ``http://users-service:8001``
- Rooms service URL: ``http://rooms-service:8002``
- Bookings service URL: ``http://bookings-service:8003``
- Reviews service URL: ``http://reviews-service:8004``

These URLs are injected through environment variables (e.g.
``USERS_SERVICE_URL``, ``ROOMS_SERVICE_URL``, etc.) and loaded by
``common.config.Settings``. The HTTP clients in each service (e.g.
``users_client``, ``rooms_client``, ``bookings_client``) use these URLs for
inter-service calls with the ``service_account`` role.

Testing with Docker & Postman
-----------------------------

With the stack running, all Postman requests target the Docker ports:

- ``{{users_base_url}} = http://localhost:8001``
- ``{{rooms_base_url}} = http://localhost:8002``
- ``{{bookings_base_url}} = http://localhost:8003``
- ``{{reviews_base_url}} = http://localhost:8004``

We validated the system end-to-end by:

- Registering and logging in users (Users service).
- Creating rooms as admin (Rooms service).
- Creating and viewing bookings (Bookings service).
- Submitting and retrieving reviews (Reviews service).

Screenshots of these Postman calls are included in the final report.

Notes for Profiling
-------------------

For performance profiling, we run pytest with coverage and use Postman / command
line timing against the Dockerized services. Details and target endpoints are
documented in ``profiling/notes.md``.
