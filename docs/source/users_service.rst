Users Service
=============

.. note::

   This page is a documentation placeholder for the Users service. It
   will later include detailed API documentation, examples, and role
   matrices once the service is fully implemented.

Role in the System
------------------

The Users service is responsible for:

* Registering new users (name, username, password, email, role).
* Authenticating users and issuing JWT access tokens.
* Managing user profile information.
* Managing user roles and permissions.
* Providing access to a user's booking history by calling the
  Bookings service over HTTP.

In the codebase, the Users service will live under
``services/users`` and will be implemented using FastAPI, Pydantic
models, and SQLAlchemy ORM models defined in :mod:`db.schema`.

Error Handling and Validation
-----------------------------

This service uses the shared error schema (:doc:`error_validation`).
Typical error codes include:

- ``INVALID_CREDENTIALS`` / ``UNAUTHORIZED``
- ``USER_ALREADY_EXISTS``
- ``USER_NOT_FOUND``
