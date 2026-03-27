from dotenv import load_dotenv
load_dotenv()

from app.config import get_config
from app.services.ai_service import AIService

cfg = get_config()
service = AIService(config=cfg)

prompts = [
    "хочу бодрый рок для тренировки",
    "что-то грустное и медленное",
    "весёлая латиноамериканская музыка для вечеринки",
]

for prompt in prompts:
    print(f"промпт: {prompt}")
    result = service.prompt_to_text(prompt)
    print(f"результат: {result}\n")
