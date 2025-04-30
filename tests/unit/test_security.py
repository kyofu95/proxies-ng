import pytest
from argon2.exceptions import Argon2Error, InvalidHashError

from app.core.exceptions import HashingError
from app.core.security import Hasher


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
