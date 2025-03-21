class BaseError(Exception):
    """
    Base class for custom application exceptions.

    All custom exceptions in the application should inherit from this class.
    """


class NotFoundError(BaseError):
    """
    Exception raised when a requested entity is not found.

    This exception should be used to signal that an operation failed because
    the specified resource could not be located.
    """

class AlreadyExistsError(BaseError):
    """
    Exception raised when attempting to create a resource that already exists.

    This exception is typically used to indicate that an attempt was made to create
    or add an entity that already exists in the system.
    """


class DatabaseError(BaseError):
    """
    Exception raised for database-related errors.

    This exception should be used when an error occurs while interacting
    with the database, such as connection failures or query issues.
    """
