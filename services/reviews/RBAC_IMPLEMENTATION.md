# RBAC Implementation for Reviews Service

## Overview

The Reviews service implements Role-Based Access Control (RBAC) with two permission levels for moderation:

1. **ADMIN**: Full moderation capabilities
2. **MODERATOR**: Limited moderation capabilities

## Permission Levels

### ADMIN-ONLY Operations

These operations require the `admin` role exclusively:

1. **List All Reviews** - View all reviews in the system regardless of visibility or flag status
2. **Delete Reviews** - Permanently remove reviews from the database (hard delete)
3. **Restore Reviews** - Make hidden reviews visible again

### MODERATOR + ADMIN Operations

These operations are available to both `moderator` and `admin` roles:

1. **Flag Reviews** - Mark reviews as flagged for inappropriate content
2. **Unflag Reviews** - Clear the flagged state from reviews
3. **Hide Reviews** - Temporarily hide reviews from public view
4. **Show Reviews** - Make hidden reviews visible again
5. **View Flagged Reviews** - See all flagged reviews (reports view)

## Implementation Details

### Dependencies (`app/dependencies.py`)

Two dependency functions control access:

1. **`require_admin_only`**: Restricts access to admin role only
   ```python
   def require_admin_only(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
       # Checks if user.role == "admin"
   ```

2. **`require_moderator_or_admin`**: Allows both moderator and admin roles
   ```python
   def require_moderator_or_admin(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
       # Checks if user.role in ["admin", "moderator"]
   ```

### Endpoint Organization

#### Admin Routes (`/admin/reviews/*`)

Located in `app/routers/admin_routes.py`:

**ADMIN-ONLY:**
- `GET /admin/reviews` - List all reviews
- `DELETE /admin/reviews/{review_id}` - Delete review (permanent)
- `POST/PATCH /admin/reviews/{review_id}/restore` - Restore hidden review

**MODERATOR + ADMIN:**
- `POST/PATCH /admin/reviews/{review_id}/flag` - Flag review
- `POST/PATCH /admin/reviews/{review_id}/unflag` - Unflag review
- `POST/PATCH /admin/reviews/{review_id}/hide` - Hide review
- `POST/PATCH /admin/reviews/{review_id}/show` - Show review

#### Moderation Routes (`/reviews/*`)

Located in `app/routers/moderation_routes.py`:

**MODERATOR + ADMIN:**
- `POST /reviews/{review_id}/flag` - Flag review
- `POST /reviews/{review_id}/unflag` - Unflag review
- `GET /reviews/flagged` - List flagged reviews (reports)

## API Endpoints Summary

### Base URL: `http://localhost:8004`

#### ADMIN-ONLY Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/admin/reviews` | List all reviews | Admin only |
| DELETE | `/admin/reviews/{review_id}` | Delete review permanently | Admin only |
| POST/PATCH | `/admin/reviews/{review_id}/restore` | Restore hidden review | Admin only |

#### MODERATOR + ADMIN Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST/PATCH | `/admin/reviews/{review_id}/flag` | Flag review | Moderator + Admin |
| POST/PATCH | `/admin/reviews/{review_id}/unflag` | Unflag review | Moderator + Admin |
| POST/PATCH | `/admin/reviews/{review_id}/hide` | Hide review | Moderator + Admin |
| POST/PATCH | `/admin/reviews/{review_id}/show` | Show review | Moderator + Admin |
| POST | `/reviews/{review_id}/flag` | Flag review (alt path) | Moderator + Admin |
| POST | `/reviews/{review_id}/unflag` | Unflag review (alt path) | Moderator + Admin |
| GET | `/reviews/flagged` | List flagged reviews (reports) | Moderator + Admin |

## Authentication

All endpoints require JWT authentication via Bearer token in the Authorization header:

```
Authorization: Bearer <jwt_token>
```

The JWT token must contain:
- `sub`: User ID
- `username`: Username
- `role`: User role (`admin`, `moderator`, `regular`, etc.)

## Testing with Postman

### Prerequisites

1. Obtain JWT tokens for:
   - An admin user
   - A moderator user
   - A regular user (for negative testing)

