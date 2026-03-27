from pydantic import BaseModel, Field, field_validator, EmailStr, StringConstraints # Валидация данных
from typing import Optional, Annotated


class User(BaseModel):
    id: int
    email: EmailStr
    password: str = Field(..., min_length=5, max_length=99)

    def to_dict(self):
        return {"id": self.id, "email": self.email, "password": self.password}