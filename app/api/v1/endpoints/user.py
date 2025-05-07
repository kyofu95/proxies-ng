from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from .schemas.user import UserPasswordRequest
from .utils.dependencies import UserServiceDep
from .utils.token_auth import CurrentUserDep

router = APIRouter(prefix="/user")


@router.post("/change_password", status_code=status.HTTP_202_ACCEPTED)
async def change_password(
    password_schema: UserPasswordRequest,
    current_user: CurrentUserDep,
    user_service: UserServiceDep,
) -> JSONResponse:
    """
    Change the password for the currently authenticated user.

    This endpoint verifies the old password before updating it to a new one.
    If the verification fails, a 401 Unauthorized response is returned.
    On successful password change, the user's access token cookie is removed
    to force re-authentication.

    Args:
        password_schema (UserPasswordRequest): Schema containing the old and new passwords.
        current_user (CurrentUserDep): Dependency that provides the currently authenticated user.
        user_service (UserServiceDep): Dependency that provides access to user-related operations.

    Returns:
        JSONResponse: A JSON response indicating the result of the operation.
            - 202 Accepted on success.
            - 401 Unauthorized if the old password is invalid.
    """
    # validate old password
    user = await user_service.get_by_login_with_auth(current_user.login, password_schema.old_password)
    if not user:
        content = {"detail": "invalid login or password."}
        return JSONResponse(content=content, status_code=status.HTTP_401_UNAUTHORIZED)

    # change password
    await user_service.change_password(user, password_schema.new_password)

    content = {"detail": "password changed successfully"}
    response = JSONResponse(content=content, status_code=status.HTTP_202_ACCEPTED)

    # user auth changed, kick them out
    response.delete_cookie("access_token")

    return response
