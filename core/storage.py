"""S3-backed file storage utilities."""

import mimetypes
import posixpath
from pathlib import PurePosixPath
from typing import BinaryIO
from uuid import uuid4

import boto3
from botocore.exceptions import ClientError
from fastapi import UploadFile

from core.config import (
    AWS_ACCESS_KEY_ID,
    AWS_S3_ENDPOINT_URL,
    AWS_S3_REGION_NAME,
    AWS_SECRET_ACCESS_KEY,
    AWS_STORAGE_BUCKET_NAME,
    STORAGE_SERVICE,
)


class StorageConfigurationError(RuntimeError):
    """Raised when S3 storage has not been configured."""


class S3StorageService:
    def __init__(self):
        if not AWS_STORAGE_BUCKET_NAME:
            raise StorageConfigurationError(
                "AWS_STORAGE_BUCKET_NAME is required for S3 storage"
            )

        client_options = {
            "service_name": "s3",
            "region_name": AWS_S3_REGION_NAME,
        }
        if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
            client_options.update(
                aws_access_key_id=AWS_ACCESS_KEY_ID,
                aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            )
        if AWS_S3_ENDPOINT_URL:
            client_options["endpoint_url"] = AWS_S3_ENDPOINT_URL

        self.bucket_name = AWS_STORAGE_BUCKET_NAME
        self.client = boto3.client(**client_options)

    @staticmethod
    def _safe_directory(directory: str) -> str:
        directory = directory.strip().strip("/")
        if not directory:
            return "uploads"
        path = PurePosixPath(directory)
        if ".." in path.parts:
            raise ValueError("Invalid storage directory")
        return path.as_posix()

    @staticmethod
    def _file_extension(filename: str) -> str:
        extension = PurePosixPath(filename).suffix.lower()
        if not extension:
            raise ValueError("File must have an extension")
        return extension

    @classmethod
    def generate_key(cls, filename: str, directory: str = "uploads") -> str:
        extension = cls._file_extension(filename)
        safe_directory = cls._safe_directory(directory)
        return posixpath.join(safe_directory, f"{uuid4()}{extension}")

    @staticmethod
    def file_url(key: str) -> str:
        if STORAGE_SERVICE:
            return f"{STORAGE_SERVICE.rstrip('/')}/{key.lstrip('/')}"
        return key

    def upload_stream(
        self,
        stream: BinaryIO,
        filename: str,
        directory: str = "uploads",
        content_type: str | None = None,
        file_type: str | None = None,
    ) -> dict:
        key = self.generate_key(filename, directory)
        resolved_content_type = (
            content_type
            or mimetypes.guess_type(filename)[0]
            or "application/octet-stream"
        )
        self.client.upload_fileobj(
            stream,
            self.bucket_name,
            key,
            ExtraArgs={"ContentType": resolved_content_type},
        )
        return {
            "file_name": PurePosixPath(key).name,
            "file_url": key,
            "absolute_url": self.file_url(key),
            "original_name": PurePosixPath(filename).name,
            "file_extension": PurePosixPath(filename).suffix.lower(),
            "file_type": file_type,
        }

    def upload_file(
        self,
        file: UploadFile,
        directory: str = "uploads",
        file_type: str | None = None,
    ) -> dict:
        if not file.filename:
            raise ValueError("File name is required")
        return self.upload_stream(
            stream=file.file,
            filename=file.filename,
            directory=directory,
            content_type=file.content_type,
            file_type=file_type,
        )

    def delete_file(self, key: str) -> None:
        self.client.delete_object(Bucket=self.bucket_name, Key=key.lstrip("/"))

    def get_file_size(self, key: str) -> int | None:
        try:
            response = self.client.head_object(
                Bucket=self.bucket_name,
                Key=key.lstrip("/"),
            )
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code")
            if error_code in {"404", "NoSuchKey", "NotFound"}:
                return None
            raise
        return response["ContentLength"]

    def generate_presigned_download_url(
        self,
        key: str,
        expires_in: int = 3600,
    ) -> str:
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket_name, "Key": key.lstrip("/")},
            ExpiresIn=expires_in,
        )


def get_storage_service() -> S3StorageService:
    """FastAPI dependency for S3-backed operations."""
    return S3StorageService()
