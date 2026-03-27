from pydantic import BaseModel, Field, field_validator, StringConstraints # Валидация данных
from typing import Optional, Annotated
"""
BaseModel — базовый класс для создания моделей данных.

Field — функция для описания дополнительных свойств поля
(значение по умолчанию, ограничения и т.д.).

field_validator — декоратор, который позволяет добавлять
собственную логику проверки для конкретного поля.
"""

# --- Входящие данные от фронтенда ---
class PlaylistRequest(BaseModel):
    """
    Запрос пользователя на генерацию плейлиста
    Pydantic автоматически валидирует при создании объекта.
    Если данные невалидны — ValidationError до того как код выполнится
    """
    prompt: str = Field(..., min_length=1, max_length=500) # ... эквивалентно required=True, т.е. обязательно что-то передать
    number_of_tracks: int = Field(default=10, ge=1, le=100)

    @field_validator("prompt") # снизу будет валидатор, который будет вызываться при передаче в промпт строки
    @classmethod # декоратор, который превращает следующий метод в метод класса, Это нужно, потому что валидаторы Pydantic должны быть методами класса, чтобы работать на уровне класса, а не конкретного объекта
    def strip_prompt(cls, value: str) -> str:
        # Он принимает два параметра: cls (ссылка на класс PlaylistRequest) и value (значение поля prompt, которое будет передано в валидатор).
        return value.strip() # удаление пробелов и т.п.


# --- Внутренние данные между сервисами ---
# Данные обработанные AI (между сервисами)
# Пример данных от клиента (JSON)
# { "items": ["python", "flask", "pydantic"] }
ValidTags = Annotated[str, StringConstraints(min_length=1, max_length=20)]

class MoodRequest(BaseModel):
    mood_tags: list[ValidTags] = Field(..., min_length=1, max_length=5)

# Параметры для LastFM (внутри приложения)
class LastfmParams(BaseModel):
    tag: str = Field(...)
    page: int = Field(default=1, ge=1, le=100)
    limit: int = Field(default=5, ge=1, le=20)
    method: str = "tag.getTopTracks"
    format: str = "json"

# --- Исходящие данные фронтенду ---
# Один трек в плейлисте
class TrackResponse(BaseModel):
    name: str
    artist: str
    # lastfm_url: str                # Last.fm даёт ссылку на страницу трека
    # image_url: Optional[str]       # Last.fm даёт обложку (несколько размеров)
    # listeners: Optional[int]       # Last.fm возвращает количество слушателей
    # mbid: Optional[str]            # MusicBrainz ID (Last.fm его возвращает)

# Итоговый ответ API
class PlaylistResponse(BaseModel):
    tracks: list[TrackResponse]
    explanation: str
    mood_summary: str