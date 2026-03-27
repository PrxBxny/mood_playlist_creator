import os
from dataclasses import dataclass


@dataclass(frozen=True)
class BaseConfig:
    LASTFM_API_KEY: str = os.getenv("LASTFM_API_KEY", "")
    LASTFM_SECRET: str = os.getenv("LASTFM_SECRET", "")
    LASTFM_API_BASE_URL: str = "https://ws.audioscrobbler.com/2.0/"

    AI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    AI_MODEL: str = "gemini-3-flash-preview"


@dataclass(frozen=True)
class DevelopmentConfig(BaseConfig):
    DEBUG: bool = True
    TESTING: bool = False


@dataclass(frozen=True)
class TestingConfig(BaseConfig):
    DEBUG: bool = True
    TESTING: bool = True


@dataclass(frozen=True)
class ProductionConfig(BaseConfig):
    DEBUG: bool = False
    TESTING: bool = False


def get_config() -> BaseConfig:
    """
    Фабричная функция конфига — единственная точка входа.
    SOLID: Open/Closed — добавляешь новое окружение, не меняя остальное.
    """
    env = os.getenv("FLASK_ENV", "development")
    configs = {
        "development": DevelopmentConfig,
        "testing": TestingConfig,
        "production": ProductionConfig,
    }
    config_class = configs.get(env, DevelopmentConfig)
    return config_class()
