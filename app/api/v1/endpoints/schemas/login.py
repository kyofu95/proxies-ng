from pydantic import BaseModel


class LoginRequest(BaseModel):
    """
    Schema for user login request.

    This class defines the structure for the user login request, which includes
    a username and password.

    Attributes:
        username (str): The username of the user.
        password (str): The password of the user.
    """

    username: str
    password: str
