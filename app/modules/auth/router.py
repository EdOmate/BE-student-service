

from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session
from core.database import get_db
from core.response import ErrorResponse, SuccessResponse
from app.modules.auth.schema import (
    ParentLoginRequest,
    StudentLoginRequest,
    StudentLoginTokenRequest,
    TokenRefreshRequest,
)
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
    profile_data = AuthService.get_profile_by_token(db, token)

    if not profile_data:
        return ErrorResponse(
            message="Invalid or expired token",
            status_code=401,
        )

    return SuccessResponse(
        message="Profile fetched successfully",
        data=profile_data,
    )


@auth_router.post("/auth/student-login-token")
async def create_student_login_token(
    data: StudentLoginTokenRequest | None = None,
    authorization: str = Header(None),
    db: Session = Depends(get_db),
):
    if not authorization or not authorization.startswith("Bearer "):
        return ErrorResponse(
            message="Authorization token is required",
            status_code=401,
        )

    token = authorization.split(" ", 1)[1].strip()
    session_data = AuthService.create_student_login_token_from_parent_token(
        db,
        token,
        device_id=data.device_id if data else None,
        device_name=data.device_name if data else None,
    )

    if not session_data:
        return ErrorResponse(
            message="Invalid parent session",
            status_code=401,
        )

    return SuccessResponse(
        message="Student login token created successfully",
        data=session_data,
    )


@auth_router.post("/auth/student-login")
async def student_login(
    data: StudentLoginRequest,
    db: Session = Depends(get_db),
):
    session_data = AuthService.login_student_with_token(
        db,
        data.token,
        device_id=data.device_id,
        device_name=data.device_name,
    )

    if not session_data:
        return ErrorResponse(
            message="Invalid or expired student login token",
            status_code=401,
        )

    return SuccessResponse(
        message="Student logged in successfully",
        data=session_data,
    )


@auth_router.post("/auth/refresh")
async def refresh_tokens(
    data: TokenRefreshRequest,
    db: Session = Depends(get_db),
):
    refreshed = AuthService.refresh_session_tokens(db, data.refresh_token)

    if not refreshed:
        return ErrorResponse(
            message="Invalid or expired refresh token",
            status_code=401,
        )

    return SuccessResponse(
        message="Token refreshed successfully",
        data=refreshed,
    )
