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


class CountryCodeError(BaseError):
    """
    Exception raised when an invalid or unsupported country code is encountered.

    This exception should be used to indicate issues related to country code
    validation, normalization, or lookup operations.
    """


class HashingError(BaseError):
    """
    Exception raised for errors during password or data hashing operations.

    This exception should be used when hashing fails due to configuration issues,
    unsupported algorithms, or unexpected input data.
    """


class TokenError(BaseError):
    """
    Exception raised for errors related to JWT token creation or validation.

    This exception should be used when token encoding, decoding, or validation
    fails due to expiration, tampering, or incorrect format.
    """


class LogicError(BaseError):
    """
    Exception raised when application logic constraints are violated.

    This exception should be used to indicate violations of business logic rules
    or invalid combinations of parameters or states.
    """
