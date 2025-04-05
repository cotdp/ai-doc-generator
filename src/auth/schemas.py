from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, validator


class Token(BaseModel):
    """Token model."""
    access_token: str
    refresh_token: str
    token_type: str


class TokenData(BaseModel):
    """Token data model."""
    sub: Optional[str] = None
    role: Optional[str] = None


class RefreshToken(BaseModel):
    """Refresh token model."""
    refresh_token: str


class UserBase(BaseModel):
    """Base user model."""
    email: EmailStr
    username: str
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """User create model."""
    password: str = Field(..., min_length=8)
    password_confirm: str

    @validator("password_confirm")
    def passwords_match(cls, v, values, **kwargs):
        if "password" in values and v != values["password"]:
            raise ValueError("Passwords do not match")
        return v


class UserUpdate(BaseModel):
    """User update model."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None


class UserRead(UserBase):
    """User read model."""
    id: int
    role: str
    is_active: bool

    class Config:
        orm_mode = True


class User(UserBase):
    """User model for API operations."""
    id: int
    role: str
    is_active: bool
    is_admin: bool = False

    class Config:
        orm_mode = True


class UserResponse(UserBase):
    """User response model."""
    id: int
    role: str
    is_active: bool

    class Config:
        orm_mode = True


class ChangePassword(BaseModel):
    """Change password model."""
    current_password: str
    new_password: str = Field(..., min_length=8)
    new_password_confirm: str

    @validator("new_password_confirm")
    def passwords_match(cls, v, values, **kwargs):
        if "new_password" in values and v != values["new_password"]:
            raise ValueError("Passwords do not match")
        return v