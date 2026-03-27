from google import genai
from google.genai import types

from app.config import BaseConfig
from app.utils.exceptions import AIServiceError



SYSTEM_PROMPT = """
Ты — эксперт по музыкальной метадате Last.fm. Твоя задача: переводить запросы пользователя в список поисковых тегов (от 1 до 5 слов).
Правила формирования ответа:
1. Приоритет жанров: Если в запросе явно или косвенно упоминается жанр (например, "гитары" -> rock, "биты" -> hip-hop), он должен стоять на первом месте.
2. Количество: Строго от 1 до 5 тегов.
3. Формат: Только английский язык, через запятую, без лишнего текста и кавычек.
4. Запреты: НЕ используй слова music, songs, playlist, cool, good, best.
5. Используй наиболее популярные теги из сообщества Last.fm"
"""

class AIService:
    def __init__(self, config: BaseConfig):
        self._client = genai.Client(api_key=config.AI_API_KEY)
        self._model = config.AI_MODEL

    def prompt_to_text(self, user_prompt: str) -> list[str]:
        try:
            response = self._client.models.generate_content(
                model=self._model,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.3,
                ),
                contents=[user_prompt]
            )


            if not response.text:
                raise AIServiceError("AI вернул пустой список")

            tags_raw = response.text.strip()
            tags_list = [tag.strip().lower() for tag in tags_raw.split(",")]

            return tags_list

        except AIServiceError:
            raise  # перебрасываем наши исключения как есть
        except Exception as e:
            raise AIServiceError(f"AI недоступен: {e}") from e
