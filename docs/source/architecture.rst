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
