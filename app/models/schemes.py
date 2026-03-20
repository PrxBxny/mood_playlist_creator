from pydantic import BaseModel, Field, field_validator, EmailStr # Валидация данных
from typing import Optional
"""
BaseModel — базовый класс для создания моделей данных.

Field — функция для описания дополнительных свойств поля
(значение по умолчанию, ограничения и т.д.).

field_validator — декоратор, который позволяет добавлять
собственную логику проверки для конкретного поля.
"""

class User(BaseModel):
    id: int
    email: EmailStr
    password: str = Field(..., min_length=5, max_length=99)

    def to_dict(self):
        return {"id": self.id, "email": self.email, "password": self.password}

# --- Входящие данные от фронтенда ---
class PlaylistRequest(BaseModel):
    """
    Запрос пользователя на генерацию плейлиста
    Pydantic автоматически валидирует при создании объекта.
    Если данные невалидны — ValidationError до того как код выполнится
    """
    prompt: str = Field(..., min_length=1, max_length=500) # ... эквивалентно required=True, т.е. обязательно что-то передать
    size: int = Field(default=10, ge=1, le=20)

    @field_validator("prompt") # снизу будет валидатор, который будет вызываться при передаче в промпт строки
    @classmethod # декоратор, который превращает следующий метод в метод класса, Это нужно, потому что валидаторы Pydantic должны быть методами класса, чтобы работать на уровне класса, а не конкретного объекта
    def strip_prompt(cls, value: str) -> str:
        # Он принимает два параметра: cls (ссылка на класс PlaylistRequest) и value (значение поля prompt, которое будет передано в валидатор).
        return value.strip() # удаление пробелов и т.п.

class MoodRequest(BaseModel):
    mood: str = Field(..., min_length=1, max_length=100)
    size: int = Field(default=10, ge=1, le=20)


# --- Внутренние данные между сервисами ---
# Параметры для Spotify (внутри приложения)
class SpotifyParams(BaseModel):
    seed_genres: list[str]
    target_energy: Optional[float]
    ...


# --- Исходящие данные фронтенду ---
# Один трек в плейлисте
class TrackResponse(BaseModel):
    id: str
    name: str
    artist: str
    album: str
    preview_url: Optional[str]
    spotify_url: str
    image_url: Optional[str]
    duration_ms: int

# Итоговый ответ API
class PlaylistResponse(BaseModel):
    tracks: list[TrackResponse]
    explanation: str
    mood_summary: str