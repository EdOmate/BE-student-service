

from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from core.database import get_db
from core.response import ErrorResponse, SuccessResponse
from app.modules.auth.schema import ParentLoginRequest
from app.modules.auth.service import AuthService


auth_router = APIRouter(
    prefix="/api/v1"
)

@auth_router.get("/health")
async def get_health_info():
    return {
        "message": "Success: Service is running"
    }

@auth_router.post("/auth/parent-login")
async def user_login(
    data: ParentLoginRequest,
    db: Session = Depends(get_db),
):
    auth_data = AuthService.parent_login_username_password(
        db,
        data.username,
        data.password,
    )
    if not auth_data:
        return ErrorResponse(
            message="Invalid username or password",
            status_code=401,
        )
    return SuccessResponse(
        message="User Logged in",
        data=auth_data,
    )


@auth_router.get("/auth/profile")
async def user_profile(
    authorization: str = Header(None),
    db: Session = Depends(get_db),
):
    if not authorization or not authorization.startswith("Bearer "):
        return ErrorResponse(
            message="Authorization token is required",
            status_code=401,
        )

    token = authorization.split(" ", 1)[1].strip()
    profile_data = AuthService.get_parent_profile_by_token(db, token)

    if not profile_data:
        return ErrorResponse(
            message="Invalid or expired token",
            status_code=401,
        )

    return SuccessResponse(
        message="Profile fetched successfully",
        data=profile_data,
    )
