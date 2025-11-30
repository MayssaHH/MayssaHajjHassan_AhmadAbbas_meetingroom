Reviews Service
===============

Overview
--------

The **Reviews** service is responsible for handling user feedback about meeting rooms.
It exposes APIs that allow authenticated users to:

* Submit a review for a room.
* Update or delete their own reviews.
* Retrieve reviews for a specific room.
* List their own reviews.

In addition, it supports **moderation** features that allow privileged roles
(e.g., moderators and admins) to:

* View and filter reviews (e.g., flagged reviews).
* Flag or unflag reviews that violate policies.
* Hide or restore reviews from public visibility.

All review content is validated and sanitized before being stored to prevent
SQL injection and to reduce the risk of XSS or inappropriate content.

User-facing endpoints
---------------------

The following endpoints are intended for **regular authenticated users**.

* **POST** ``/reviews``

  *Purpose*: Submit a new review for a meeting room.

  *Request body* (JSON):

  - ``room_id`` (int): Identifier of the room being reviewed.
  - ``rating`` (int): Numeric rating in a bounded range (for example 1–5).
  - ``comment`` (string): Free-text comment about the room.

  *Notes*:

  - The user identifier is taken from the authenticated JWT, not from the body.
  - Rating is validated to be within an allowed range.
  - Comment is trimmed and validated for minimum and maximum length.

* **GET** ``/reviews/room/{room_id}``

  *Purpose*: Retrieve all non-hidden reviews for a given room.

  *Access*: Typically available to any authenticated user so that users can
  inspect the quality and feedback of a room.

* **GET** ``/reviews/me``

  *Purpose*: Return the list of reviews created by the current user.

  *Access*: Authenticated user only.

* **PUT** ``/reviews/{review_id}``

  *Purpose*: Allow a user to update their own review (rating and/or comment).

  *Access rules*:

  - Only the **owner** of the review can update it.
  - Administrative roles may optionally be allowed to correct or clean up
    specific reviews depending on the RBAC configuration.

* **DELETE** ``/reviews/{review_id}``

  *Purpose*: Allow a user to delete (soft-delete) their own review.

  *Behavior*: In most cases this is implemented as a **soft delete** by
  marking a status or flag on the review instead of physically removing it
  from the database.

Moderation and admin endpoints
------------------------------

The following endpoints are intended for **moderators and administrators**
responsible for enforcing content rules and dealing with inappropriate reviews.

Typical patterns include:

* **GET** ``/admin/reviews``

  *Purpose*: List reviews for moderation purposes. This can be filtered by
  room, by status, or by whether the review is flagged.

* **GET** ``/admin/reviews/flagged``

  *Purpose*: List only reviews that have been flagged as potentially
  inappropriate.

* **PATCH** ``/admin/reviews/{review_id}/flag``

  *Purpose*: Flag or unflag a review.

  *Behavior*:

  - Setting ``flagged = true`` marks the review as needing moderator attention.
  - Clearing the flag indicates that the review has been checked and is
    acceptable.

* **PATCH** ``/admin/reviews/{review_id}/visibility``

  *Purpose*: Hide or restore a review from public listings.

  *Behavior*:

  - When a review is hidden, it no longer appears in normal room review
    listings, but remains available for audit and moderation.
  - Restoring the review makes it visible again if it no longer violates
    any policy.

Validation and sanitization
---------------------------

The Reviews service applies several layers of validation and sanitization:

* **Pydantic validation** ensures that:

  - ``rating`` is within a strict numeric range (e.g., 1–5).
  - ``comment`` is non-empty (after trimming) and does not exceed the maximum
    allowed length.
  - ``room_id`` and other identifiers are integers and required.

* **Sanitization**:

  - User-provided text is cleaned (for example by trimming whitespace and
    optionally stripping dangerous HTML).
  - All database interactions go through SQLAlchemy with bound parameters,
    which protects against SQL injection.

Authentication and roles
------------------------

All write operations on reviews require a valid JWT access token. The token is
decoded in a shared authentication layer and exposes:

* The **user id** (used to associate the review with its owner).
* The **role** (e.g., regular, moderator, admin).

Access control rules:

* Regular users:

  - Create/update/delete **their own** reviews.
  - View public reviews for rooms.

* Moderators:

  - Access moderation endpoints for flagging/unflagging and hiding/restoring
    reviews.
  - Read reviews in order to apply content policies.

* Admins:

  - Have full moderation capabilities.
  - May additionally view audit information, depending on the overall RBAC
    configuration.
