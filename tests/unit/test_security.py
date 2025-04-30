from datetime import datetime, timedelta, timezone

import pytest
from argon2.exceptions import Argon2Error, InvalidHashError
from jwt import encode as jwt_encode

from app.core.exceptions import HashingError
from app.core.security import Hasher, Token, TokenError


@pytest.mark.unit
@pytest.mark.asyncio
async def test_hasher_hash() -> None:
    plaintext = "abc"

    hashed = Hasher.hash(plaintext)
    assert hashed
    assert isinstance(hashed, str)
    assert hashed != plaintext


@pytest.mark.unit
@pytest.mark.asyncio
async def test_hasher_verify() -> None:
    plaintext = "abc"

    hashed = Hasher.hash(plaintext)

    assert Hasher.verify(hashed, plaintext) == True


@pytest.mark.unit
@pytest.mark.asyncio
async def test_hasher_verify_wrong_password() -> None:
    plaintext = "abc"
    plaintext_wrong = "xyz"

    hashed = Hasher.hash(plaintext)

    assert Hasher.verify(hashed, plaintext_wrong) == False


@pytest.mark.unit
@pytest.mark.asyncio
async def test_haser_raises_hashing_error(monkeypatch):
    from argon2 import PasswordHasher

    def broken_hash(self, password):
        raise Argon2Error("something went wrong")

    monkeypatch.setattr(PasswordHasher, "hash", broken_hash)
    with pytest.raises(HashingError, match="Failed to hash password"):
        Hasher.hash("password")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_hasher_verify_raises_hashing_error_on_invalid_hash(monkeypatch):
    from argon2 import PasswordHasher

    def broken_verify(self, hash, password):
        raise InvalidHashError("bad hash")

    monkeypatch.setattr(PasswordHasher, "verify", broken_verify)
    with pytest.raises(HashingError, match="Failed to verify password"):
        Hasher.verify("invalid_hash", "password")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_hasher_verify_raises_hashing_error_on_generic_argon2(monkeypatch):
    from argon2 import PasswordHasher

    def broken_verify(self, hash, password):
        raise Argon2Error("generic error")

    monkeypatch.setattr(PasswordHasher, "verify", broken_verify)
    with pytest.raises(HashingError, match="Failed to verify password"):
        Hasher.verify("some_hash", "password")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_token_encode_valid(monkeypatch):
    user_id = "user123"
    token = Token.encode(user_id)
    assert isinstance(token, str)

    decoded_id = Token.decode(token)
    assert decoded_id == user_id


@pytest.mark.unit
@pytest.mark.asyncio
async def test_token_decode_invalid(monkeypatch):
    with pytest.raises(TokenError, match="Invalid token"):
        Token.decode("not.a.valid.token")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_token_decode_empty():
    with pytest.raises(TokenError, match="Token is empty"):
        Token.decode("")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_token_decode_expired(monkeypatch):
    expired_payload = {
        "sub": "user123",
        "iat": datetime(2000, 1, 1, tzinfo=timezone.utc) - timedelta(minutes=10),
        "exp": datetime(2000, 1, 1, tzinfo=timezone.utc) - timedelta(minutes=5),
    }

    def patched_encode(payload, key, algorithm):
        del payload
        return jwt_encode(payload=expired_payload, key=key, algorithm=algorithm)

    monkeypatch.setattr("app.core.security.jwt_encode", patched_encode)

    expired_token = Token.encode("user123")

    with pytest.raises(TokenError, match="Expired token signature"):
        Token.decode(expired_token)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_token_decode_missing_sub(monkeypatch):
    payload_missing = {
        "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        "iat": datetime.now(timezone.utc),
        # "sub" is missing
    }

    def patched_encode(payload, key, algorithm):
        del payload
        return jwt_encode(payload=payload_missing, key=key, algorithm=algorithm)

    monkeypatch.setattr("app.core.security.jwt_encode", patched_encode)

    token = Token.encode("user123")

    with pytest.raises(TokenError, match="Invalid token payload"):
        Token.decode(token)
