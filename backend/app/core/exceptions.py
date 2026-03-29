"""
Custom exception classes for FinSight AI.

Each exception maps to a specific HTTP status code. When any of these
are raised anywhere in the application, FastAPI's exception handlers
(registered in main.py) catch them and return a clean JSON error response.

Example:
    raise NotFoundError("Document", document_id)
    → HTTP 404: {"detail": "Document with ID abc-123 not found"}
"""

from fastapi import HTTPException, status


class BadRequestError(HTTPException):
    """
    HTTP 400 — The request was malformed or missing required fields.
    Example: uploading a .docx file when only .pdf is accepted.
    """
    def __init__(self, detail: str = "Bad request"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class AuthenticationError(HTTPException):
    """
    HTTP 401 — The user is not authenticated (not logged in, or token expired).
    Example: sending a request without a valid JWT token.
    """
    def __init__(self, detail: str = "Could not validate credentials"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class AuthorizationError(HTTPException):
    """
    HTTP 403 — The user IS authenticated but does NOT have permission.
    Example: a "viewer" role trying to upload a document (only "analyst" and "admin" can).
    """
    def __init__(self, detail: str = "You do not have permission to perform this action"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class NotFoundError(HTTPException):
    """
    HTTP 404 — The requested resource does not exist.
    Example: trying to view a report for a document that was never uploaded.
    """
    def __init__(self, resource: str = "Resource", resource_id: str = ""):
        detail = f"{resource} not found"
        if resource_id:
            detail = f"{resource} with ID {resource_id} not found"
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class ConflictError(HTTPException):
    """
    HTTP 409 — The request conflicts with existing data.
    Example: trying to register with an email that already exists.
    """
    def __init__(self, detail: str = "Resource already exists"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class RateLimitError(HTTPException):
    """
    HTTP 429 — Too many requests. The user has exceeded their rate limit.
    Example: more than 5 login attempts per minute.
    """
    def __init__(self, detail: str = "Too many requests. Please try again later."):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
        )


class ServiceUnavailableError(HTTPException):
    """
    HTTP 503 — An external service (database, Redis, Qdrant) is down.
    Example: Redis connection failed during token blacklist check.
    """
    def __init__(self, detail: str = "Service temporarily unavailable"):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
        )