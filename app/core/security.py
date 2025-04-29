from argon2 import PasswordHasher
from argon2.exceptions import Argon2Error, InvalidHashError, VerifyMismatchError

from .exceptions import HashingError

hasher = PasswordHasher()


class Hasher:
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
