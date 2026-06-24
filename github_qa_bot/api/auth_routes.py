import re
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from utils.db import get_user_by_username, get_user_by_email, create_user
from utils.auth import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


class SignupRequest(BaseModel):
    username: str
    email: str
    password: str

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        v = v.strip()
        if not re.match(r"^[a-zA-Z][a-zA-Z0-9_]{2,29}$", v):
            raise ValueError(
                "Username must start with a letter and contain only alphanumeric characters or underscores (3-30 characters)"
            )
        return v

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", v):
            raise ValueError("Gmail ID / Email must be a valid email address")
        return v

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")
        if not re.search(r"[@$!%*?&#]", v):
            raise ValueError("Password must contain at least one special character (@$!%*?&#)")
        return v


class LoginRequest(BaseModel):
    username_or_email: str
    password: str

    @field_validator('username_or_email')
    @classmethod
    def validate_username_or_email(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Username or Email is required")
        return v

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not v:
            raise ValueError("Password is required")
        return v


class AuthResponse(BaseModel):
    username: str
    message: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    username: str


@router.post("/signup", response_model=AuthResponse)
def signup(request: SignupRequest):
    username = request.username.strip()
    email = request.email.strip().lower()
    
    # Check if username already exists
    if get_user_by_username(username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
        
    # Check if email already exists
    if get_user_by_email(email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email/Gmail ID already registered"
        )
        
    # Hash the password and save
    hashed = hash_password(request.password)
    success = create_user(username, email, hashed)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register user"
        )
        
    return AuthResponse(
        username=username,
        message="User registered successfully"
    )


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest):
    username_or_email = request.username_or_email.strip()
    
    # Fetch user (searches by username or email)
    user = get_user_by_username(username_or_email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username/email or password"
        )
        
    # Verify password
    if not verify_password(request.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username/email or password"
        )
        
    # Generate token
    token = create_access_token(data={"sub": user["username"]})
    
    return LoginResponse(
        access_token=token,
        token_type="bearer",
        username=user["username"]
    )
