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
