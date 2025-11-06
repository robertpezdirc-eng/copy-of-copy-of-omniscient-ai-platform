"""
User Models - Authentication & User Management
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
from enum import Enum


class UserRole(str, Enum):
    """User roles"""
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    USER = "user"
    READONLY = "readonly"


class UserStatus(str, Enum):
    """User account status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


# Pydantic Models for API
class UserBase(BaseModel):
    """Base user model"""
    email: EmailStr
    full_name: str
    role: UserRole = UserRole.USER
    is_active: bool = True
    tenant_id: Optional[str] = None


class UserCreate(UserBase):
    """User creation model"""
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    """User update model"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class User(UserBase):
    """User response model"""
    id: str
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    email_verified: bool = False
    phone_verified: bool = False
    mfa_enabled: bool = False
    
    class Config:
        from_attributes = True


class UserInDB(User):
    """User model with password hash"""
    hashed_password: str


class UserProfile(BaseModel):
    """Extended user profile"""
    user_id: str
    avatar_url: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    timezone: str = "UTC"
    language: str = "en"
    currency: str = "EUR"
    bio: Optional[str] = None
    social_links: dict = {}
    preferences: dict = {}
    metadata: dict = {}


class UserStats(BaseModel):
    """User statistics"""
    user_id: str
    total_api_calls: int = 0
    total_ai_interactions: int = 0
    total_spent: float = 0.0
    affiliate_earnings: float = 0.0
    referral_count: int = 0
    login_count: int = 0
    last_activity: Optional[datetime] = None


# Authentication Models
class Token(BaseModel):
    """JWT token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """Token payload data"""
    user_id: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    tenant_id: Optional[str] = None


class LoginRequest(BaseModel):
    """Login request"""
    email: EmailStr
    password: str
    remember_me: bool = False


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str


class PasswordResetRequest(BaseModel):
    """Password reset request"""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation"""
    token: str
    new_password: str = Field(..., min_length=8)


class ChangePasswordRequest(BaseModel):
    """Change password request"""
    current_password: str
    new_password: str = Field(..., min_length=8)


class MFASetupRequest(BaseModel):
    """MFA setup request"""
    method: str = Field(..., pattern="^(totp|sms|email)$")


class MFAVerifyRequest(BaseModel):
    """MFA verification request"""
    code: str = Field(..., min_length=6, max_length=6)


class OAuth2Provider(str, Enum):
    """OAuth2 providers"""
    GOOGLE = "google"
    GITHUB = "github"
    MICROSOFT = "microsoft"
    FACEBOOK = "facebook"


class OAuth2CallbackRequest(BaseModel):
    """OAuth2 callback request"""
    provider: OAuth2Provider
    code: str
    state: str
