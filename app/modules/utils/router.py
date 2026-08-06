"""Shared utility API routes."""

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.modules.auth.dependencies import (
    AuthenticatedStudent,
    get_authenticated_student,
)
from app.modules.utils.service import FileService
from core.response import ErrorResponse, SuccessResponse
from core.storage import (
    S3StorageService,
    StorageConfigurationError,
)


utils_router = APIRouter(
    prefix="/org/utils",
    tags=["Utils"],
)


@utils_router.post("/file-upload", status_code=201)
def upload_file(
    file: UploadFile | None = File(default=None),
    file_type: str | None = Form(default=None),
    _auth: AuthenticatedStudent = Depends(get_authenticated_student),
):
    if file is None:
        return ErrorResponse(
            message="No file provided",
            status_code=400,
        )

    try:
        storage = S3StorageService()
        result = FileService.upload_file(
            storage=storage,
            file=file,
            file_type=file_type,
        )
    except (ValueError, StorageConfigurationError) as exc:
        return ErrorResponse(
            message=str(exc),
            status_code=400,
        )
    except Exception:
        return ErrorResponse(
            message="File upload failed",
            status_code=500,
        )

    return SuccessResponse(
        message="File uploaded successfully",
        data=result.model_dump(mode="json"),
        status_code=201,
    )