2. Start the reviews service:
   ```bash
   uvicorn services.reviews.app.main:app --reload --port 8004
   ```

### Test Scenarios

#### 1. Admin: List All Reviews
- **Method**: GET
- **URL**: `http://localhost:8004/admin/reviews`
- **Headers**: `Authorization: Bearer <admin_token>`
- **Expected**: 200 OK, list of all reviews

#### 2. Admin: Delete Review
- **Method**: DELETE
- **URL**: `http://localhost:8004/admin/reviews/{review_id}`
- **Headers**: `Authorization: Bearer <admin_token>`
- **Expected**: 204 No Content

#### 3. Admin: Restore Review
- **Method**: POST or PATCH
- **URL**: `http://localhost:8004/admin/reviews/{review_id}/restore`
- **Headers**: `Authorization: Bearer <admin_token>`
- **Expected**: 200 OK, restored review

#### 4. Moderator/Admin: Flag Review
- **Method**: POST or PATCH
- **URL**: `http://localhost:8004/admin/reviews/{review_id}/flag`
- **Headers**: `Authorization: Bearer <moderator_or_admin_token>`
- **Expected**: 200 OK, flagged review

#### 5. Moderator/Admin: Unflag Review
- **Method**: POST or PATCH
- **URL**: `http://localhost:8004/admin/reviews/{review_id}/unflag`
- **Headers**: `Authorization: Bearer <moderator_or_admin_token>`
- **Expected**: 200 OK, unflagged review

#### 6. Moderator/Admin: Hide Review
- **Method**: POST or PATCH
- **URL**: `http://localhost:8004/admin/reviews/{review_id}/hide`
- **Headers**: `Authorization: Bearer <moderator_or_admin_token>`
- **Expected**: 200 OK, hidden review

#### 7. Moderator/Admin: Show Review
- **Method**: POST or PATCH
- **URL**: `http://localhost:8004/admin/reviews/{review_id}/show`
- **Headers**: `Authorization: Bearer <moderator_or_admin_token>`
- **Expected**: 200 OK, visible review

#### 8. Moderator/Admin: View Flagged Reviews (Reports)
- **Method**: GET
- **URL**: `http://localhost:8004/reviews/flagged`
- **Headers**: `Authorization: Bearer <moderator_or_admin_token>`
- **Expected**: 200 OK, list of flagged reviews

### Negative Test Cases

#### 1. Moderator tries to access admin-only endpoint
- **Method**: GET
- **URL**: `http://localhost:8004/admin/reviews`
- **Headers**: `Authorization: Bearer <moderator_token>`
- **Expected**: 403 Forbidden - "This operation requires admin privileges."

#### 2. Regular user tries to moderate
- **Method**: POST
- **URL**: `http://localhost:8004/admin/reviews/{review_id}/flag`
- **Headers**: `Authorization: Bearer <regular_user_token>`
- **Expected**: 403 Forbidden - "You do not have permission to moderate reviews."

#### 3. Unauthenticated request
- **Method**: GET
- **URL**: `http://localhost:8004/admin/reviews`
- **Headers**: None
- **Expected**: 403 Forbidden - "Not authenticated"

## Key Differences: Admin vs Moderator

| Operation | Admin | Moderator |
|-----------|-------|-----------|
| View all reviews | ✅ | ❌ |
| Delete reviews permanently | ✅ | ❌ |
| Restore reviews | ✅ | ❌ |
| Flag/unflag reviews | ✅ | ✅ |
| Hide/show reviews | ✅ | ✅ |
| View flagged reviews (reports) | ✅ | ✅ |

## Notes

- **Hide vs Delete**: 
  - Hide (`/hide`) is temporary and can be reversed by admin or moderator
  - Delete (`DELETE /admin/reviews/{review_id}`) is permanent and admin-only
  
- **Restore vs Show**:
  - `restore` endpoint is admin-only and explicitly for restoring hidden reviews
  - `show` endpoint is available to both moderator and admin

- **Duplicate Endpoints**: 
  - Flag/unflag operations exist in both `/admin/reviews/*` and `/reviews/*` paths
  - Both require moderator or admin role
  - Use whichever path is more convenient for your use case

