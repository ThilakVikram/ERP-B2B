from pydantic import EmailStr, Field, model_validator

from app.schemas.base import CamelModel
from app.schemas.user import UserOut


class SignupRequest(CamelModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    confirm_password: str

    @model_validator(mode="after")
    def passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class LoginRequest(CamelModel):
    email: EmailStr
    password: str
    remember_me: bool = False


class TokenResponse(CamelModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user: UserOut
