from fastapi import APIRouter, HTTPException, Response, status

from .schemas.status import StatusMessageResponse
from .schemas.user import UserPasswordRequest
from .utils.dependencies import UserServiceDep
from .utils.token_auth import CurrentUserDep

router = APIRouter(prefix="/user")


@router.post("/change_password", status_code=status.HTTP_202_ACCEPTED)
async def change_password(
    response: Response,
    password_schema: UserPasswordRequest,
    current_user: CurrentUserDep,
    user_service: UserServiceDep,
) -> StatusMessageResponse:
    """
    Change the password for the currently authenticated user.

    This endpoint verifies the old password before updating it to a new one.
    If the verification fails, a 401 Unauthorized response is returned.
    On successful password change, the user's access token cookie is removed
    to force re-authentication.

    Args:
        response (Response): The HTTP response object used to delete the access token cookie.
        password_schema (UserPasswordRequest): Schema containing the old and new passwords.
        current_user (CurrentUserDep): The currently authenticated user.
        user_service (UserServiceDep): Service responsible for user management.

    Raises:
        HTTPException: If the old password is invalid (401 Unauthorized).

    Returns:
        StatusMessageResponse: A message indicating successful password change.
    """
    # validate old password
    user = await user_service.get_by_login_with_auth(current_user.login, password_schema.old_password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid login or password")

    # change password
    await user_service.change_password(user, password_schema.new_password)

    # user auth changed, kick them out
    response.delete_cookie("access_token")

    return StatusMessageResponse(detail="password changed successfully")
