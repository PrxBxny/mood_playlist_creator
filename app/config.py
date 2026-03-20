import os
from dataclasses import dataclass


@dataclass(frozen=True)
class BaseConfig:
    SPOTIFY_CLIENT_ID: str = os.getenv("SPOTIFY_CLIENT_ID", "")
    SPOTIFY_CLIENT_SECRET: str = os.getenv("SPOTIFY_CLIENT_SECRET", "")


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
