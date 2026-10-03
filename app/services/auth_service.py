from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import get_password_hash, verify_password
from app.core.exceptions import CustomAPIException
from fastapi import status


class AuthService:
    @staticmethod
    def register_user(db: Session, user_in: UserCreate) -> User:
        """Register a new user after verifying email uniqueness."""
        existing_user = db.query(User).filter(User.email == user_in.email.lower()).first()
        if existing_user:
            raise CustomAPIException(
                status_code=status.HTTP_409_CONFLICT,
                code="EMAIL_ALREADY_REGISTERED",
                message="A user with this email address already exists."
            )
        
        db_user = User(
            name=user_in.name,
            email=user_in.email.lower(),
            hashed_password=get_password_hash(user_in.password),
            is_active=True
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> User:
        """Authenticate user credentials and return user object."""
        user = db.query(User).filter(User.email == email.lower()).first()
        if not user or not verify_password(password, user.hashed_password):
            raise CustomAPIException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                code="INVALID_CREDENTIALS",
                message="Invalid email or password."
            )
        if not user.is_active:
            raise CustomAPIException(
                status_code=status.HTTP_403_FORBIDDEN,
                code="INACTIVE_USER",
                message="User account is deactivated."
            )
        return user

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> User:
        """Fetch user by primary key ID."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise CustomAPIException(
                status_code=status.HTTP_404_NOT_FOUND,
                code="USER_NOT_FOUND",
                message="User not found."
            )
        return user
