from datetime import timedelta

import pytest
from jose import JWTError, jwt

from app.core.config import settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_hash_password_does_not_return_plaintext():
    hashed = hash_password("correct-horse-battery-staple")

    assert hashed != "correct-horse-battery-staple"
    assert hashed.startswith("$2b$")


def test_verify_password_round_trips():
    hashed = hash_password("correct-horse-battery-staple")

    assert verify_password("correct-horse-battery-staple", hashed) is True
    assert verify_password("wrong-password", hashed) is False


def test_create_access_token_round_trips_subject():
    token = create_access_token(data={"sub": "42"})

    payload = decode_access_token(token)

    assert payload["sub"] == "42"


def test_decode_access_token_rejects_expired_token():
    token = create_access_token(data={"sub": "42"}, expires_delta=timedelta(minutes=-1))

    with pytest.raises(JWTError):
        decode_access_token(token)


def test_decode_access_token_rejects_tampered_token():
    token = create_access_token(data={"sub": "42"})
    tampered = jwt.encode({"sub": "999"}, "wrong-secret", algorithm=settings.algorithm)

    with pytest.raises(JWTError):
        decode_access_token(tampered)
    # sanity: the original, correctly-signed token still decodes fine
    assert decode_access_token(token)["sub"] == "42"
