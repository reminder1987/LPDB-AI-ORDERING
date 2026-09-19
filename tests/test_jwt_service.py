from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.core.config import settings
from app.services.jwt_service import (
    create_access_token,
    decode_access_token,
)


def test_create_and_decode_access_token():
    token = create_access_token(
        user_id=123,
    )

    decoded_user_id = decode_access_token(
        token,
    )

    assert decoded_user_id == 123


def test_decode_access_token_requires_subject():
    now = datetime.now(timezone.utc)

    token = jwt.encode(
        {
            "iat": now,
            "exp": now + timedelta(minutes=60),
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    with pytest.raises(jwt.MissingRequiredClaimError):
        decode_access_token(token)


def test_decode_access_token_requires_expiration():
    now = datetime.now(timezone.utc)

    token = jwt.encode(
        {
            "sub": "123",
            "iat": now,
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    with pytest.raises(jwt.MissingRequiredClaimError):
        decode_access_token(token)


def test_decode_access_token_requires_issued_at():
    now = datetime.now(timezone.utc)

    token = jwt.encode(
        {
            "sub": "123",
            "exp": now + timedelta(minutes=60),
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    with pytest.raises(jwt.MissingRequiredClaimError):
        decode_access_token(token)


def test_decode_access_token_rejects_expired_token():
    now = datetime.now(timezone.utc)

    token = jwt.encode(
        {
            "sub": "123",
            "iat": now - timedelta(minutes=2),
            "exp": now - timedelta(minutes=1),
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(token)


def test_decode_access_token_rejects_invalid_subject():
    now = datetime.now(timezone.utc)

    token = jwt.encode(
        {
            "sub": "usuario-invalido",
            "iat": now,
            "exp": now + timedelta(minutes=60),
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token(token)