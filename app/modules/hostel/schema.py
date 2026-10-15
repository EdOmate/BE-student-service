from pydantic import BaseModel, Field, field_validator


class CreateHostelComplaintRequest(BaseModel):
    target_type: int = Field(default=4, ge=1, le=5)
    category: int
    priority: int = Field(default=2, ge=1, le=4)
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1, max_length=5000)

    @field_validator("category")
    @classmethod
    def validate_category(cls, value: int) -> int:
        if value not in {1, 2, 3, 4, 5, 6, 99}:
            raise ValueError("Invalid complaint category")
        return value

    @field_validator("title", "description")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field is required")
        return value
