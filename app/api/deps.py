from fastapi import Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pymysql.connections import Connection
from app.database import get_db, fetch_one
from app.core.security import decode_access_token
from app.core.exceptions import CustomAPIException

# Reads the "Authorization: Bearer <token>" header
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    db: Connection = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    """
    Dependency used by protected endpoints. Steps:
    1. Read the Bearer token from the Authorization header.
    2. Verify the JWT signature and expiry.
    3. Load that user from MySQL and make sure the account is active.
    Returns the user row as a dictionary.
    """
    if not credentials or not credentials.credentials:
        raise CustomAPIException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="MISSING_TOKEN",
            message="Authorization token is required.",
        )

    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise CustomAPIException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="INVALID_TOKEN",
            message="Invalid or expired authentication token.",
        )

    try:
        user_id = int(payload.get("sub"))
    except (TypeError, ValueError):
        raise CustomAPIException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="INVALID_TOKEN_PAYLOAD",
            message="Token payload is missing a valid user id.",
        )

    user = fetch_one(db, "SELECT * FROM users WHERE id = %s", (user_id,))
    if not user:
        raise CustomAPIException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="USER_NOT_FOUND",
            message="User belonging to this token no longer exists.",
        )

    if not user["is_active"]:
        raise CustomAPIException(
            status_code=status.HTTP_403_FORBIDDEN,
            code="INACTIVE_USER",
            message="User account is deactivated.",
        )

    return user
