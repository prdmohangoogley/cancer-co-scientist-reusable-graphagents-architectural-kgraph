"""Enterprise authentication and Zero Ambient Authority (PAT-ZAA / DOC-02) token management.

Implements:
- Scoped JWT Token issuing and verification
- Role-based Access Control (Clinician, Researcher, Auditor)
- Mock User Registry with default oncology accounts
- FastAPI security dependency injection (get_current_user)
"""

from __future__ import annotations

import hashlib
import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import jwt
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

logger = logging.getLogger("auth")

# Enterprise JWT Configuration under Zero Ambient Authority
AUTH_JWT_SECRET = os.getenv("AUTH_JWT_SECRET", "coscientist-zaa-super-secret-key-32bytes-min!")
JWT_ALGORITHM = "HS256"
JWT_ISSUER = "https://auth.cancer-coscientist.app"
JWT_AUDIENCE = "cancer-coscientist-backend"
ACCESS_TOKEN_EXPIRE_MINUTES = 15


class UserCredentials(BaseModel):
    """User login / registration credentials."""
    email: Optional[str] = Field(default=None, description="User corporate or institutional email")
    username: Optional[str] = Field(default=None, description="Optional username alias")
    password: str = Field(..., min_length=4, description="Password")

    @property
    def identifier(self) -> str:
        val = self.email or self.username
        if not val:
            raise ValueError("Either email or username must be provided")
        return val.lower().strip()


class UserProfile(BaseModel):
    """Scoped user identity adhering to Zero Ambient Authority."""
    user_id: str
    email: str
    full_name: str
    roles: List[str] = Field(default_factory=lambda: ["clinician"])
    tenant_id: str = "mskcc_oncology"

    def has_role(self, role: str) -> bool:
        return role in self.roles


class TokenResponse(BaseModel):
    """JWT response structure."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = ACCESS_TOKEN_EXPIRE_MINUTES * 60
    user: UserProfile


def _hash_password(password: str, salt: str = "coscientist_salt") -> str:
    """Hash password using SHA-256 with salt."""
    return hashlib.sha256(f"{salt}:{password}".encode("utf-8")).hexdigest()


class UserRegistry:
    """Mock user registry simulating Cloud Identity / LDAP / Directory."""

    def __init__(self) -> None:
        self._users: Dict[str, dict[str, Any]] = {}
        self._seed_default_users()

    def _seed_default_users(self) -> None:
        """Seed default enterprise accounts for Clinician, Researcher, and Auditor."""
        default_accounts = [
            {
                "user_id": "usr_clinician_001",
                "email": "clinician@cancercenter.org",
                "full_name": "Dr. Sarah Chen, MD",
                "roles": ["clinician"],
                "tenant_id": "mskcc_oncology",
                "password_hash": _hash_password("clinician123!"),
            },
            {
                "user_id": "usr_researcher_002",
                "email": "researcher@cancercenter.org",
                "full_name": "Dr. Alex Mercer, PhD",
                "roles": ["researcher"],
                "tenant_id": "mskcc_genomics",
                "password_hash": _hash_password("researcher123!"),
            },
            {
                "user_id": "usr_auditor_003",
                "email": "auditor@cancercenter.org",
                "full_name": "Elena Rostova, CISA",
                "roles": ["auditor"],
                "tenant_id": "mskcc_compliance",
                "password_hash": _hash_password("auditor123!"),
            },
        ]

        for acc in default_accounts:
            self._users[acc["email"].lower()] = acc

    def authenticate(self, identifier: str, password: str) -> Optional[UserProfile]:
        """Authenticate user against registry."""
        email_key = identifier.lower().strip()
        account = self._users.get(email_key)
        if not account:
            # Also search by username if identifier is not an email
            for acc in self._users.values():
                if acc.get("username") == email_key:
                    account = acc
                    break

        if not account:
            return None

        if account["password_hash"] != _hash_password(password):
            return None

        return UserProfile(
            user_id=account["user_id"],
            email=account["email"],
            full_name=account["full_name"],
            roles=account["roles"],
            tenant_id=account["tenant_id"],
        )

    def register(
        self,
        identifier: str,
        password: str,
        full_name: str = "",
        roles: Optional[List[str]] = None,
        tenant_id: str = "mskcc_oncology",
    ) -> UserProfile:
        """Register a new user."""
        email_key = identifier.lower().strip()
        if email_key in self._users:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"User with identifier '{identifier}' already exists.",
            )

        user_id = f"usr_{uuid.uuid4().hex[:12]}"
        email_val = email_key if "@" in email_key else f"{email_key}@cancercenter.org"
        name_val = full_name or email_key.split("@")[0].capitalize()
        user_roles = roles if roles else ["clinician"]

        acc_data = {
            "user_id": user_id,
            "email": email_val,
            "username": email_key if "@" not in email_key else None,
            "full_name": name_val,
            "roles": user_roles,
            "tenant_id": tenant_id,
            "password_hash": _hash_password(password),
        }
        self._users[email_key] = acc_data

        return UserProfile(
            user_id=user_id,
            email=email_val,
            full_name=name_val,
            roles=user_roles,
            tenant_id=tenant_id,
        )

    def get_by_id(self, user_id: str) -> Optional[UserProfile]:
        """Find profile by user_id."""
        for acc in self._users.values():
            if acc["user_id"] == user_id:
                return UserProfile(
                    user_id=acc["user_id"],
                    email=acc["email"],
                    full_name=acc["full_name"],
                    roles=acc["roles"],
                    tenant_id=acc["tenant_id"],
                )
        return None


# Global registry singleton
user_registry = UserRegistry()


def create_access_token(user: UserProfile, expires_minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES) -> str:
    """Generate cryptographically signed JWT for the given user profile."""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=expires_minutes)

    payload: Dict[str, Any] = {
        "sub": user.user_id,
        "email": user.email,
        "full_name": user.full_name,
        "roles": user.roles,
        "tenant_id": user.tenant_id,
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }

    return jwt.encode(payload, AUTH_JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_access_token(token: str) -> UserProfile:
    """Verify JWT token signature and expiration, returning authenticated UserProfile."""
    try:
        payload = jwt.decode(
            token,
            AUTH_JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
            audience=JWT_AUDIENCE,
            issuer=JWT_ISSUER,
        )

        return UserProfile(
            user_id=payload["sub"],
            email=payload.get("email", ""),
            full_name=payload.get("full_name", ""),
            roles=payload.get("roles", ["clinician"]),
            tenant_id=payload.get("tenant_id", "mskcc_oncology"),
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


# FastAPI Security HTTP Bearer dependency
_bearer_security = HTTPBearer(auto_error=False)


async def get_current_user(
    auth_credentials: Optional[HTTPAuthorizationCredentials] = Security(_bearer_security),
) -> UserProfile:
    """FastAPI dependency extracting and verifying the Bearer token."""
    if not auth_credentials or not auth_credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed Authorization header. Expected Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return verify_access_token(auth_credentials.credentials)


def require_role(*allowed_roles: str):
    """Dependency factory checking that the authenticated user possesses at least one allowed role."""
    def _role_checker(user: UserProfile = Depends(get_current_user)) -> UserProfile:
        if not any(role in user.roles for role in allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. User roles {user.roles} do not include required: {list(allowed_roles)}",
            )
        return user
    return _role_checker
