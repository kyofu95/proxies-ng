from uuid import UUID, uuid4

from app.core.exceptions import AlreadyExistsError
from app.core.security import PasswordHasher
from app.core.uow import SQLUnitOfWork
from app.models.user import User


class UserService:
    """
    Service class for handling operations related to users.

    This class provides methods for creating, retrieving, updating,
    and deleting users using the repository pattern.
    """

    def __init__(self, uow: SQLUnitOfWork) -> None:
        """
        Initialize the UserService with a unit-of-work instance.

        Args:
            uow (SQLUnitOfWork): The unit-of-work instance.
        """
        self.uow = uow

    async def create(self, login: str, password: str) -> User:
        """
        Create a new user with the provided login and password.

        The password will be securely hashed before storing in the database.
        Raises an exception if a user with the same login already exists.

        Args:
            login (str): The login for the new user.
            password (str): The plain-text password for the new user.

        Raises:
            AlreadyExistsError: If a user with the same login already exists.

        Returns:
            User: The newly created user object.
        """
        existing_user = await self.get_by_login(login)
        if existing_user:
            raise AlreadyExistsError("User with the same login already exist")

        hashed_password = PasswordHasher.hash(password)
        user = User(id=uuid4(), login=login, password=hashed_password)

        async with self.uow as uow:
            return await uow.user_repository.add(user)

    async def get_by_id(self, id_: UUID) -> User | None:
        """
        Retrieve a user by their unique ID.

        Args:
            id_ (UUID): The unique identifier of the user.

        Returns:
            User | None: The user object if found, otherwise None.
        """
        async with self.uow as uow:
            return await uow.user_repository.get_by_id(id_)

    async def get_by_login(self, login: str) -> User | None:
        """
        Retrieve a user by their login.

        Args:
            login (str): The login of the user.

        Returns:
            User | None: The user object if found, otherwise None.
        """
        async with self.uow as uow:
            return await uow.user_repository.get_by_login(login)

    async def get_by_login_with_auth(self, login: str, plain_password: str) -> User | None:
        """
        Retrieve a user by login and verify their password.

        This method fetches the user by login and compares the hashed password
        against the provided plaintext password. Returns the user if authentication
        is successful; otherwise, returns None.

        Args:
            login (str): The login of the user.
            plain_password (str): The plaintext password to verify.

        Returns:
            User | None: The authenticated user if credentials match, otherwise None.
        """
        async with self.uow as uow:
            user = await uow.user_repository.get_by_login(login)

        if not user:
            return None

        # check if password match
        encoded_password = PasswordHasher.hash(plain_password)
        if user.password != encoded_password:
            return None

        return user

    async def update(self, user: User) -> User:
        """
        Update an existing user in the database.

        Args:
            user (User): The user object with updated data.

        Returns:
            User: The updated user object.
        """
        async with self.uow as uow:
            return await uow.user_repository.update(user)

    async def remove(self, user: User) -> None:
        """
        Remove a user from the database.

        Args:
            user (User): The user object to be removed.
        """
        async with self.uow as uow:
            return await uow.user_repository.remove(user)
