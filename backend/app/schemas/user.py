from datetime import datetime

from pydantic import EmailStr

from app.schemas.base import CamelModel


class UserOut(CamelModel):
    id: int
    email: EmailStr
    username: str
    first_name: str
    last_name: str
    is_active: bool
    created_at: datetime
