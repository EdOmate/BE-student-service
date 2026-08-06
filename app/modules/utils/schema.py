"""Schemas for utility APIs."""

from pydantic import BaseModel


class FileUploadResponse(BaseModel):
    file_name: str
    file_url: str
    absolute_url: str
    original_name: str
    file_extension: str
    file_type: str | None = None
