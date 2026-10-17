

from fastapi import APIRouter, Depends
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
from app.modules.auth.dependencies import AuthenticatedStudent, get_authenticated_parent
from core.redis import redis_client

auth_router = APIRouter(
    prefix="/api/v1"
)

@auth_router.get("/health")
async def get_health_info():
    print(redis_client.get("name"))
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


@auth_router.post("/auth/student-login-token")
async def create_student_login_token(
    data: StudentLoginTokenRequest | None = None,
    auth: AuthenticatedStudent = Depends(get_authenticated_parent),
    db: Session = Depends(get_db),
):
    session_data = AuthService.create_student_login_token_for_student(
        db,
        parent_id=auth.parent_id,
        student_id=auth.student_id,
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
