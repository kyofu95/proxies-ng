from fastapi import APIRouter, HTTPException, Response, status
from fastapi.responses import JSONResponse

from app.core.security import JWT

from .schemas.login import LoginRequest
from .utils.dependencies import UserServiceDep

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", status_code=status.HTTP_200_OK)
async def login(user_data: LoginRequest, service: UserServiceDep, response: Response) -> JSONResponse:
    """
    Authenticate the user and logs them in by setting an access token in a cookie.

    Args:
        user_data (LoginRequest): The login credentials of the user (username and password).
        service (UserServiceDep): The service responsible for retrieving user data.
        response (Response): The FastAPI response object, used to set cookies.

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

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/",
        max_age=3600,  # one hour
    )

    content = {"message": "logged in"}

    return JSONResponse(content=content)


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(response: Response) -> JSONResponse:
    """
    Log the user out by deleting the cookie with token cookie.

    Args:
        response (Response): The FastAPI response object, used to delete cookies.

    Returns:
        JSONResponse: A response containing a message indicating that the user has logged out.
    """
    response.delete_cookie(
        "access_token",
        path="/",
    )

    content = {"message": "logged out"}

    return JSONResponse(content=content)
