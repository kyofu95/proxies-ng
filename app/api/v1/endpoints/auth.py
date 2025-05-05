from fastapi import APIRouter, HTTPException, status
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

    Raises:
        HTTPException: If the login credentials are incorrect, a 401 error is raised.

    Returns:
        JSONResponse: A response containing a message indicating that the user has logged in.
    """
    user = await service.get_by_login_with_auth(user_data.username, user_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect login or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = JWT.encode(str(user.id))

    content = {"message": "logged in"}

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
    content = {"message": "logged out"}

    response = JSONResponse(content=content)

    response.delete_cookie(
        "access_token",
        path="/",
    )

    return response
