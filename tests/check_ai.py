from dotenv import load_dotenv
load_dotenv()

from app.config import get_config
from app.services.ai_service import AIService

cfg = get_config()
service = AIService(config=cfg)

prompts = [
    # "что-то агрессивное для тренировок, типа фонка",
    "спокойный джазовый рэп для учебы",
    "хочу послушать Crystal Castles или что-то на подобие",
    "хочу плейлист в стиле Post Malone",
    "мне нравится Scarlxrd",
    "хочу плейлист в стиле русского эмо",
    "хочу что-то по типу Machine Gun Kelly",
    "в последнее время нравится Lana Del Rey, сделай что-то на подобие",
    "хочу что-то нежное, но электронное, как музыка для ночной поездки",
    "веселая и позитивная музыка для вечеринки",
    "что-то думерское",
    "хочу увидеть в плейлесте что-то агрессивное и грустное, например пусть там будет фонк и что-то в стиле кишлака"
]

for prompt in prompts:
    print(f"промпт: {prompt}")
    result = service.prompt_to_mood_tags(prompt)
    print(f"результат: {result}\n")
