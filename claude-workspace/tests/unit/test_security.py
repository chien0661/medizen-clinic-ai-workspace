"""Unit tests for app.core.security — password hashing and JWT tokens."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from jose import JWTError
from jose import jwt as jose_jwt

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)

# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------


class TestPasswordHashing:
    def test_hash_returns_string(self):
        hashed = hash_password("secret123")
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_hash_is_not_plaintext(self):
        plain = "my_password"
        hashed = hash_password(plain)
        assert hashed != plain

    def test_verify_correct_password(self):
        plain = "correct_horse_battery_staple"
        hashed = hash_password(plain)
        assert verify_password(plain, hashed) is True

    def test_verify_wrong_password(self):
        hashed = hash_password("correct")
        assert verify_password("wrong", hashed) is False

    def test_verify_empty_string_fails(self):
        hashed = hash_password("not_empty")
        assert verify_password("", hashed) is False

    def test_two_hashes_of_same_password_differ(self):
        """bcrypt uses random salts — same password should produce different hashes."""
        pw = "same_password"
        h1 = hash_password(pw)
        h2 = hash_password(pw)
        assert h1 != h2
        # But both verify correctly
        assert verify_password(pw, h1)
        assert verify_password(pw, h2)


# ---------------------------------------------------------------------------
# Access token
# ---------------------------------------------------------------------------


class TestCreateAccessToken:
    def test_access_token_is_string(self):
        token = create_access_token(uuid4(), uuid4(), [], [])
        assert isinstance(token, str)

    def test_access_token_has_correct_claims(self):
        user_id = uuid4()
        clinic_id = uuid4()
        roles = ["admin"]
        permissions = ["read:patient"]

        token = create_access_token(user_id, clinic_id, roles, permissions)
        claims = decode_token(token)

        assert claims["sub"] == str(user_id)
        assert claims["clinic_id"] == str(clinic_id)
        assert claims["roles"] == roles
        assert claims["permissions"] == permissions
        assert claims["type"] == "access"
        assert "jti" in claims
        assert "exp" in claims
        assert "iat" in claims

    def test_access_token_expires_in_15_minutes(self):
        token = create_access_token(uuid4(), uuid4(), [], [])
        claims = decode_token(token)
        exp = datetime.fromtimestamp(claims["exp"], tz=UTC)
        iat = datetime.fromtimestamp(claims["iat"], tz=UTC)
        delta = exp - iat
        # Allow ±2 second tolerance
        assert abs(delta.total_seconds() - settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60) <= 2

    def test_access_token_jti_is_unique(self):
        uid = uuid4()
        cid = uuid4()
        t1 = create_access_token(uid, cid, [], [])
        t2 = create_access_token(uid, cid, [], [])
        c1 = decode_token(t1)
        c2 = decode_token(t2)
        assert c1["jti"] != c2["jti"]


# ---------------------------------------------------------------------------
# Refresh token
# ---------------------------------------------------------------------------


class TestCreateRefreshToken:
    def test_refresh_token_has_correct_claims(self):
        user_id = uuid4()
        clinic_id = uuid4()
        token = create_refresh_token(user_id, clinic_id)
        claims = decode_token(token)

        assert claims["sub"] == str(user_id)
        assert claims["clinic_id"] == str(clinic_id)
        assert claims["type"] == "refresh"
        assert "jti" in claims

    def test_refresh_token_expires_in_7_days(self):
        token = create_refresh_token(uuid4(), uuid4())
        claims = decode_token(token)
        exp = datetime.fromtimestamp(claims["exp"], tz=UTC)
        iat = datetime.fromtimestamp(claims["iat"], tz=UTC)
        delta = exp - iat
        expected_seconds = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400
        assert abs(delta.total_seconds() - expected_seconds) <= 2


# ---------------------------------------------------------------------------
# decode_token
# ---------------------------------------------------------------------------


class TestDecodeToken:
    def test_decode_valid_access_token(self):
        user_id = uuid4()
        token = create_access_token(user_id, uuid4(), [], [])
        claims = decode_token(token)
        assert claims["sub"] == str(user_id)

    def test_decode_raises_on_expired_token(self):
        """An access token with exp in the past must raise JWTError."""
        user_id = uuid4()
        clinic_id = uuid4()
        past = datetime.now(UTC) - timedelta(seconds=10)
        payload = {
            "sub": str(user_id),
            "clinic_id": str(clinic_id),
            "type": "access",
            "jti": str(uuid4()),
            "exp": past,
            "iat": past - timedelta(minutes=15),
        }
        expired_token = jose_jwt.encode(
            payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
        )
        with pytest.raises(JWTError):
            decode_token(expired_token)

    def test_decode_raises_on_wrong_signature(self):
        token = jose_jwt.encode(
            {"sub": str(uuid4()), "exp": datetime.now(UTC) + timedelta(minutes=15)},
            "wrong-secret",
            algorithm="HS256",
        )
        with pytest.raises(JWTError):
            decode_token(token)

    def test_decode_raises_on_malformed_token(self):
        with pytest.raises(JWTError):
            decode_token("not.a.valid.token")

    def test_decode_raises_on_empty_string(self):
        with pytest.raises(JWTError):
            decode_token("")
