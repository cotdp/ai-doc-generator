from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from src.database import get_db
from src.database.models import User, UserRole
from .auth import verify_password, get_password_hash
from .jwt import create_access_token, create_refresh_token
from .dependencies import get_current_user, get_current_active_user
from .schemas import (
    Token, TokenData, UserCreate, UserRead, UserUpdate, 
    RefreshToken, ChangePassword
)

# Create router
router = APIRouter(prefix="/auth", tags=["Authentication"])

# OAuth2 scheme for authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db)
):
    """Login and get access token.
    
    Args:
        form_data: Form data with username and password
        db: Database session
        
    Returns:
        Token: Access token and refresh token
        
    Raises:
        HTTPException: If authentication fails
    """
    # Get user by username or email
    user = (
        db.query(User)
        .filter(
            (User.username == form_data.username) | 
            (User.email == form_data.username)
        )
        .first()
    )
    
    # Check user exists and password is correct
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    
    # Create access token
    access_token_data = {
        "sub": str(user.id),
        "role": user.role.value,
    }
    access_token = create_access_token(data=access_token_data)
    
    # Create refresh token
    refresh_token_data = {
        "sub": str(user.id),
        "role": user.role.value,
    }
    refresh_token = create_refresh_token(data=refresh_token_data)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=Token)
async def refresh_access_token(
    refresh_token_data: RefreshToken,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token.
    
    Args:
        refresh_token_data: Refresh token
        db: Database session
        
    Returns:
        Token: New access token and refresh token
        
    Raises:
        HTTPException: If refresh token is invalid
    """
    from .jwt import verify_token
    
    # Verify refresh token
    token_data = verify_token(refresh_token_data.refresh_token)
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user by ID
    user = db.query(User).filter(User.id == int(token_data.sub)).first()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create new access token
    access_token_data = {
        "sub": str(user.id),
        "role": user.role.value,
    }
    access_token = create_access_token(data=access_token_data)
    
    # Create new refresh token
    refresh_token_data = {
        "sub": str(user.id),
        "role": user.role.value,
    }
    refresh_token = create_refresh_token(data=refresh_token_data)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/register", response_model=UserRead)
async def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """Register a new user.
    
    Args:
        user_data: User data
        db: Database session
        
    Returns:
        UserRead: The created user
        
    Raises:
        HTTPException: If username or email already exists
    """
    # Check if username or email already exists
    existing_user = (
        db.query(User)
        .filter(
            (User.username == user_data.username) | 
            (User.email == user_data.email)
        )
        .first()
    )
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered",
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hashed_password,
        role=UserRole.USER,  # Default role is user
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user


@router.get("/me", response_model=UserRead)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Get current user.
    
    Args:
        current_user: Current user
        
    Returns:
        UserRead: The current user
    """
    return current_user


@router.put("/me", response_model=UserRead)
async def update_user_me(
    user_data: UserUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db)
):
    """Update current user.
    
    Args:
        user_data: User data to update
        current_user: Current user
        db: Database session
        
    Returns:
        UserRead: The updated user
        
    Raises:
        HTTPException: If email is already used by another user
    """
    # Check if email already exists and belongs to another user
    if user_data.email != current_user.email:
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
    
    # Update user data
    if user_data.email is not None:
        current_user.email = user_data.email
    if user_data.full_name is not None:
        current_user.full_name = user_data.full_name
    
    db.commit()
    db.refresh(current_user)
    
    return current_user


@router.post("/change-password")
async def change_password(
    password_data: ChangePassword,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db)
):
    """Change password for current user.
    
    Args:
        password_data: Password data
        current_user: Current user
        db: Database session
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: If current password is incorrect
    """
    # Check if current password is correct
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect password",
        )
    
    # Hash new password
    hashed_password = get_password_hash(password_data.new_password)
    
    # Update password
    current_user.hashed_password = hashed_password
    db.commit()
    
    return {"message": "Password changed successfully"}