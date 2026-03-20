# Как думает Senior: полный разбор бэкенда Moodify

> Это не просто объяснение кода. Это объяснение **мышления**.  
> Код — это результат мышления. Сначала нужно научиться думать правильно.

---

## ЧАСТЬ 0: Прежде чем писать первую строку кода

### Главный вопрос, который задаёт senior перед стартом

Прежде чем открыть редактор, senior задаёт себе один вопрос:

> **"Что может пойти не так, и как мне это пережить?"**

Junior думает: "Как сделать чтобы работало?"  
Senior думает: "Как сделать чтобы было легко **изменить**, **протестировать**, и **не сломать**?"

Это принципиальная разница. Вся наша архитектура — ответ на этот вопрос.

---

### Мысленная карта проекта ДО написания кода

Когда senior получает задачу "напиши бэкенд для плейлист-генератора", он рисует в голове (или на бумаге) такую карту:

```
КТО общается с КОГО?

Фронтенд (браузер)
    ↓ HTTP запросы
[Наш Flask-сервер] ← здесь живёт наш код
    ↓                   ↓
Spotify API         Claude API
(внешний сервис)    (внешний сервис)
```

Уже из этой карты видно три вещи:

1. У нас есть **граница** между нашим кодом и внешним миром (API)
2. Нам нужно **переводить** запрос пользователя в язык Spotify
3. Оба внешних сервиса могут **упасть** — нам нужно это обрабатывать

Следующий шаг — разбить задачу на **ответственности**:

| Ответственность | Кто за это отвечает |
|---|---|
| Принять HTTP-запрос | Роуты (routes) |
| Интерпретировать текст пользователя | ClaudeService |
| Общаться со Spotify | SpotifyService |
| Склеить всё вместе | PlaylistService |
| Описать форму данных | Schemas (модели) |
| Настройки приложения | Config |
| Сообщить об ошибках | Exceptions |

Это и есть **архитектура** — ещё до написания кода.

---

## ЧАСТЬ 1: Конфигурация — `config.py`

### Проблема, которую мы решаем

Представь: ты закончил проект, залил на сервер, и вдруг понимаешь — в коде прямо написано:

```python
# ВОТ ТАК ДЕЛАТЬ НЕЛЬЗЯ НИКОГДА
SPOTIFY_SECRET = "a1b2c3d4e5f6..."
```

Теперь твой секретный ключ в истории git навсегда. Любой, кто видит репозиторий — видит его. Это катастрофа.

Или другая ситуация: у тебя три окружения:
- **development** — твой ноутбук, режим отладки включён
- **testing** — тесты с заглушками вместо реальных API
- **production** — боевой сервер, отладка выключена

Как переключаться между ними? Менять код руками каждый раз? Нет — это приведёт к ошибкам.

### Решение: переменные окружения + классы конфига

```python
# app/config.py

import os
from dataclasses import dataclass


@dataclass(frozen=True)  # ← frozen=True делает объект неизменяемым
class BaseConfig:
    SPOTIFY_CLIENT_ID: str = os.getenv("SPOTIFY_CLIENT_ID", "")
    SPOTIFY_CLIENT_SECRET: str = os.getenv("SPOTIFY_CLIENT_SECRET", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    SPOTIFY_TOKEN_URL: str = "https://accounts.spotify.com/api/token"
    SPOTIFY_API_BASE_URL: str = "https://api.spotify.com/v1"
    ANTHROPIC_MODEL: str = "claude-sonnet-4-20250514"
    MAX_PLAYLIST_SIZE: int = 20
    DEFAULT_PLAYLIST_SIZE: int = 10
```

**Почему `os.getenv("SPOTIFY_CLIENT_ID", "")`?**

`os.getenv` читает переменную из окружения операционной системы.  
Ты создаёшь файл `.env` на своём компьютере:

```
SPOTIFY_CLIENT_ID=abc123
SPOTIFY_CLIENT_SECRET=xyz789
```

