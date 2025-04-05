from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from src.auth.dependencies import get_current_active_user
from src.auth.schemas import User, UserResponse

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Get current user information."""
    return current_user

@router.get("/", response_model=List[UserResponse])
async def read_users(
    skip: int = 0, 
    limit: int = 100, 
    current_user: User = Depends(get_current_active_user)
):
    """Get list of users (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    # This would normally query the database
    return []