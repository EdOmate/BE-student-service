"""Business logic for utility APIs."""

from fastapi import UploadFile

from app.modules.utils.schema import FileUploadResponse
from core.storage import S3StorageService


class FileService:
    @staticmethod
    def upload_file(
        storage: S3StorageService,
        file: UploadFile,
        file_type: str | None = None,
    ) -> FileUploadResponse:
        result = storage.upload_file(
            file=file,
            directory="uploads",
            file_type=file_type,
        )
        return FileUploadResponse(**result)
