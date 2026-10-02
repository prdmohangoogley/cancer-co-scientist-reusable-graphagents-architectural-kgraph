"""Unit tests for enterprise authentication and Zero Ambient Authority token management (PAT-ZAA / DOC-02)."""

from __future__ import annotations

import sys
from pathlib import Path
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

# Add apps/co-scientist to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "apps" / "co-scientist"))

from agent.auth import (
    UserCredentials,
    UserProfile,
    create_access_token,
    get_current_user,
    require_role,
    user_registry,
    verify_access_token,
)


def test_default_user_registry_authentication():
    """Verify built-in default users authenticate successfully."""
    # Clinician
    clinician = user_registry.authenticate("clinician@cancercenter.org", "clinician123!")
    assert clinician is not None
    assert clinician.email == "clinician@cancercenter.org"
    assert "clinician" in clinician.roles
    assert clinician.tenant_id == "mskcc_oncology"

    # Researcher
    researcher = user_registry.authenticate("researcher@cancercenter.org", "researcher123!")
    assert researcher is not None
    assert "researcher" in researcher.roles

    # Auditor
    auditor = user_registry.authenticate("auditor@cancercenter.org", "auditor123!")
    assert auditor is not None
    assert "auditor" in auditor.roles

    # Invalid password
    bad_auth = user_registry.authenticate("clinician@cancercenter.org", "wrong_password!")
    assert bad_auth is None

    # Non-existent user
    non_existent = user_registry.authenticate("nonexistent@cancercenter.org", "password")
    assert non_existent is None


def test_user_registration_flow():
    """Verify new user registration and duplicate rejection."""
    reg_user = user_registry.register(
        identifier="new_oncologist@cancercenter.org",
        password="securePassword123!",
        full_name="Dr. Oncology Fellow",
        roles=["clinician"],
        tenant_id="mskcc_pediatrics",
    )
    assert reg_user.user_id.startswith("usr_")
    assert reg_user.email == "new_oncologist@cancercenter.org"
    assert reg_user.roles == ["clinician"]

    # Verify login with newly registered user
    authenticated = user_registry.authenticate("new_oncologist@cancercenter.org", "securePassword123!")
    assert authenticated is not None
    assert authenticated.user_id == reg_user.user_id

    # Verify duplicate registration fails with 409
    with pytest.raises(HTTPException) as exc_info:
        user_registry.register(
            identifier="new_oncologist@cancercenter.org",
            password="anotherPassword",
        )
    assert exc_info.value.status_code == 409


def test_jwt_create_and_verify():
    """Verify JWT access token creation, signing, and verification under ZAA."""
    user = UserProfile(
        user_id="usr_test_12345",
        email="test_user@cancercenter.org",
        full_name="Test Clinician",
        roles=["clinician", "researcher"],
        tenant_id="mskcc_test",
    )

    token = create_access_token(user, expires_minutes=15)
    assert isinstance(token, str)
    assert len(token) > 50

    verified_user = verify_access_token(token)
    assert verified_user.user_id == user.user_id
    assert verified_user.email == user.email
    assert verified_user.roles == ["clinician", "researcher"]
    assert verified_user.tenant_id == "mskcc_test"


def test_jwt_expiration():
    """Verify expired JWT tokens raise HTTP 401 Unauthorized."""
    user = UserProfile(
        user_id="usr_expired_001",
        email="expired@cancercenter.org",
        full_name="Expired User",
        roles=["clinician"],
    )

    # Issue an already-expired token (-5 minutes)
    expired_token = create_access_token(user, expires_minutes=-5)

    with pytest.raises(HTTPException) as exc_info:
        verify_access_token(expired_token)
    assert exc_info.value.status_code == 401
    assert "expired" in exc_info.value.detail.lower()


def test_jwt_invalid_signature():
    """Verify tampered or invalid JWT tokens raise HTTP 401 Unauthorized."""
    with pytest.raises(HTTPException) as exc_info:
        verify_access_token("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature")
    assert exc_info.value.status_code == 401
    assert "invalid" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_get_current_user_dependency():
    """Verify FastAPI security dependency get_current_user extracts bearer token."""
    user = UserProfile(
        user_id="usr_dep_001",
        email="dep@cancercenter.org",
        full_name="Dependency User",
        roles=["clinician"],
    )
    token = create_access_token(user)

    # Valid Bearer credentials
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    current = await get_current_user(creds)
    assert current.user_id == user.user_id

    # Missing credentials
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(None)
    assert exc_info.value.status_code == 401


def test_require_role_access_control():
    """Verify role-based access control enforcement."""
    clinician_user = UserProfile(
        user_id="usr_clin_99",
        email="clin@cancercenter.org",
        full_name="Clinician Only",
        roles=["clinician"],
    )

    # Clinician should pass clinician role check
    check_clinician = require_role("clinician")
    assert check_clinician(clinician_user) == clinician_user

    # Clinician should be forbidden from auditor-only endpoint
    check_auditor = require_role("auditor")
    with pytest.raises(HTTPException) as exc_info:
        check_auditor(clinician_user)
    assert exc_info.value.status_code == 403
