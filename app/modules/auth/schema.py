from pydantic import BaseModel, Field


class ParentLoginRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class ParentLoginResponse(BaseModel):
    id: int
    username: str | None = None
    student_id: int
    access_token: str | None = None
    refresh_token: str | None = None


class StudentSessionRequest(BaseModel):
    device_id: str | None = None
    device_name: str | None = None


class StudentLoginTokenRequest(BaseModel):
    device_id: str | None = None
    device_name: str | None = None


class StudentLoginRequest(BaseModel):
    token: str = Field(..., min_length=1)
    device_id: str | None = None
    device_name: str | None = None


class TokenRefreshRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1)
