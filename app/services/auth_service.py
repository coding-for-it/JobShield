from fastapi import status
from pymysql.connections import Connection
from app.database import fetch_one, execute
from app.schemas.user import UserCreate
from app.core.security import get_password_hash, verify_password
from app.core.exceptions import CustomAPIException


class AuthService:
    @staticmethod
    def register_user(db: Connection, user_in: UserCreate) -> dict:
        """Create a new user after checking the email is not already taken."""
        email = user_in.email.lower()

        if fetch_one(db, "SELECT id FROM users WHERE email = %s", (email,)):
            raise CustomAPIException(
                status_code=status.HTTP_409_CONFLICT,
                code="EMAIL_ALREADY_REGISTERED",
                message="A user with this email address already exists.",
            )

        user_id = execute(
            db,
            "INSERT INTO users (name, email, hashed_password) VALUES (%s, %s, %s)",
            (user_in.name, email, get_password_hash(user_in.password)),
        )
        db.commit()
        return fetch_one(db, "SELECT * FROM users WHERE id = %s", (user_id,))

    @staticmethod
    def authenticate_user(db: Connection, email: str, password: str) -> dict:
        """Check email + password and return the user row."""
        user = fetch_one(db, "SELECT * FROM users WHERE email = %s", (email.lower(),))

        if not user or not verify_password(password, user["hashed_password"]):
            raise CustomAPIException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                code="INVALID_CREDENTIALS",
                message="Invalid email or password.",
            )
        if not user["is_active"]:
            raise CustomAPIException(
                status_code=status.HTTP_403_FORBIDDEN,
                code="INACTIVE_USER",
                message="User account is deactivated.",
            )
        return user
