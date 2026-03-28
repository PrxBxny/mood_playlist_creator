from google import genai
from google.genai import types

from app.config import BaseConfig
from app.models.schemas import MoodRequest
from app.utils.exceptions import AIServiceError
from app.prompts.ai_tags import MOOD_TAGS_PROMPT



class AIService:
    def __init__(self, config: BaseConfig):
        self._client = genai.Client(api_key=config.AI_API_KEY)
        self._model = config.AI_MODEL

    def prompt_to_mood_tags(self, user_prompt: str) -> MoodRequest:
        try:
            response = self._client.models.generate_content(
                model=self._model,
                config=types.GenerateContentConfig(
                    system_instruction=MOOD_TAGS_PROMPT, # промпт из prompts/ai_tags
                    temperature=0.3,
                ),
                contents=[user_prompt]
            )

            if not response.text:
                raise AIServiceError("AI вернул пустой список")

            tags_raw = response.text.strip()
            tags_list = [tag.strip().lower() for tag in tags_raw.split(",")]
            mood = MoodRequest(mood_tags=tags_list)

            return mood

        except AIServiceError:
            raise  # перебрасываем наши исключения как есть
        except Exception as e:
            raise AIServiceError(f"AI недоступен: {e}") from e