Этот файл НЕ попадает в git (он в `.gitignore`). На сервере эти переменные устанавливают через панель управления. Код одинаковый — значения разные в каждом окружении. Это называется [12-factor app](https://12factor.net/ru/) — стандарт индустрии.

**Почему `@dataclass(frozen=True)`?**

```python
config = get_config()
config.DEBUG = True  # ← Это вызовет ошибку!
# FrozenInstanceError: cannot assign to field 'DEBUG'
```

Конфиг — это настройки, которые задаются **один раз при запуске**. Если кто-то случайно изменит конфиг в середине работы приложения — поведение станет непредсказуемым. `frozen=True` делает это физически невозможным. Защита от собственных ошибок.

**Почему три класса?**

```python
@dataclass(frozen=True)
class DevelopmentConfig(BaseConfig):
    DEBUG: bool = True      # В dev включаем отладку
    TESTING: bool = False


@dataclass(frozen=True)
class TestingConfig(BaseConfig):
    DEBUG: bool = True
    TESTING: bool = True
    # Заглушки — тесты не ходят в реальный Spotify
    SPOTIFY_CLIENT_ID: str = "test_client_id"
    SPOTIFY_CLIENT_SECRET: str = "test_client_secret"
    ANTHROPIC_API_KEY: str = "test_anthropic_key"


@dataclass(frozen=True)
class ProductionConfig(BaseConfig):
    DEBUG: bool = False     # На проде отладка ВЫКЛЮЧЕНА
    TESTING: bool = False
```

Наследование (`:BaseConfig`) даёт нам **DRY** — общие настройки пишем один раз в `BaseConfig`, а в дочерних классах только то, что отличается.

**Почему фабричная функция `get_config()`?**

```python
def get_config() -> BaseConfig:
    env = os.getenv("FLASK_ENV", "development")
    configs = {
        "development": DevelopmentConfig,
        "testing": TestingConfig,
        "production": ProductionConfig,
    }
    config_class = configs.get(env, DevelopmentConfig)
    return config_class()
```

Одна переменная `FLASK_ENV` управляет всем. Хочешь переключить окружение:
```bash
FLASK_ENV=production python run.py
```

Словарь `configs` вместо `if/elif` — это паттерн **таблица решений**. Если добавишь `StagingConfig` — просто добавляешь строку в словарь. Не трогаешь `if/elif`. Это SOLID принцип **Open/Closed**: открыт для расширения, закрыт для изменения.

---

## ЧАСТЬ 2: Модели данных — `schemas.py`

### Проблема, которую мы решаем

Фронтенд отправляет тебе JSON:
```json
{"prompt": "мне весело", "size": 10}
```

Но что если придёт:
```json
{"prompt": "", "size": -5}
```

Или вообще:
```json
{"prompt": 12345, "size": "много"}
```

Без валидации твой код упадёт где-то глубоко с непонятной ошибкой. Или хуже — продолжит работу с невалидными данными.

Ещё проблема: как передавать данные **между сервисами внутри приложения**? Можно использовать обычные словари `dict`, но тогда ты не знаешь, какие ключи в нём есть, IDE не подсказывает, и ошибки находишь только в рантайме.

### Решение: Pydantic-схемы

```python
# app/models/schemas.py

from pydantic import BaseModel, Field, field_validator
from typing import Optional


class PlaylistRequest(BaseModel):
    """Запрос пользователя на генерацию плейлиста."""
    prompt: str = Field(..., min_length=1, max_length=500)
    size: int = Field(default=10, ge=1, le=20)

    @field_validator("prompt")
    @classmethod
    def strip_prompt(cls, v: str) -> str:
        return v.strip()
```

**Почему Pydantic, а не просто `dict`?**

Смотри разницу:

```python
# БЕЗ Pydantic (плохо)
def generate(request_data: dict):
    prompt = request_data["promt"]  # Опечатка — упадёт в рантайме
    size = request_data.get("size", 10)
    # IDE не знает, что здесь должно быть

# С Pydantic (хорошо)
def generate(request: PlaylistRequest):
    prompt = request.prompt      # IDE подсказывает, опечатку видно сразу
    size = request.size          # Гарантированно int, уже прошёл валидацию
```

**Что делает `Field(..., min_length=1, max_length=500)`?**

- `...` — поле **обязательное** (если передашь `None` — Pydantic выбросит ошибку)
- `min_length=1` — пустая строка не пройдёт
- `max_length=500` — защита от огромных запросов
- `ge=1, le=20` — greater-than-or-equal, less-than-or-equal (числовые границы)

Pydantic проверит всё это **автоматически** при создании объекта:
```python
PlaylistRequest(prompt="", size=100)
# ValidationError: prompt: String should have at least 1 character
#                 size: Input should be less than or equal to 20
```

**Почему разные классы для разных целей?**

```python
# Входящий запрос от фронтенда
class PlaylistRequest(BaseModel):
    prompt: str
    size: int

# Параметры для Spotify (внутри приложения)  
class SpotifyParams(BaseModel):
    seed_genres: list[str]
    target_energy: Optional[float]
    ...

# Трек для ответа фронтенду
class TrackResponse(BaseModel):
    id: str
    name: str
    artist: str
    ...

# Итоговый ответ
class PlaylistResponse(BaseModel):
    tracks: list[TrackResponse]
    explanation: str
    mood_summary: str
```

Каждый класс живёт в своём слое. Данные **трансформируются** при переходе между слоями:

```
JSON от фронтенда
    → PlaylistRequest (валидация входа)
        → SpotifyParams (параметры для API)
            → list[TrackResponse] (данные от Spotify)
                → PlaylistResponse (финальный ответ)
                    → JSON фронтенду
```

Это называется **Data Transfer Object (DTO)** паттерн. Каждый слой знает только о своих данных.

---

## ЧАСТЬ 3: Исключения — `exceptions.py`

### Проблема, которую мы решаем

Когда что-то идёт не так, Python выбрасывает исключение. По умолчанию это может быть:
- `requests.exceptions.ConnectionError` — Spotify недоступен
- `json.JSONDecodeError` — Claude вернул не JSON
- `KeyError` — в ответе нет ожидаемого поля

Проблема: в роутах тебе нужно ловить **разные** ошибки и возвращать **разный** HTTP-статус:
- Ошибка авторизации Spotify → 502
- Неверный запрос от пользователя → 400
- Наш баг → 500

Если ловить базовый `Exception` везде — ты не можешь различить что случилось.

### Решение: иерархия кастомных исключений

```python
# app/utils/exceptions.py

class MoodifyBaseException(Exception):
    """Базовое исключение приложения."""
    pass

class SpotifyAuthError(MoodifyBaseException):
    """Ошибка авторизации в Spotify."""
    pass

class SpotifyAPIError(MoodifyBaseException):
    """Ошибка при запросе к Spotify API."""
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.status_code = status_code

class ClaudeAPIError(MoodifyBaseException):
    pass

class PlaylistGenerationError(MoodifyBaseException):
    pass
```

**Почему иерархия, а не один класс?**

Смотри как это используется в роутах:

```python
# В роуте можно ловить специфично:
try:
    result = service.generate(data)
except SpotifyAuthError as e:
    return jsonify({"error": "Ошибка авторизации"}), 401
except SpotifyAPIError as e:
    return jsonify({"error": str(e)}), e.status_code  # используем статус из исключения
except ClaudeAPIError as e:
    return jsonify({"error": "AI недоступен"}), 502
except MoodifyBaseException as e:
    return jsonify({"error": "Общая ошибка"}), 500
# Любое другое исключение (баг в коде) — не ловим, пусть 500 отдаёт Flask
```

Иерархия позволяет ловить **любой уровень**:
- Поймать конкретное: `except SpotifyAuthError`
- Поймать всё от Spotify: `except (SpotifyAuthError, SpotifyAPIError)`
- Поймать любую нашу ошибку: `except MoodifyBaseException`

**Почему `super().__init__(message)`?**

`super()` вызывает конструктор родительского класса. Это важно — иначе стандартные механизмы Python не будут знать о тексте ошибки:
```python
raise SpotifyAuthError("Токен истёк")
# str(exception) → "Токен истёк"   ← работает благодаря super().__init__
```

---

## ЧАСТЬ 4: Spotify сервис — `spotify_service.py`

### Мышление перед написанием

Что нужно делать сервису? Три вещи:
1. Получить токен доступа у Spotify (авторизация)
2. Найти треки-затравки (`seed_tracks`) по ключевым словам
3. Получить рекомендации по параметрам

Сразу вопрос: токен живёт 3600 секунд (1 час). Глупо получать новый токен при КАЖДОМ запросе — это лишний HTTP-вызов и лишняя задержка. Нужно кэширование.

### Кэш токена

```python
@dataclass
class _TokenCache:
    """Кэш токена — не ходим за новым при каждом запросе."""
    access_token: str = ""
    expires_at: float = 0.0

    def is_valid(self) -> bool:
        # Буфер 30 секунд — защита от гонки (token expires while request is in-flight)
        return bool(self.access_token) and time.time() < self.expires_at - 30
```

**Почему это отдельный класс, а не просто два атрибута в сервисе?**

Принцип Single Responsibility. `_TokenCache` знает только одно: **валиден ли токен**. Логика валидности (буфер в 30 секунд) инкапсулирована в методе `is_valid()`. Завтра ты захочешь добавить "обновляй токен если осталось меньше 5 минут" — меняешь только `_TokenCache`, не трогаешь остальной сервис.

Нижнее подчёркивание `_TokenCache` — соглашение Python: этот класс **приватный**, он нужен только внутри этого файла.

### Конструктор сервиса

```python
class SpotifyService:
    def __init__(self, config: BaseConfig) -> None:
        self._config = config
        self._token_cache = _TokenCache()
```

**Почему принимаем `config` снаружи, а не читаем `os.getenv` прямо здесь?**

Это принцип **Dependency Injection (DI)** — внедрение зависимостей.

Плохой вариант:
```python
class SpotifyService:
    def __init__(self):
        self._client_id = os.getenv("SPOTIFY_CLIENT_ID")  # ← жёсткая зависимость
```

Что не так? Чтобы протестировать этот класс, тебе нужно выставить переменную окружения. Тесты становятся зависимы от окружения. Это хрупко.

Хороший вариант (наш):
```python
class SpotifyService:
    def __init__(self, config: BaseConfig) -> None:
        self._config = config  # ← зависимость передаётся извне
```

В тестах:
```python
service = SpotifyService(config=TestingConfig())  # подставляем тестовый конфиг
```

Сервис не знает, откуда пришёл конфиг. Он просто использует его. Это и есть DI.

### Получение токена

```python
def _get_access_token(self) -> str:
    if self._token_cache.is_valid():
        return self._token_cache.access_token  # ← кэш-хит, не делаем запрос

    credentials = f"{self._config.SPOTIFY_CLIENT_ID}:{self._config.SPOTIFY_CLIENT_SECRET}"
    encoded = base64.b64encode(credentials.encode()).decode()

    response = requests.post(
        self._config.SPOTIFY_TOKEN_URL,
        headers={
            "Authorization": f"Basic {encoded}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={"grant_type": "client_credentials"},
        timeout=10,  # ← ВАЖНО
    )

    if response.status_code != 200:
        raise SpotifyAuthError(f"Не удалось получить токен: {response.text}")

    data = response.json()
    self._token_cache.access_token = data["access_token"]
    self._token_cache.expires_at = time.time() + data["expires_in"]
    return self._token_cache.access_token
```

**Почему `timeout=10`?**

Без таймаута запрос может висеть **бесконечно** если Spotify не отвечает. Твой сервер заморозится. С таймаутом — через 10 секунд получаешь исключение, ловишь его, возвращаешь ошибку пользователю.

**Почему `raise SpotifyAuthError` вместо `return None`?**

Это один из важнейших принципов. Если метод не может выполнить свою задачу — он должен **кричать** об этом исключением, а не тихо возвращать `None` или `False`.

Плохой вариант:
```python
if response.status_code != 200:
    return None  # ← тихо провалились
```

Потом в коде:
```python
token = self._get_access_token()
# Если token == None, следующая строка упадёт с непонятной ошибкой:
headers = {"Authorization": f"Bearer {token}"}
# TypeError: can only concatenate str (not "NoneType") to str
```

Хороший вариант: исключение сразу говорит **что случилось** и **где**.

**Почему метод приватный (`_get_access_token`)?**

Внешний код не должен знать, как именно мы получаем токен. Завтра ты добавишь Redis для кэша токена между перезапусками — это детали реализации. Публичный интерфейс не изменится. Это **инкапсуляция**.

### Парсинг трека — принцип DRY

```python
def _parse_track(self, raw: dict) -> TrackResponse:
    """DRY: одна функция парсинга трека для всех методов."""
    images = raw.get("album", {}).get("images", [])
    return TrackResponse(
        id=raw["id"],
        name=raw["name"],
        artist=", ".join(a["name"] for a in raw.get("artists", [])),
        album=raw.get("album", {}).get("name", ""),
        preview_url=raw.get("preview_url"),
        spotify_url=raw.get("external_urls", {}).get("spotify", ""),
        image_url=images[0]["url"] if images else None,
        duration_ms=raw.get("duration_ms", 0),
    )
```

**Почему `raw.get("album", {}).get("images", [])` а не просто `raw["album"]["images"]`?**

`raw["album"]["images"]` вызовет `KeyError` если поля нет в ответе. А Spotify не гарантирует, что каждый трек имеет все поля. Цепочка `.get()` с дефолтными значениями — защитное программирование.

**Почему выделен в отдельный метод?**

Представь, что у тебя два метода: `get_recommendations` и `get_search_results`. Оба парсят треки. Без `_parse_track` — дублируешь один и тот же код дважды. Завтра Spotify изменит структуру ответа (например, добавит поле `isrc`) — правишь в двух местах. Забыл одно — баг. С `_parse_track` — правишь в одном месте. Это и есть DRY.

---

## ЧАСТЬ 5: Claude сервис — `claude_service.py`

### Мышление перед написанием

Наша главная задача — перевести "Мне весело, хочу танцевальное" в:
```json
{
  "seed_genres": ["pop", "dance"],
  "target_energy": 0.85,
  "target_valence": 0.9,
  "target_tempo": 128
}
```

Claude — это инструмент перевода с человеческого языка на язык Spotify.

Сложность: Claude — языковая модель, она возвращает текст. Нам нужен структурированный JSON. Claude иногда может обернуть JSON в блок ` ```json ``` `. Нужна защитная обработка.

### Системный промпт как константа

```python
_SYSTEM_PROMPT = """
Ты — музыкальный куратор. Твоя задача: преобразовать описание настроения/ситуации
в параметры для Spotify Recommendations API.

ВАЖНО: отвечай ТОЛЬКО валидным JSON без лишнего текста, блоков кода или пояснений.

Структура ответа:
{
  "seed_genres": [...],
  "target_energy": 0.0-1.0,
  ...
}
"""
```

**Почему промпт — это константа на уровне модуля, а не внутри метода?**

1. **DRY** — создаётся один раз, а не при каждом вызове
2. **Видимость** — сразу видно при открытии файла, что это важная часть логики
3. **Тестирование** — можно менять промпт без изменения логики метода

Нижнее подчёркивание `_SYSTEM_PROMPT` означает "это приватная деталь этого модуля".

### Безопасный парсинг JSON

```python
def _safe_json_parse(self, text: str) -> dict:
    cleaned = text.strip("` \n")
    if cleaned.startswith("json"):
        cleaned = cleaned[4:].strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ClaudeAPIError(f"Claude вернул невалидный JSON: {text}") from e
```

**Почему `raise ... from e`?**

Это называется **exception chaining** (цепочка исключений). Когда ловишь одно исключение и бросаешь другое, `from e` сохраняет оригинальное исключение как "причину". В логах ты увидишь оба:

```
ClaudeAPIError: Claude вернул невалидный JSON
  Caused by: json.JSONDecodeError: Expecting value at line 1
```

Без `from e` оригинальная причина теряется. Это критично для отладки.

### Возвращаемый тип — кортеж

```python
def interpret_mood(self, user_prompt: str, playlist_size: int) -> tuple[SpotifyParams, str, str]:
    """
    Returns:
        (SpotifyParams, explanation, mood_summary)
    """
```

**Почему кортеж из трёх элементов, а не словарь?**

Можно было вернуть:
```python
return {"params": params, "explanation": "...", "mood_summary": "..."}
```

Но тогда вызывающий код не знает, что внутри словаря. IDE не подсказывает. С аннотацией `tuple[SpotifyParams, str, str]` — всё явно. Используется распаковка:

```python
params, explanation, mood_summary = self._claude.interpret_mood(prompt, size)
```

Три переменные, три значения — читается как текст.

---

## ЧАСТЬ 6: Playlist сервис — `playlist_service.py` (Оркестратор)

### Самая важная идея этого файла

`PlaylistService` — это **дирижёр**. Он не знает деталей реализации ни Spotify, ни Claude. Он только говорит:

> "Claude, переведи этот текст в параметры. Spotify, дай треки по этим параметрам. Готово."

Дирижёр не умеет играть на скрипке. Но он знает когда и кому играть.

### Пресеты настроений как таблица данных

```python
MOOD_PRESETS: dict[str, dict] = {
    "happy": {
        "seed_genres": ["pop", "dance"],
        "target_energy": 0.8,
        "target_valence": 0.9,
        "target_tempo": 128,
        "explanation": "Весёлые и энергичные треки!",
        "mood_summary": "Радость и веселье",
    },
    "workout": {
        "seed_genres": ["metal", "hip-hop"],
        "target_energy": 0.95,
        ...
    },
    # ...
}
```

**Почему словарь, а не if/elif/else?**

Плохой вариант:
```python
def get_preset(mood):
    if mood == "happy":
        return {"genres": ["pop"], "energy": 0.8}
    elif mood == "sad":
        return {"genres": ["blues"], "energy": 0.3}
    elif mood == "workout":
        return {"genres": ["metal"], "energy": 0.95}
    # ... ещё 10 условий
```

Добавить новое настроение — нужно добавить `elif`. Изменить порядок проверки — риск что-то поломать. Найти конкретный пресет — читать весь код.

С словарём:
```python
MOOD_PRESETS["happy"]     # O(1) — мгновенный доступ
MOOD_PRESETS["new_mood"] = {...}  # Добавить новый — одна строка данных
```

Это паттерн **таблица решений (decision table)** — данные отделены от логики.

### Внедрение зависимостей в оркестраторе

```python
class PlaylistService:
    def __init__(self, spotify: SpotifyService, claude: ClaudeService) -> None:
        self._spotify = spotify
        self._claude = claude
```

`PlaylistService` **не создаёт** `SpotifyService` и `ClaudeService` внутри себя. Он **получает** их снаружи. Это ключевой момент.

Плохой вариант:
```python
class PlaylistService:
    def __init__(self):
        self._spotify = SpotifyService(config=get_config())  # ← жёсткая связь
        self._claude = ClaudeService(config=get_config())
```

Проблема: чтобы протестировать `PlaylistService`, тебе нужны настоящие Spotify и Claude. Тест занимает секунды, стоит денег за API, и падает если нет интернета.

Хороший вариант (наш): в тестах передаём заглушки:
```python
mock_spotify = MagicMock()
mock_claude = MagicMock()
service = PlaylistService(spotify=mock_spotify, claude=mock_claude)
# Тест работает мгновенно, без интернета, бесплатно
```

### Деградация при неизвестном настроении

```python
def generate_from_mood(self, request: MoodRequest) -> PlaylistResponse:
    preset = MOOD_PRESETS.get(request.mood.lower())
    if not preset:
        # Неизвестный пресет — обрабатываем как текстовый промпт
        return self.generate_from_prompt(
            PlaylistRequest(prompt=request.mood, size=request.size)
        )
```

Пользователь нажал кнопку "nostalgia" (которой нет в пресетах)? Вместо ошибки — отправляем слово "nostalgia" как текстовый запрос в Claude. Claude разберётся. Приложение продолжает работать. Это называется **graceful degradation** — изящная деградация.

---

## ЧАСТЬ 7: Роуты — `playlist.py`

### Роль роутов

Роут — это **тонкий слой** между HTTP и бизнес-логикой. Его работа:
1. Принять HTTP-запрос
2. Распарсить и валидировать входные данные
3. Вызвать нужный сервис
4. Вернуть HTTP-ответ

**Роут не содержит бизнес-логику.** Если в роуте больше 20 строк — что-то пошло не так.

### Почему `_get_playlist_service()` а не глобальная переменная?

```python
def _get_playlist_service():
    return current_app.extensions["playlist_service"]
```

Flask имеет концепцию **application context** (контекст приложения). `current_app` — это Flask-магия, которая указывает на текущее запущенное приложение.

Плохой вариант:
```python
# В начале файла:
service = PlaylistService(...)  # Создаём при импорте модуля

@app.route("/generate")
def generate():
    service.generate(...)  # Используем глобальный объект
```

Проблема: при импорте модуля сервис создаётся немедленно — без конфига, без ключей. Тесты ломаются. Несколько инстансов Flask (например, в тестах) делят один объект.

Хороший вариант: сервис живёт в `app.extensions` — словаре, который принадлежит конкретному Flask-приложению. `current_app` всегда указывает на нужное приложение в контексте запроса.

### Обработка ошибок в роуте

```python
@playlist_bp.route("/generate", methods=["POST"])
def generate_from_prompt():
    # Слой 1: валидация входных данных
    try:
        data = PlaylistRequest.model_validate(request.get_json() or {})
    except ValidationError as e:
        return jsonify({"error": "Некорректный запрос", "detail": str(e)}), 400

    # Слой 2: бизнес-логика
    try:
        result = _get_playlist_service().generate_from_prompt(data)
        return jsonify(result.model_dump()), 200
    except (SpotifyAuthError, SpotifyAPIError) as e:
        return jsonify({"error": "Ошибка Spotify", "detail": str(e)}), 502
    except ClaudeAPIError as e:
        return jsonify({"error": "Ошибка AI", "detail": str(e)}), 502
    except PlaylistGenerationError as e:
        return jsonify({"error": "Не удалось создать плейлист", "detail": str(e)}), 500
```

**Почему два отдельных `try/except`?**

Ошибки валидации (400 Bad Request) и ошибки сервисов (5xx) — разные по природе. Смешивать их в один блок — путаница. Два блока — два слоя ответственности.

**Почему `request.get_json() or {}`?**

`request.get_json()` возвращает `None` если тело запроса пустое или не JSON. `or {}` превращает `None` в пустой словарь. Pydantic поймает недостающие поля и вернёт валидную ошибку вместо `TypeError: argument of type 'NoneType' is not iterable`.

**Почему `result.model_dump()`?**

Pydantic-объекты нельзя напрямую сериализовать в JSON. `.model_dump()` превращает их в обычный Python-словарь, который `jsonify` уже умеет сериализовать.

---

## ЧАСТЬ 8: App Factory — `app/__init__.py`

### Что такое App Factory и зачем он нужен

```python
def create_app(config: BaseConfig | None = None) -> Flask:
    app = Flask(__name__)
    cfg = config or get_config()
    
    CORS(app, ...)
    
    # Создаём сервисы и помещаем в app.extensions
    spotify_service = SpotifyService(cfg)
    claude_service = ClaudeService(cfg)
    playlist_service = PlaylistService(spotify=spotify_service, claude=claude_service)
    app.extensions["playlist_service"] = playlist_service
    
    # Регистрируем Blueprint с роутами
    app.register_blueprint(playlist_bp)
    
    return app
```

**Почему функция, а не просто `app = Flask(__name__)` на уровне модуля?**

Если `app` — глобальная переменная, создаётся при импорте. Все тесты используют **один** инстанс приложения. Состояние одного теста загрязняет другой.

С factory функцией:
```python
# В тестах:
def test_one():
    app = create_app(TestingConfig())  # чистый инстанс для этого теста
    ...

def test_two():
    app = create_app(TestingConfig())  # другой чистый инстанс
    ...
```

**Почему зависимости собираются здесь?**

`create_app` — это наш **DI-контейнер** (контейнер внедрения зависимостей). Здесь происходит **composition root** — единственное место, где мы знаем обо всех зависимостях и собираем их вместе:

```
create_app
    ├── SpotifyService(config)
    ├── ClaudeService(config)
    └── PlaylistService(spotify, claude)  ← получает готовые сервисы
```

Каждый сервис не создаёт свои зависимости — он их получает. `create_app` — единственный, кто знает всю картину.

**Почему `app.extensions["playlist_service"]`?**

`app.extensions` — стандартный словарь Flask для хранения расширений/зависимостей приложения. Альтернатива — `g` (request context), но он живёт только во время запроса. Нам нужен singleton, живущий всё время работы приложения.

---

## ЧАСТЬ 9: Тесты — `test_playlist_service.py`

### Почему тесты — это не опция, а необходимость

Представь: ты написал код. Он работает. Через неделю добавил новую фичу. Старый код перестал работать — ты не заметил. Пользователи получают ошибки.

Тесты — это **автоматическая проверка**, что старый код работает после твоих изменений. Senior пишет тесты не потому что "так надо", а потому что без них он не может спать спокойно.

### Фикстуры — DRY для тестов

```python
@pytest.fixture
def mock_track() -> TrackResponse:
    return TrackResponse(
        id="track123",
        name="Test Track",
        ...
    )

@pytest.fixture
def mock_spotify(mock_track):
    spotify = MagicMock()
    spotify.get_recommendations.return_value = [mock_track]
    return spotify

@pytest.fixture
def service(mock_spotify, mock_claude) -> PlaylistService:
    return PlaylistService(spotify=mock_spotify, claude=mock_claude)
```

Фикстура — это переиспользуемая заготовка для теста. Если 10 тестов нужен `mock_track` — создаём его один раз в фикстуре. Pytest автоматически передаёт фикстуры в тест, если название параметра совпадает с названием фикстуры.

### Mock-объекты — тестирование без реальных API

```python
mock_spotify = MagicMock()
mock_spotify.get_recommendations.return_value = [mock_track]
```

`MagicMock` — заглушка. Она ведёт себя как настоящий `SpotifyService`, но:
- Не делает реальных HTTP-запросов
- Возвращает то, что ты задал
- Запоминает, как её вызывали

```python
# Проверяем, что Claude был вызван с правильными аргументами:
mock_claude.interpret_mood.assert_called_once_with("Мне весело", 10)
```

Это называется **unit testing** — тестируем один юнит (PlaylistService) в изоляции от остальных.

### Структура тестового класса

```python
class TestGenerateFromPrompt:
    def test_returns_playlist_response(self, service, mock_claude):
        ...
    
    def test_passes_correct_size_to_claude(self, service, mock_claude):
        ...
```

Группировка по классам — читаемость. Видишь класс `TestGenerateFromMood` — знаешь, что внутри все тесты для метода `generate_from_mood`. Это не обязательно, но делает тесты документацией.

---

## ЧАСТЬ 10: Как всё связывается вместе

### Поток запроса от начала до конца

```
1. POST /api/playlist/generate  {"prompt": "хочу потанцевать", "size": 10}
        ↓
2. playlist.py: generate_from_prompt()
   - Pydantic валидирует данные → PlaylistRequest(prompt="хочу потанцевать", size=10)
   - Получает PlaylistService из app.extensions
        ↓
3. PlaylistService.generate_from_prompt(request)
   - "Моя задача — организовать работу сервисов"
        ↓
4. ClaudeService.interpret_mood("хочу потанцевать", 10)
   - Формирует запрос к Claude API
   - Claude возвращает JSON с параметрами
   - Парсит и валидирует → SpotifyParams(seed_genres=["dance","pop"], energy=0.85, ...)
        ↓
5. SpotifyService.get_recommendations(params)
   - Проверяет кэш токена → берёт из кэша или получает новый
   - Ищет seed tracks по ключевым словам
   - Запрашивает рекомендации у Spotify
   - Парсит ответ → list[TrackResponse]
        ↓
6. PlaylistService собирает PlaylistResponse(tracks=[...], explanation="...", mood_summary="...")
        ↓
7. playlist.py: jsonify(result.model_dump()) → HTTP 200
        ↓
8. {"tracks": [...], "explanation": "...", "mood_summary": "..."}
```

### Что случается при ошибке

```
5. SpotifyService → requests → Timeout!
   raise SpotifyAPIError("Spotify не ответил за 10 секунд", status_code=504)
        ↓
6. PlaylistService не ловит — исключение "всплывает" вверх
        ↓
7. playlist.py ловит SpotifyAPIError:
   return jsonify({"error": "Ошибка Spotify", "detail": "..."}), 502
        ↓
8. Фронтенд получает {"error": "Ошибка Spotify"} с HTTP 502
```

Исключение "всплывает" через стек вызовов, пока его кто-то не поймает. Мы ловим его максимально близко к HTTP-слою — там, где можно вернуть правильный HTTP-статус.

---

## Итог: Правила мышления Senior

| Вопрос | Плохой ответ | Senior-ответ |
|---|---|---|
| Как хранить конфиг? | Захардкодить в коде | Переменные окружения + классы по окружению |
| Как валидировать данные? | `if "prompt" in data` | Pydantic-схемы на всех границах |
| Как обрабатывать ошибки? | `return None` при ошибке | Кастомные исключения с иерархией |
| Как передавать зависимости? | Создавать внутри класса | Dependency Injection через конструктор |
| Как тестировать? | Руками проверять | Unit-тесты с Mock-заглушками |
| Как добавить новый сервис? | Изменить существующий код | Добавить новый класс (Open/Closed) |
| Где создавать объекты? | Везде где нужны | Только в App Factory (Composition Root) |

**Главная идея, которую стоит запомнить:**

> Хороший код — это код, который легко **изменить**.  
> Не тот, который работает. Работающий код пишет каждый.  
> Код, который легко изменить через год — пишет senior.
