from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.core.security import JWT

from .schemas.login import LoginRequest
from .utils.dependencies import UserServiceDep
from .utils.token_auth import CurrentUserDep

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", status_code=status.HTTP_200_OK)
async def login(user_data: LoginRequest, service: UserServiceDep) -> JSONResponse:
    """
    Authenticate the user and logs them in by setting an access token in a cookie.

    Args:
        user_data (LoginRequest): The login credentials of the user (username and password).
        service (UserServiceDep): The service responsible for retrieving user data.

    Returns:
        JSONResponse: A response containing a message indicating that the user has logged in.
    """
    user = await service.get_by_login_with_auth(user_data.username, user_data.password)

    if not user:
        content = {"detail": "incorrect login or password"}
        return JSONResponse(content=content, status_code=status.HTTP_401_UNAUTHORIZED)

    access_token = JWT.encode(str(user.id))

    content = {"detail": "logged in"}

    response = JSONResponse(content=content)

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/",
        max_age=3600,  # one hour
    )

    return response


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(_: CurrentUserDep) -> JSONResponse:
    """
    Log the user out by deleting the cookie with token cookie.

    Returns:
        JSONResponse: A response containing a message indicating that the user has logged out.
    """
    content = {"detail": "logged out"}

    response = JSONResponse(content=content)

    response.delete_cookie(
        "access_token",
        path="/",
    )

    return response
