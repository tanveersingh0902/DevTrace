from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr, field_validator


class EmailRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    email: Annotated[EmailStr, Field(max_length=254)]

    @field_validator("email", mode="before")
    @classmethod
    def trim_email(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        # DevTrace treats the entire address as case insensitive; do not rewrite aliases.
        return value.lower()


class LoginRequest(EmailRequest):
    password: Annotated[SecretStr, Field(min_length=1, max_length=128)]


class AccessResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RegistrationRequest(EmailRequest):
    password: Annotated[SecretStr, Field(min_length=12, max_length=128)]
    display_name: Annotated[str, Field(min_length=1, max_length=100)]

    @field_validator("display_name")
    @classmethod
    def clean_display_name(cls, value: str) -> str:
        value = value.strip()
        if not value or any(ord(character) < 32 or ord(character) == 127 for character in value):
            raise ValueError("Display name must contain visible text and no control characters.")
        return value


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    display_name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @field_validator("created_at", "updated_at")
    @classmethod
    def utc_timestamp(cls, value: datetime) -> datetime:
        return value.astimezone(timezone.utc)
