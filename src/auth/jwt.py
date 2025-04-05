import os
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from jose import jwt
from pydantic import BaseModel

# Load secret key from environment variable
SECRET_KEY = os.getenv("SECRET_KEY", "default-secret-key-for-development-only")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))


class TokenPayload(BaseModel):
    """Token payload model."""
    sub: str
    exp: datetime
    iat: datetime
    role: str


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a new JWT access token.
    
    Args:
        data: The data to encode in the token
        expires_delta: Optional expiration time
        
    Returns:
        str: The encoded JWT
    """
    to_encode = data.copy()
    
    # Set expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Add expiration time and issued at time to the payload
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    
    # Encode the JWT
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create a new JWT refresh token.
    
    Args:
        data: The data to encode in the token
        
    Returns:
        str: The encoded JWT
    """
    to_encode = data.copy()
    
    # Set expiration time (longer than access token)
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    # Add expiration time and issued at time to the payload
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    
    # Encode the JWT
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[TokenPayload]:
    """Verify a JWT token and return its payload.
    
    Args:
        token: The JWT token
        
    Returns:
        TokenPayload: The token payload if valid, None otherwise
    """
    try:
        # Decode the JWT
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Extract the subject (user ID), expiration time, and issued at time
        token_data = TokenPayload(
            sub=payload["sub"],
            exp=datetime.fromtimestamp(payload["exp"]),
            iat=datetime.fromtimestamp(payload["iat"]),
            role=payload.get("role", "user")
        )
        
        # Check if token is expired
        if datetime.utcnow() >= token_data.exp:
            return None
            
        return token_data
    except jwt.JWTError:
        return None