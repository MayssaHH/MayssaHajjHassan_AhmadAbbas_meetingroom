# Unified Error Handling

All four microservices (Users, Rooms, Bookings, Reviews) now use a unified error response format.

## Error Response Format

Every error is returned as a JSON object with the following structure:

```json
{
  "error_code": "ERROR_CODE",
  "message": "Human-readable error message",
  "details": {
    "field": "additional context",
    "reason": "more information"
  }
}
```

### Fields

- **`error_code`** (string, required): Machine-readable error identifier in UPPER_SNAKE_CASE
  - Examples: `VALIDATION_ERROR`, `UNAUTHORIZED`, `FORBIDDEN`, `NOT_FOUND`, `BOOKING_CONFLICT`
  
- **`message`** (string, required): Human-readable error message suitable for display to users

- **`details`** (object, optional): Additional contextual information about the error
  - For validation errors: `field`, `expected`, `actual`
  - For conflicts: `room_id`, `start_time`, `end_time`
  - For not found: `resource_type`, `resource_id`

## Error Types

### BadRequestError (400)
- **Error Code**: `VALIDATION_ERROR` (default) or more specific codes
- **Use Case**: Invalid request data, missing required fields, invalid parameter values
- **Example**:
```json
{
  "error_code": "VALIDATION_ERROR",
  "message": "Rating must be between 1 and 5",
  "details": {
    "field": "rating",
    "expected": "1-5",
    "actual": 10
  }
}
```

### UnauthorizedError (401)
- **Error Code**: `UNAUTHORIZED`
- **Use Case**: Missing or invalid authentication token
- **Example**:
```json
{
  "error_code": "UNAUTHORIZED",
  "message": "Authentication required.",
  "details": {}
}
```

### ForbiddenError (403)
- **Error Code**: `FORBIDDEN`
- **Use Case**: Authenticated user lacks permission for the operation
- **Example**:
```json
{
  "error_code": "FORBIDDEN",
  "message": "You do not have permission to perform this operation.",
  "details": {
    "required_role": "admin",
    "user_role": "regular"
  }
}
```

### NotFoundError (404)
- **Error Code**: `NOT_FOUND` (default) or more specific like `USER_NOT_FOUND`, `ROOM_NOT_FOUND`
- **Use Case**: Requested resource does not exist
- **Example**:
```json
{
  "error_code": "USER_NOT_FOUND",
  "message": "User not found.",
  "details": {
    "user_id": 123
  }
}
```

### ConflictError (409)
- **Error Code**: `CONFLICT` (default) or more specific like `BOOKING_CONFLICT`
- **Use Case**: Operation conflicts with existing state (e.g., overlapping bookings)
- **Example**:
```json
{
  "error_code": "BOOKING_CONFLICT",
  "message": "Room is already booked in this time range.",
  "details": {
    "room_id": 1,
    "start_time": "2025-01-01T10:00:00",
    "end_time": "2025-01-01T11:00:00"
  }
}
```

### InternalServerError (500)
- **Error Code**: `INTERNAL_ERROR`
- **Use Case**: Unexpected server errors (catch-all)
- **Example**:
```json
{
  "error_code": "INTERNAL_ERROR",
  "message": "An unexpected error occurred.",
  "details": {}
}
```

## Implementation

### Global Exception Handlers

All services register global exception handlers in their `main.py`:

```python
from common.error_handlers import register_error_handlers

app = FastAPI(...)
register_error_handlers(app)
```

The handlers automatically convert:
- **AppError** and subclasses → Unified JSON format
- **HTTPException** → Unified JSON format with appropriate error_code
- **ValidationError** (Pydantic) → Unified JSON format with validation details
- **Exception** (catch-all) → Internal server error in unified format

### Using Custom Exceptions

In your service code, raise custom exceptions:

```python
from common.exceptions import BadRequestError, NotFoundError

# Validation error
if rating < 1 or rating > 5:
    raise BadRequestError(
        message="Rating must be between 1 and 5",
        error_code="INVALID_RATING",
        details={"field": "rating", "value": rating}
    )

# Not found error
if user is None:
    raise NotFoundError(
        message="User not found",
        error_code="USER_NOT_FOUND",
        details={"user_id": user_id}
    )
```

### HTTPException Still Works

You can still use FastAPI's `HTTPException` - it will be automatically converted to the unified format:

```python
from fastapi import HTTPException, status

raise HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Review not found."
)
```

This will be converted to:
```json
{
  "error_code": "NOT_FOUND",
  "message": "Review not found.",
  "details": {}
}
```

## Benefits

1. **Consistency**: All services return errors in the same format
2. **Predictability**: Frontend/client code can handle errors uniformly
3. **Debugging**: Error codes make it easy to identify error types programmatically
4. **Details**: Additional context helps with troubleshooting
5. **Logging**: Errors are automatically logged with consistent structure

## Testing

All error responses follow this format. Test your endpoints and verify that:
- Invalid requests return `VALIDATION_ERROR`
- Unauthorized requests return `UNAUTHORIZED`
- Forbidden requests return `FORBIDDEN`
- Missing resources return `NOT_FOUND`
- Conflicts return `CONFLICT` or more specific codes

