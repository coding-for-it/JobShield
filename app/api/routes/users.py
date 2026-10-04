from fastapi import APIRouter, Depends
from pymysql.connections import Connection
from app.database import get_db, fetch_one, update_row
from app.schemas.user import UserResponse, UserUpdate
from app.api.deps import get_current_user
from app.core.security import get_password_hash

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
def get_user_profile(current_user: dict = Depends(get_current_user)):
    """Retrieve current user profile."""
    return current_user


@router.patch("/me", response_model=UserResponse)
def update_user_profile(
    user_update: UserUpdate,
    current_user: dict = Depends(get_current_user),
    db: Connection = Depends(get_db),
):
    """Update current user profile (name or password)."""
    fields = {}
    if user_update.name is not None:
        fields["name"] = user_update.name
    if user_update.password is not None:
        fields["hashed_password"] = get_password_hash(user_update.password)

    update_row(db, "users", current_user["id"], fields)
    return fetch_one(db, "SELECT * FROM users WHERE id = %s", (current_user["id"],))
