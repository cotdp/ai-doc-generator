from typing import Annotated, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from src.database import get_db
from src.database.models import User, UserRole
from .jwt import verify_token

# OAuth2 scheme for Swagger UI and authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get the current user from the token.
    
    Args:
        token: The JWT token
        db: Database session
        
    Returns:
        User: The current user
        
    Raises:
        HTTPException: If authentication fails
    """
    # Verify the token
    token_data = verify_token(token)
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get the user from the database
    user = db.query(User).filter(User.id == int(token_data.sub)).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Get the current active user.
    
    Args:
        current_user: The current user
        
    Returns:
        User: The current active user
        
    Raises:
        HTTPException: If the user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user


async def get_current_admin_user(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    """Get the current admin user.
    
    Args:
        current_user: The current user
        
    Returns:
        User: The current admin user
        
    Raises:
        HTTPException: If the user is not an admin
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized",
        )
    return current_user