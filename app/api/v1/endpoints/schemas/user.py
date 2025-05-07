from pydantic import BaseModel


class UserPasswordRequest(BaseModel):
    """
    Request schema for updating a user's password.

    Attributes:
        old_password (str): The current password of the user.
        new_password (str): The new password to be set for the user.
    """

    old_password: str
    new_password: str
