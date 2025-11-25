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

Rooms Service
-------------

The Rooms service is responsible for storing and exposing meeting room metadata,
including capacity, equipment, and location. It provides filtered search for
rooms and a status endpoint that can be combined with booking information from
the Bookings service to determine availability.

