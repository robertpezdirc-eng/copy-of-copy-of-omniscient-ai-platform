"""from datetime import datetime, timedelta, timezone

Authentication & User Management Routesimport os

JWT-based authentication with MFA supportfrom typing import Optional, List

"""

import pyotp

from fastapi import APIRouter, HTTPException, Depends, Bodyfrom fastapi import APIRouter, HTTPException, Depends, Body

from pydantic import BaseModel, EmailStrfrom fastapi.security import OAuth2PasswordRequestForm

from typing import Optionalfrom jose import jwt

from datetime import datetime, timedelta, timezonefrom passlib.context import CryptContext

import uuidfrom pydantic import BaseModel, EmailStr

import secrets

from utils.gcp import get_firestore

router = APIRouter()



router = APIRouter()

class UserLogin(BaseModel):

    email: EmailStrpwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

    password: str

    mfa_code: Optional[str] = NoneJWT_ALG = "HS256"

JWT_TTL_MIN = int(os.getenv("JWT_TTL_MIN", "120"))

JWT_SECRET = os.getenv("JWT_SECRET", "change-this-in-prod")

class UserRegister(BaseModel):

    email: EmailStr

    password: strclass RegisterRequest(BaseModel):

    full_name: str    email: EmailStr

    company_name: Optional[str] = None    password: str

    tenant_id: Optional[str] = None

    roles: Optional[List[str]] = ["user"]

class TokenResponse(BaseModel):    enable_mfa: bool = False

    access_token: str

    refresh_token: str

    token_type: str = "bearer"class TokenResponse(BaseModel):

    expires_in: int    access_token: str

    token_type: str = "bearer"

    expires_in: int

@router.post("/register")

async def register_user(user: UserRegister):

    """Register new user"""def create_token(sub: str, tenant_id: str, roles: List[str]) -> TokenResponse:

        now = datetime.now(timezone.utc)

    user_id = f"user_{uuid.uuid4().hex[:12]}"    exp = now + timedelta(minutes=JWT_TTL_MIN)

        payload = {

    return {        "sub": sub,

        "success": True,        "iat": int(now.timestamp()),

        "user_id": user_id,        "exp": int(exp.timestamp()),

        "email": user.email,        "tenant_id": tenant_id,

        "message": "User registered successfully",        "roles": roles,

        "verification_email_sent": True    }

    }    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)

    return TokenResponse(access_token=token, expires_in=JWT_TTL_MIN * 60)



@router.post("/login")

async def login_user(credentials: UserLogin):@router.post("/register", response_model=TokenResponse)

    """User login with JWT token generation"""async def register_user(req: RegisterRequest):

        """

    # Generate tokens    Register a new user account with JWT authentication.

    access_token = f"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.{secrets.token_urlsafe(32)}"

    refresh_token = f"refresh_{secrets.token_urlsafe(48)}"    **Request Body:**

        ```json

    return TokenResponse(    {

        access_token=access_token,        "email": "user@example.com",

        refresh_token=refresh_token,        "password": "SecurePass123!",

        expires_in=86400  # 24 hours        "tenant_id": "t_mycompany",  // optional, auto-generated if not provided

    )        "roles": ["user", "admin"],   // optional, defaults to ["user"]

        "enable_mfa": false           // optional, enable 2FA/TOTP

    }

@router.post("/logout")    ```

async def logout_user():

    """User logout"""    **Response:**

    return {"success": True, "message": "Logged out successfully"}    ```json

    {

        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",

@router.get("/me")        "token_type": "bearer",

async def get_current_user():        "expires_in": 7200  // seconds (2 hours)

    """Get current authenticated user"""    }

        ```

    return {

        "user_id": "user_demo123",    **Errors:**

        "email": "user@example.com",    - 400: Email already registered

        "full_name": "Demo User",    - 422: Validation error (invalid email format)

        "role": "admin",

        "tenant_id": "tenant_demo",    **Usage:**

        "created_at": datetime.now(timezone.utc).isoformat()    Include the access_token in subsequent requests:

    }    ```

    Authorization: Bearer <access_token>

    ```

@router.post("/refresh")    """

async def refresh_token(refresh_token: str = Body(..., embed=True)):    db = get_firestore()

    """Refresh access token"""    users = db.collection("users")

        # Check existing

    new_access_token = f"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.{secrets.token_urlsafe(32)}"    existing = list(users.where("email", "==", req.email).limit(1).stream())

        if existing:

    return {        raise HTTPException(status_code=400, detail="Email already registered")

        "access_token": new_access_token,

        "token_type": "bearer",    user_doc = {

        "expires_in": 86400        "email": req.email,

    }        "password_hash": pwd_context.hash(req.password),

        "tenant_id": req.tenant_id or f"t_{req.email.split('@')[0]}",
        "roles": req.roles or ["user"],
    "created_at": datetime.now(timezone.utc).isoformat(),
        "mfa_enabled": req.enable_mfa,
        "mfa_secret": pyotp.random_base32() if req.enable_mfa else None,
    }
    ref = users.document()
    ref.set(user_doc)

    return create_token(ref.id, user_doc["tenant_id"], user_doc["roles"])


@router.post("/login", response_model=TokenResponse)
async def login(form: OAuth2PasswordRequestForm = Depends()):
    """
    Authenticate user and obtain JWT access token.

    **Form Data (application/x-www-form-urlencoded):**
    - username: user@example.com (email address)
    - password: SecurePass123!
    - scope: mfa:123456 (optional, required if MFA enabled)

    **Alternative JSON Request:**
    ```bash
    curl -X POST "https://api.example.com/api/v1/auth/login" \\
      -H "Content-Type: application/x-www-form-urlencoded" \\
      -d "username=user@example.com&password=SecurePass123!"
    ```

    **Response:**
    ```json
    {
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "token_type": "bearer",
        "expires_in": 7200
    }
    ```

    **Errors:**
    - 400: Invalid credentials (wrong email or password)
    - 401: MFA code required or invalid MFA code

    **MFA Flow:**
    If MFA is enabled, include TOTP code in scope:
    ```
    username=user@example.com&password=Pass123!&scope=mfa:123456
    ```
    """
    db = get_firestore()
    users = db.collection("users")
    q = users.where("email", "==", form.username).limit(1).stream()
    rec = next(iter(q), None)
    if not rec:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    data = rec.to_dict()
    if not pwd_context.verify(form.password, data.get("password_hash", "")):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    # Optional MFA code validation if provided in 'scope' (dirty but simple for now)
    # Client can pass scope="mfa:123456" to submit TOTP
    if data.get("mfa_enabled"):
        code = None
        for s in form.scopes:
            if s.startswith("mfa:"):
                code = s.split(":", 1)[1]
                break
        if not code:
            raise HTTPException(status_code=401, detail="MFA code required: use scope mfa:123456")
        totp = pyotp.TOTP(data.get("mfa_secret"))
        if not totp.verify(code, valid_window=1):
            raise HTTPException(status_code=401, detail="Invalid MFA code")

    return create_token(rec.id, data.get("tenant_id", "default"), data.get("roles", ["user"]))
