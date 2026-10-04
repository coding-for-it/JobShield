from fastapi import APIRouter, Depends, status
from pymysql.connections import Connection
from app.database import get_db
from app.schemas.user import UserCreate, UserResponse
from app.schemas.auth import Token, LoginRequest
from app.services.auth_service import AuthService
from app.core.security import create_access_token
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Connection = Depends(get_db)):
    """
    Register a new user account.
    Validates email format, checks for duplicate registration, hashes password with bcrypt.
    """
    user = AuthService.register_user(db, user_in)
    return user


@router.post("/login", response_model=Token, status_code=status.HTTP_200_OK)
def login(login_in: LoginRequest, db: Connection = Depends(get_db)):
    """
    Authenticate user credentials and generate a signed JWT access token.
    """
    user = AuthService.authenticate_user(db, email=login_in.email, password=login_in.password)
    access_token = create_access_token(subject=user["id"])
    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
def get_me(current_user: dict = Depends(get_current_user)):
    """
    Protected endpoint to retrieve the authenticated user profile.
    Requires Bearer JWT token in Authorization header.
    """
    return current_user
