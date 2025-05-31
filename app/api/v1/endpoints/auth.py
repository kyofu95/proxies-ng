from fastapi import APIRouter, HTTPException, Response, status

from app.core.security import JWT

from .schemas.login import LoginRequest
from .schemas.status import StatusMessageResponse
from .utils.dependencies import UserServiceDep
from .utils.token_auth import CurrentUserDep

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", status_code=status.HTTP_200_OK)
async def login(response: Response, user_data: LoginRequest, service: UserServiceDep) -> StatusMessageResponse:
    """
    Authenticate the user and logs them in by setting an access token in a cookie.

    Args:
        response (Response): The HTTP response object used to set the cookie.
        user_data (LoginRequest): The login credentials of the user (username and password).
        service (UserServiceDep): The service responsible for retrieving user data.

    Returns:
        StatusMessageResponse: A response containing a message indicating that the user has logged in.
    """
    user = await service.get_by_login_with_auth(user_data.username, user_data.password)

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="incorrect login or password")

    access_token = JWT.encode(str(user.id))

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/",
        max_age=3600,  # one hour
    )

    return StatusMessageResponse(detail="logged in")


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(response: Response, _: CurrentUserDep) -> StatusMessageResponse:
    """
    Log the user out by deleting the cookie with token cookie.

    Args:
        response (Response): The HTTP response object used to clear the cookie.
        _ (CurrentUserDep): Dependency-injected current user (used to enforce authentication).

    Returns:
        StatusMessageResponse: A response containing a message indicating that the user has logged out.
    """
    response.delete_cookie(
        "access_token",
        path="/",
    )

    return StatusMessageResponse(detail="logged out")
