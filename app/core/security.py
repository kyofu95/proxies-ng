from datetime import datetime, timedelta, timezone
from typing import Any

from argon2 import PasswordHasher as Argon2Hasher
from argon2.exceptions import Argon2Error, InvalidHashError, VerifyMismatchError
from jwt import decode as jwt_decode
from jwt import encode as jwt_encode
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError, PyJWTError

from .config import jwt_settings
from .exceptions import HashingError, TokenError

hasher = Argon2Hasher()


class PasswordHasher:
    """
    Utility class for password hashing and verification using Argon2.

    This class wraps the `argon2.PasswordHasher` to provide password hashing
    and verification functionality with proper exception handling.
    """

    @staticmethod
    def hash(password: str) -> str:
        """
        Generate a secure hash for the given plaintext password.

        Args:
            password (str): The plaintext password to hash.

        Raises:
            HashingError: If hashing fails due to an internal Argon2 error.

        Returns:
            str: The hashed password.
        """
        try:
            return hasher.hash(password)
        except Argon2Error as exc:
            raise HashingError("Failed to hash password") from exc

    @staticmethod
    def verify(hashed_password: str, plaintext_password: str) -> bool:
        """
        Verify whether a plaintext password matches its hashed counterpart.

        Args:
            hashed_password (str): The stored hash to verify against.
            plaintext_password (str): The plaintext password to verify.

        Raises:
            HashingError: If verification fails due to an internal Argon2 error.

        Returns:
            bool: True if the password matches, False if it does not.
        """
        try:
            return hasher.verify(hash=hashed_password, password=plaintext_password)
        except VerifyMismatchError:
            return False
        except (Argon2Error, InvalidHashError) as exc:
            raise HashingError("Failed to verify password") from exc


class JWT:
    """
    Utility class for encoding and decoding JWT tokens.

    This class provides static methods to generate and validate JSON Web Tokens (JWT)
    for user authentication, using the configured secret key and algorithm.
    """

    @staticmethod
    def encode(user_id: str) -> str:
        """
        Create a JWT access token for the given user ID.

        The token includes an expiration (`exp`), issued at (`iat`), and subject (`sub`) claim.

        Args:
            user_id (str): The ID of the user for whom the token is being created.

        Raises:
            TokenError: If encoding the token fails due to a JWT error.

        Returns:
            str: The encoded JWT token as a string.
        """
        delta = timedelta(minutes=jwt_settings.access_token_expiry)

        payload = {
            "exp": datetime.now(timezone.utc) + delta,
            "iat": datetime.now(timezone.utc),
            "sub": str(user_id),
        }

        try:
            token = jwt_encode(payload=payload, key=jwt_settings.secret_key, algorithm=jwt_settings.algorithm)
        except PyJWTError as exc:
            raise TokenError("Token encode failure") from exc

        return token

    @staticmethod
    def decode(token: str) -> str:
        """
        Decode a JWT token and extract the user ID.

        Args:
            token (str): The JWT token to decode.

        Raises:
            TokenError: If the token is empty, expired, invalid, or lacks a user ID.

        Returns:
            str: The user ID extracted from the token.
        """
        if not token:
            raise TokenError("Token is empty")

        try:
            payload: dict[str, Any] = jwt_decode(
                jwt=token,
                key=jwt_settings.secret_key,
                algorithms=[jwt_settings.algorithm],
            )
        except ExpiredSignatureError as exc:
            raise TokenError("Expired token signature") from exc
        except InvalidTokenError as exc:
            raise TokenError("Invalid token") from exc

        user_id = payload.get("sub")
        if not user_id:
            raise TokenError("Invalid token payload")

        return str(user_id)
