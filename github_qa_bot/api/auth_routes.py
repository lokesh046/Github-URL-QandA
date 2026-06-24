from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from utils.db import get_user_by_username, create_user
from utils.auth import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


class AuthRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)


class AuthResponse(BaseModel):
    username: str
    message: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    username: str


@router.post("/signup", response_model=AuthResponse)
def signup(request: AuthRequest):
    username = request.username.strip()
    
    # Check if user already exists
    existing_user = get_user_by_username(username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
        
    # Hash the password and save
    hashed = hash_password(request.password)
    success = create_user(username, hashed)
    
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
def login(request: AuthRequest):
    username = request.username.strip()
    
    # Fetch user
    user = get_user_by_username(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
        
    # Verify password
    if not verify_password(request.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
        
    # Generate token
    token = create_access_token(data={"sub": username})
    
    return LoginResponse(
        access_token=token,
        token_type="bearer",
        username=username
    )
