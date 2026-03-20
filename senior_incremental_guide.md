# Senior Way: От пустой папки до MVP

> Принцип номер один: **в любой момент времени приложение должно запускаться**.  
> Ты не пишешь мёртвый код, который "оживёт когда всё будет готово".  
> Каждый шаг — живое, работающее приложение. Просто с меньшим функционалом.

---

## Шаг 0: Среда и структура — "обустрой рабочее место"

Прежде чем писать код, senior готовит окружение. Это занимает 5 минут, но экономит часы потом.

### Почему виртуальное окружение (venv)?

Представь: у тебя два проекта. Один требует `flask==2.0`, другой `flask==3.0`.  
Без venv они конфликтуют — установить оба нельзя.  
С venv — каждый проект живёт в своей изолированной "песочнице" с собственными пакетами.

```bash
# Создаём папку проекта
mkdir moodify-backend
cd moodify-backend

# Создаём виртуальное окружение
python -m venv venv

# Активируем его
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Теперь ты в изолированной среде. В терминале появится (venv)
```

### Почему .gitignore сразу?

```bash
# .gitignore — создаём ДО первого git commit
venv/          # виртуальное окружение — у каждого своё, не коммитим
.env           # секреты — НИКОГДА не коммитим
__pycache__/   # скомпилированный Python — генерируется автоматически
*.pyc          # байткод Python
```

Если забудешь создать `.gitignore` и закоммитишь `.env` с ключами —  
придётся менять все ключи. Это реальная история, которая случалась с людьми.

### Первая структура — максимально плоская

```
moodify-backend/
├── venv/           ← виртуальное окружение (не трогаем)
├── .gitignore
├── .env            ← секреты (не в git)
├── .env.example    ← шаблон без секретов (в git, для других разработчиков)
├── requirements.txt
└── app.py          ← ВСЁ в одном файле для начала
```

**Почему начинаем с одного файла `app.py`, а не с красивой структурой папок?**

Потому что красивая структура для кода, которого ещё нет — это YAGNI  
(You Aren't Gonna Need It — тебе это не понадобится).  
Структуру папок создают когда **реально** нужно разделить код, а не заранее.

---

## Шаг 1: Самый простой Flask — "убедись что стоит"

### Устанавливаем первые зависимости

```bash
pip install flask python-dotenv
pip freeze > requirements.txt
```

**Почему `pip freeze > requirements.txt`?**  
`pip freeze` выводит все установленные пакеты с точными версиями.  
`requirements.txt` — это "рецепт" проекта. Другой разработчик (или ты на новом компьютере) сделает:
```bash
pip install -r requirements.txt
```
И получит точно такое же окружение. Без этого файла — "у меня работает" становится проблемой.

### Пишем первое приложение

```python
# app.py — буквально минимум
from flask import Flask

app = Flask(__name__)

@app.route("/health")
def health():
    return {"status": "ok"}, 200

if __name__ == "__main__":
    app.run(debug=True)
```

**Запускаем и проверяем:**
```bash
python app.py
# Running on http://127.0.0.1:5000

curl http://localhost:5000/health
# {"status": "ok"}
```

✅ Приложение стоит. Можно двигаться дальше.

**Почему именно `/health` — первый роут?**  
Health-check — это стандарт индустрии. Это роут, который отвечает "я жив".  
Его используют: системы мониторинга, Docker, Kubernetes, балансировщики нагрузки.  
Привыкай добавлять его в каждый проект с первой минуты.

---

## Шаг 2: App Factory — "подготовь к росту"

Сейчас у нас `app = Flask(__name__)` — глобальный объект.  
Как только напишем тесты — это станет проблемой: все тесты будут делить один инстанс.  
Senior переходит к App Factory **сразу**, пока кода мало и рефакторинг дёшев.

### Почему сейчас, а не потом?

Правило: чем позже рефакторинг — тем он дороже.  
Переписать с глобального `app` на фабрику когда у тебя 3 строки — 2 минуты.  
Переписать когда у тебя 20 роутов — полдня и риск что-то сломать.

```python
# app.py — добавляем фабрику
from flask import Flask


def create_app() -> Flask:
    """
    App Factory — единственное место создания приложения.
    
    Почему функция, а не глобальная переменная?
    - Каждый вызов = новый чистый инстанс (идеально для тестов)
    - Зависимости передаются явно, нет скрытого глобального состояния
    - Стандартный паттерн Flask, все плагины его ожидают
    """
    app = Flask(__name__)

    @app.route("/health")
    def health():
        return {"status": "ok"}, 200

    return app


# Точка запуска — только если запускаем этот файл напрямую
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
```

```bash
python app.py
curl http://localhost:5000/health
# {"status": "ok"} — всё ещё работает ✅
```

Мы ничего не сломали. Функционал тот же, архитектура стала лучше.  
Это и есть рефакторинг — улучшение структуры без изменения поведения.

---

## Шаг 3: Конфигурация — "отдели секреты от кода"

### Создаём файлы окружения

```bash
# .env — твои реальные секреты (НЕ в git)
FLASK_ENV=development
SPOTIFY_CLIENT_ID=твой_реальный_id
SPOTIFY_CLIENT_SECRET=твой_реальный_secret
ANTHROPIC_API_KEY=твой_реальный_ключ

# .env.example — шаблон для других (В git)
FLASK_ENV=development
SPOTIFY_CLIENT_ID=
SPOTIFY_CLIENT_SECRET=
ANTHROPIC_API_KEY=
```

### Добавляем конфиг в проект

```python
# config.py — новый файл рядом с app.py
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    """
    Один класс конфига для начала — не усложняем раньше времени.
    
    frozen=True — конфиг задаётся один раз при запуске.
    Случайное изменение конфига в рантайме невозможно физически.
    """
    FLASK_ENV: str = os.getenv("FLASK_ENV", "development")
    DEBUG: bool = FLASK_ENV == "development"

    SPOTIFY_CLIENT_ID: str = os.getenv("SPOTIFY_CLIENT_ID", "")
    SPOTIFY_CLIENT_SECRET: str = os.getenv("SPOTIFY_CLIENT_SECRET", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

    SPOTIFY_TOKEN_URL: str = "https://accounts.spotify.com/api/token"
    SPOTIFY_API_BASE_URL: str = "https://api.spotify.com/v1"
    ANTHROPIC_MODEL: str = "claude-sonnet-4-20250514"


def get_config() -> Config:
    return Config()
```

```python
# app.py — подключаем конфиг
from flask import Flask
from dotenv import load_dotenv  # читает .env файл

load_dotenv()  # ← ВАЖНО: вызываем ДО импорта config

from config import get_config


def create_app() -> Flask:
    app = Flask(__name__)
    cfg = get_config()

    # Передаём debug-режим из конфига во Flask
    app.debug = cfg.DEBUG

    @app.route("/health")
    def health():
        return {"status": "ok", "env": cfg.FLASK_ENV}, 200

    return app


if __name__ == "__main__":
    app = create_app()
    app.run()
```

**Почему `load_dotenv()` вызывается в `app.py`, а не в `config.py`?**

`load_dotenv()` — это side effect (побочный эффект): он изменяет состояние процесса.  
Побочные эффекты должны быть **явными** и **в точке входа**.  
Если `load_dotenv()` в `config.py` — он вызывается при каждом импорте модуля.  
Это скрытое поведение, которое сложно отследить и контролировать.

```bash
python app.py
curl http://localhost:5000/health
# {"env": "development", "status": "ok"} ✅
```

---

## Шаг 4: Первый Blueprint — "организуй роуты"

Сейчас роуты прямо в `create_app()`. Пока один роут — это нормально.  
Но мы собираемся добавить `/api/playlist/generate`, `/api/playlist/mood` и др.  
Значит пора вводить Blueprint.

**Что такое Blueprint?**  
Blueprint — это "модуль роутов". Группа связанных URL-адресов.  
Как папки для файлов, только для роутов.

Создаём структуру папок — теперь это оправдано, потому что код реально появился:

```
moodify-backend/
├── app/
│   ├── __init__.py      ← create_app живёт здесь
│   └── routes/
│       ├── __init__.py
│       └── playlist.py  ← роуты плейлиста
├── config.py
├── .env
├── .env.example
├── requirements.txt
└── run.py               ← точка запуска
```

**Почему `app/` папка вместо одного `app.py`?**  
Когда у тебя один файл — он называется `app.py`.  
Когда файлов несколько — они живут в папке `app/`.  
Мы переходим к папке, потому что у нас появились `routes/` — значит кода стало больше.

```python
# app/routes/playlist.py
from flask import Blueprint, jsonify

# Blueprint — это "мини-приложение" с набором роутов
# "playlist" — имя (используется в url_for)
# url_prefix — все роуты этого Blueprint начинаются с /api/playlist
playlist_bp = Blueprint("playlist", __name__, url_prefix="/api/playlist")


@playlist_bp.route("/ping")
def ping():
    """
    Временный роут для проверки что Blueprint подключён.
    Потом удалим — сейчас нужен просто чтобы видеть результат.
    """
    return jsonify({"message": "playlist router is alive"}), 200
```

```python
# app/__init__.py
from flask import Flask
from flask_cors import CORS

from config import get_config
from app.routes.playlist import playlist_bp


def create_app() -> Flask:
    app = Flask(__name__)
    cfg = get_config()
    app.debug = cfg.DEBUG

    # CORS — разрешаем фронтенду (другой origin) обращаться к нашему API
    # Без этого браузер заблокирует запросы с localhost:3000 к localhost:5000
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Регистрируем Blueprint с роутами
    app.register_blueprint(playlist_bp)

    @app.route("/health")
    def health():
        return {"status": "ok"}, 200

    return app
```

```python
# run.py — точка запуска вынесена из app/
from dotenv import load_dotenv
load_dotenv()

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
```

```bash
pip install flask-cors
pip freeze > requirements.txt

python run.py
curl http://localhost:5000/health            # {"status": "ok"} ✅
curl http://localhost:5000/api/playlist/ping # {"message": "playlist router is alive"} ✅
```

---

## Шаг 5: Исключения — "договорись о языке ошибок"

**Почему исключения ПЕРЕД сервисами?**

Это вопрос порядка зависимостей.  
Сервисы будут `raise` (выбрасывать) исключения.  
Роуты будут их ловить.  
Если создать исключения после сервисов — придётся возвращаться и переписывать.

Думай об этом как о словаре: прежде чем писать статью — договорись о терминах.

```python
# app/exceptions.py — создаём рядом с routes/

class MoodifyError(Exception):
    """
    Базовый класс для всех ошибок нашего приложения.
    
    Зачем базовый класс?
    В роуте можно поймать любую нашу ошибку одним except:
        except MoodifyError as e: ...
    Или поймать конкретную:
        except SpotifyAuthError as e: ...
    """
    pass


class SpotifyAuthError(MoodifyError):
    """Не удалось получить токен Spotify."""
    pass


class SpotifyAPIError(MoodifyError):
    """Spotify вернул ошибку или недоступен."""
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.status_code = status_code  # HTTP статус от Spotify


class ClaudeError(MoodifyError):
    """Claude API недоступен или вернул невалидный ответ."""
    pass


class PlaylistError(MoodifyError):
    """Ошибка при генерации плейлиста."""
    pass
```

**Почему `super().__init__(message)` обязателен?**

```python
# Без super().__init__:
err = SpotifyAuthError("токен истёк")
str(err)     # '' — пустая строка! Текст потерян
err.args     # () — пусто

# С super().__init__:
err = SpotifyAuthError("токен истёк")
str(err)     # 'токен истёк' — работает как ожидается
err.args     # ('токен истёк',)
```

Базовый `Exception.__init__` регистрирует аргументы в системе Python.  
Без вызова `super()` — сообщение об ошибке теряется. Отладка превращается в квест.

---

## Шаг 6: Схемы данных — "договорись о форме данных"

**Почему схемы перед сервисами?**

По той же причине что исключения: сервисы будут принимать и возвращать эти типы.  
Если определить схемы сейчас — сервисы пишутся сразу правильно.

Добавляем Pydantic:
```bash
pip install pydantic
pip freeze > requirements.txt
```

```python
# app/schemas.py

from pydantic import BaseModel, Field, field_validator
from typing import Optional


# ── Входящие данные от фронтенда ───────────────────────────────

class PlaylistRequest(BaseModel):
    """
    Что фронтенд отправляет нам.
    Pydantic автоматически валидирует при создании объекта.
    Если данные невалидны — ValidationError до того как код выполнится.
    """
    prompt: str = Field(..., min_length=1, max_length=500)
    size: int = Field(default=10, ge=1, le=20)

    @field_validator("prompt")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        # Убираем пробелы по краям: "  весело  " → "весело"
        return v.strip()


class MoodRequest(BaseModel):
    mood: str = Field(..., min_length=1, max_length=100)
    size: int = Field(default=10, ge=1, le=20)


# ── Внутренние данные между сервисами ─────────────────────────

class SpotifyParams(BaseModel):
    """
    Claude переводит текст пользователя → эту структуру.
    Spotify принимает эту структуру → возвращает треки.
    
    Это называется DTO (Data Transfer Object) —
    объект для передачи данных между слоями.
    """
    seed_genres: list[str] = Field(default_factory=list)
    seed_keywords: list[str] = Field(default_factory=list)
    target_energy: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    target_valence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    target_tempo: Optional[float] = Field(default=None, ge=40.0, le=220.0)
    target_danceability: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    limit: int = Field(default=10, ge=1, le=20)


# ── Исходящие данные фронтенду ────────────────────────────────

class TrackOut(BaseModel):
    """Один трек в плейлисте."""
    id: str
    name: str
    artist: str
    album: str
    preview_url: Optional[str]
    spotify_url: str
    image_url: Optional[str]
    duration_ms: int


class PlaylistOut(BaseModel):
    """Финальный ответ API."""
    tracks: list[TrackOut]
    explanation: str
    mood_summary: str
```

**Почему отдельные классы для входящих и исходящих данных?**

Кажется лишним — можно же один класс?  
Нет. Входящие данные — это **запрос** (что хочет пользователь).  
Исходящие — это **ответ** (что мы ему даём).  
Они живут в разных слоях и могут независимо меняться.

Завтра ты добавишь в ответ поле `cached: bool` (взято из кэша или нет).  
Это не должно затрагивать схему входящего запроса.

---

## Шаг 7: Spotify сервис — "первая реальная фича"

Теперь у нас есть всё что нужно сервису:
- Config (знает ключи)
- Exceptions (знает как кричать об ошибках)
- Schemas (знает форму данных)

```bash
pip install requests
pip freeze > requirements.txt
```

```python
# app/services/__init__.py  ← пустой файл, делает папку пакетом Python

# app/services/spotify.py

import base64
import time
import requests
from dataclasses import dataclass, field

from config import Config
from app.schemas import SpotifyParams, TrackOut
from app.exceptions import SpotifyAuthError, SpotifyAPIError


@dataclass
class _TokenCache:
    """
    Приватный класс — только для этого файла (нижнее подчёркивание).
    Хранит токен и знает, истёк ли он.
    
    Почему отдельный класс, а не два атрибута в SpotifyService?
    Single Responsibility: логика "валиден ли токен" — отдельная ответственность.
    Завтра добавишь refresh-логику — меняешь только этот класс.
    """
    access_token: str = ""
    expires_at: float = 0.0

    def is_valid(self) -> bool:
        return bool(self.access_token) and time.time() < self.expires_at - 30


class SpotifyService:
    """
    Единственный класс, который знает как говорить со Spotify.
    Всё остальное приложение работает с ним — не с Spotify напрямую.
    
    Dependency Injection: принимает config снаружи.
    Никакого os.getenv внутри — зависимости явны.
    """

    def __init__(self, config: Config) -> None:
        self._config = config
        self._token_cache = _TokenCache()

    def get_recommendations(self, params: SpotifyParams) -> list[TrackOut]:
        """Публичный метод — единственное что знает внешний код."""
        token = self._get_token()
        seed_ids = self._find_seed_tracks(params.seed_keywords, token)
        return self._fetch_recommendations(params, seed_ids, token)

    def get_random_tracks(self, limit: int = 10) -> list[TrackOut]:
        import random
        genres = random.sample(self._genre_pool(), k=2)
        return self.get_recommendations(SpotifyParams(seed_genres=genres, limit=limit))

    # ── Всё ниже — приватное. Детали реализации. ──────────────────

    def _get_token(self) -> str:
        """
        Client Credentials Flow — не нужен логин пользователя.
        Работает с любым аккаунтом Spotify, без premium.
        """
        if self._token_cache.is_valid():
            return self._token_cache.access_token

        creds = f"{self._config.SPOTIFY_CLIENT_ID}:{self._config.SPOTIFY_CLIENT_SECRET}"
        encoded = base64.b64encode(creds.encode()).decode()

        resp = requests.post(
            self._config.SPOTIFY_TOKEN_URL,
            headers={
                "Authorization": f"Basic {encoded}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={"grant_type": "client_credentials"},
            timeout=10,
        )

        if resp.status_code != 200:
            raise SpotifyAuthError(f"Не удалось получить токен: {resp.text}")

        data = resp.json()
        self._token_cache.access_token = data["access_token"]
        self._token_cache.expires_at = time.time() + data["expires_in"]
        return self._token_cache.access_token

    def _find_seed_tracks(self, keywords: list[str], token: str) -> list[str]:
        """Ищем id треков по ключевым словам для использования как seed."""
        ids = []
        for kw in keywords[:2]:
            resp = requests.get(
                f"{self._config.SPOTIFY_API_BASE_URL}/search",
                headers={"Authorization": f"Bearer {token}"},
                params={"q": kw, "type": "track", "limit": 1},
                timeout=10,
            )
            if resp.status_code == 200:
                items = resp.json().get("tracks", {}).get("items", [])
                if items:
                    ids.append(items[0]["id"])
        return ids

    def _fetch_recommendations(
        self,
        params: SpotifyParams,
        seed_ids: list[str],
        token: str,
    ) -> list[TrackOut]:
        query: dict = {"limit": params.limit}

        if params.seed_genres:
            query["seed_genres"] = ",".join(params.seed_genres[:5])

        if seed_ids:
            remaining_slots = 5 - len(params.seed_genres[:5])
            if remaining_slots > 0:
                query["seed_tracks"] = ",".join(seed_ids[:remaining_slots])

        # Добавляем только те audio features что не None — DRY через dict
        optional = {
            "target_energy": params.target_energy,
            "target_valence": params.target_valence,
            "target_tempo": params.target_tempo,
            "target_danceability": params.target_danceability,
        }
        query.update({k: v for k, v in optional.items() if v is not None})

        resp = requests.get(
            f"{self._config.SPOTIFY_API_BASE_URL}/recommendations",
            headers={"Authorization": f"Bearer {token}"},
            params=query,
            timeout=10,
        )

        if resp.status_code != 200:
            raise SpotifyAPIError(f"Spotify ошибка: {resp.text}", resp.status_code)

        return [self._parse_track(t) for t in resp.json().get("tracks", [])]

    def _parse_track(self, raw: dict) -> TrackOut:
        """
        DRY: единственное место где мы знаем структуру трека от Spotify.
        Spotify изменит формат → правим здесь и только здесь.
        """
        images = raw.get("album", {}).get("images", [])
        return TrackOut(
            id=raw["id"],
            name=raw["name"],
            artist=", ".join(a["name"] for a in raw.get("artists", [])),
            album=raw.get("album", {}).get("name", ""),
            preview_url=raw.get("preview_url"),
            spotify_url=raw.get("external_urls", {}).get("spotify", ""),
            image_url=images[0]["url"] if images else None,
            duration_ms=raw.get("duration_ms", 0),
        )

    def _genre_pool(self) -> list[str]:
        return [
            "pop", "rock", "hip-hop", "electronic", "jazz", "classical",
            "r-n-b", "indie", "metal", "folk", "ambient", "dance",
        ]
```

### Проверяем Spotify сервис в изоляции

**Это важный шаг, который пропускают джуниоры.**  
Прежде чем прикручивать сервис к роутам — проверь его в консоли Python:

```python
# В терминале: python
from dotenv import load_dotenv
load_dotenv()

from config import get_config
from app.services.spotify import SpotifyService
from app.schemas import SpotifyParams

service = SpotifyService(get_config())
tracks = service.get_recommendations(
    SpotifyParams(seed_genres=["pop"], target_energy=0.8, limit=3)
)
for t in tracks:
    print(t.name, "—", t.artist)
```

Если видишь треки — сервис работает. Теперь подключаем к роутам.

---

## Шаг 8: Подключаем Spotify к роутам

```python
# app/__init__.py — добавляем сервис в app.extensions
from flask import Flask
from flask_cors import CORS

from config import get_config
from app.routes.playlist import playlist_bp
from app.services.spotify import SpotifyService


def create_app() -> Flask:
    app = Flask(__name__)
    cfg = get_config()
    app.debug = cfg.DEBUG

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Создаём сервис один раз — он живёт всё время работы приложения
    # app.extensions — стандартный Flask-словарь для зависимостей
    app.extensions["spotify"] = SpotifyService(cfg)

    app.register_blueprint(playlist_bp)

    @app.route("/health")
    def health():
        return {"status": "ok"}, 200

    return app
```

```python
# app/routes/playlist.py — добавляем реальный роут
from flask import Blueprint, jsonify, request, current_app
from pydantic import ValidationError

from app.schemas import PlaylistRequest, SpotifyParams
from app.exceptions import MoodifyError, SpotifyAPIError

playlist_bp = Blueprint("playlist", __name__, url_prefix="/api/playlist")


def _spotify():
    """
    Получаем сервис из app.extensions.
    Функция-обёртка — DRY, если понадобится поменять способ получения.
    """
    return current_app.extensions["spotify"]


@playlist_bp.route("/random")
def random_playlist():
    """
    Первый реальный роут.
    Начинаем с самого простого — не нужен ни Claude, ни промпт.
    """
    try:
        size = int(request.args.get("size", 10))
        size = max(1, min(size, 20))  # clamp — защита от выхода за границы
    except ValueError:
        return jsonify({"error": "size должен быть числом"}), 400

    try:
        tracks = _spotify().get_random_tracks(limit=size)
        return jsonify({
            "tracks": [t.model_dump() for t in tracks],
            "mood_summary": "Случайный микс",
            "explanation": "Случайные треки — иногда лучшие открытия неожиданны.",
        }), 200
    except MoodifyError as e:
        status = getattr(e, "status_code", 500)
        return jsonify({"error": str(e)}), status


@playlist_bp.route("/generate", methods=["POST"])
def generate():
    """
    Основной роут. Пока без Claude — просто принимаем жанры напрямую.
    Claude добавим на следующем шаге.
    """
    try:
        body = PlaylistRequest.model_validate(request.get_json() or {})
    except ValidationError as e:
        return jsonify({"error": "Невалидный запрос", "detail": e.errors()}), 400

    # Временная заглушка: парсим жанры из промпта по ключевым словам
    # Потом это место займёт Claude
    params = SpotifyParams(
        seed_keywords=[body.prompt],
        limit=body.size,
    )

    try:
        tracks = _spotify().get_recommendations(params)
        return jsonify({
            "tracks": [t.model_dump() for t in tracks],
            "mood_summary": "По твоему запросу",
            "explanation": f'Подобрал треки по запросу: "{body.prompt}"',
        }), 200
    except MoodifyError as e:
        status = getattr(e, "status_code", 500)
        return jsonify({"error": str(e)}), status
```

```bash
python run.py

# Тестируем случайный плейлист
curl "http://localhost:5000/api/playlist/random?size=3"

# Тестируем generate
curl -X POST http://localhost:5000/api/playlist/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "happy pop music", "size": 3}'
```

✅ У нас работающий API с реальными треками от Spotify. Без Claude.

**Это важный принцип: каждая фича должна работать до добавления следующей.**  
Generate работает с заглушкой. Потом заглушку заменяем на Claude.

---

## Шаг 9: Claude сервис — "добавляем AI"

```bash
pip install anthropic
pip freeze > requirements.txt
```

```python
# app/services/claude.py

import json
import anthropic

from config import Config
from app.schemas import SpotifyParams
from app.exceptions import ClaudeError


_SYSTEM_PROMPT = """
Ты — музыкальный куратор. Переведи описание настроения в параметры Spotify API.
Отвечай ТОЛЬКО валидным JSON. Никакого текста вокруг, никаких ```json блоков.

Структура:
{
  "seed_genres": ["genre1", "genre2"],
  "seed_keywords": ["artist or track name"],
  "target_energy": 0.0-1.0,
  "target_valence": 0.0-1.0,
  "target_tempo": 60-200,
  "target_danceability": 0.0-1.0,
  "explanation": "объяснение на русском",
  "mood_summary": "2-4 слова на русском"
}

Жанры Spotify: pop, rock, hip-hop, electronic, jazz, classical, r-n-b,
indie, metal, folk, ambient, dance, country, blues, soul.
Если поле не нужно — null.
"""


class ClaudeService:
    def __init__(self, config: Config) -> None:
        self._client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        self._model = config.ANTHROPIC_MODEL

    def interpret(self, prompt: str, size: int) -> tuple[SpotifyParams, str, str]:
        """
        Returns: (SpotifyParams, explanation, mood_summary)
        
        Почему tuple, а не dict?
        tuple[SpotifyParams, str, str] — IDE знает типы каждого элемента.
        dict — IDE не знает ничего.
        """
        raw = self._call_claude(prompt, size)
        params = SpotifyParams(
            seed_genres=raw.get("seed_genres") or [],
            seed_keywords=raw.get("seed_keywords") or [],
            target_energy=raw.get("target_energy"),
            target_valence=raw.get("target_valence"),
            target_tempo=raw.get("target_tempo"),
            target_danceability=raw.get("target_danceability"),
            limit=size,
        )
        return params, raw.get("explanation", ""), raw.get("mood_summary", "")

    def _call_claude(self, prompt: str, size: int) -> dict:
        try:
            msg = self._client.messages.create(
                model=self._model,
                max_tokens=512,
                system=_SYSTEM_PROMPT,
                messages=[{
                    "role": "user",
                    "content": f'Запрос: "{prompt}"\nТреков: {size}'
                }],
            )
        except anthropic.APIError as e:
            raise ClaudeError(f"Claude недоступен: {e}") from e

        return self._parse_json(msg.content[0].text)

    def _parse_json(self, text: str) -> dict:
        """Защитный парсинг — Claude иногда оборачивает ответ в ```json."""
        cleaned = text.strip().strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:].strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            raise ClaudeError(f"Claude вернул невалидный JSON: {text}") from e
```

---

## Шаг 10: PlaylistService — оркестратор

```python
# app/services/playlist.py

from app.schemas import PlaylistRequest, MoodRequest, SpotifyParams, PlaylistOut
from app.services.spotify import SpotifyService
from app.services.claude import ClaudeService
from app.exceptions import PlaylistError

MOOD_PRESETS: dict[str, dict] = {
    "happy":   {"seed_genres": ["pop","dance"],    "energy":0.8,  "valence":0.9, "tempo":128, "summary":"Радость",       "explain":"Весёлые треки для отличного настроения!"},
    "sad":     {"seed_genres": ["indie","blues"],  "energy":0.3,  "valence":0.2, "tempo":75,  "summary":"Грусть",        "explain":"Треки, которые поймут твоё настроение."},
    "workout": {"seed_genres": ["metal","hip-hop"],"energy":0.95, "valence":0.5, "tempo":160, "summary":"Тренировка",    "explain":"Максимальная энергия для максимальной отдачи!"},
    "focus":   {"seed_genres": ["ambient","classical"],"energy":0.4,"valence":0.5,"tempo":90, "summary":"Фокус",         "explain":"Инструментальные треки для концентрации."},
    "party":   {"seed_genres": ["electronic","dance"],"energy":0.9,"valence":0.85,"tempo":140,"summary":"Вечеринка",     "explain":"Заряженный микс для вечеринки!"},
    "chill":   {"seed_genres": ["jazz","soul"],    "energy":0.35, "valence":0.65,"tempo":85,  "summary":"Расслабление",  "explain":"Спокойные треки для отдыха."},
}


class PlaylistService:
    """
    Оркестратор — дирижёр между Spotify и Claude.
    Не знает деталей ни одного из них. Только координирует.
    
    DI: получает готовые сервисы снаружи.
    Тестируется без реальных API — просто подставь Mock.
    """

    def __init__(self, spotify: SpotifyService, claude: ClaudeService) -> None:
        self._spotify = spotify
        self._claude = claude

    def from_prompt(self, req: PlaylistRequest) -> PlaylistOut:
        try:
            params, explanation, summary = self._claude.interpret(req.prompt, req.size)
            tracks = self._spotify.get_recommendations(params)
            return PlaylistOut(tracks=tracks, explanation=explanation, mood_summary=summary)
        except Exception as e:
            raise PlaylistError(str(e)) from e

    def from_mood(self, req: MoodRequest) -> PlaylistOut:
        preset = MOOD_PRESETS.get(req.mood.lower())
        if not preset:
            # Изящная деградация: неизвестный пресет → обрабатываем как промпт
            return self.from_prompt(PlaylistRequest(prompt=req.mood, size=req.size))

        params = SpotifyParams(
            seed_genres=preset["seed_genres"],
            target_energy=preset["energy"],
            target_valence=preset["valence"],
            target_tempo=preset["tempo"],
            limit=req.size,
        )
        tracks = self._spotify.get_recommendations(params)
        return PlaylistOut(tracks=tracks, explanation=preset["explain"], mood_summary=preset["summary"])

    def random(self, size: int = 10) -> PlaylistOut:
        tracks = self._spotify.get_random_tracks(limit=size)
        return PlaylistOut(
            tracks=tracks,
            explanation="Случайный микс — лучшие открытия приходят неожиданно.",
            mood_summary="Случайный микс",
        )
```

---

## Шаг 11: Собираем всё в app factory и финальные роуты

```python
# app/__init__.py — финальная версия

from flask import Flask
from flask_cors import CORS

from config import get_config
from app.routes.playlist import playlist_bp
from app.services.spotify import SpotifyService
from app.services.claude import ClaudeService
from app.services.playlist import PlaylistService


def create_app() -> Flask:
    app = Flask(__name__)
    cfg = get_config()
    app.debug = cfg.DEBUG

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Composition Root — единственное место где собираем зависимости
    spotify = SpotifyService(cfg)
    claude = ClaudeService(cfg)
    playlist = PlaylistService(spotify=spotify, claude=claude)

    app.extensions["playlist"] = playlist

    app.register_blueprint(playlist_bp)

    @app.route("/health")
    def health():
        return {"status": "ok"}, 200

    return app
```

```python
# app/routes/playlist.py — финальная версия

from flask import Blueprint, jsonify, request, current_app
from pydantic import ValidationError

from app.schemas import PlaylistRequest, MoodRequest
from app.exceptions import MoodifyError
from app.services.playlist import MOOD_PRESETS

playlist_bp = Blueprint("playlist", __name__, url_prefix="/api/playlist")


def _service():
    return current_app.extensions["playlist"]


@playlist_bp.route("/generate", methods=["POST"])
def generate():
    try:
        body = PlaylistRequest.model_validate(request.get_json() or {})
    except ValidationError as e:
        return jsonify({"error": "Невалидный запрос", "detail": e.errors()}), 400

    try:
        result = _service().from_prompt(body)
        return jsonify(result.model_dump()), 200
    except MoodifyError as e:
        return jsonify({"error": str(e)}), getattr(e, "status_code", 500)


@playlist_bp.route("/mood", methods=["POST"])
def from_mood():
    try:
        body = MoodRequest.model_validate(request.get_json() or {})
    except ValidationError as e:
        return jsonify({"error": "Невалидный запрос", "detail": e.errors()}), 400

    try:
        result = _service().from_mood(body)
        return jsonify(result.model_dump()), 200
    except MoodifyError as e:
        return jsonify({"error": str(e)}), getattr(e, "status_code", 500)


@playlist_bp.route("/random")
def random_playlist():
    try:
        size = max(1, min(int(request.args.get("size", 10)), 20))
    except ValueError:
        return jsonify({"error": "size должен быть числом"}), 400

    try:
        result = _service().random(size=size)
        return jsonify(result.model_dump()), 200
    except MoodifyError as e:
        return jsonify({"error": str(e)}), getattr(e, "status_code", 500)


@playlist_bp.route("/moods")
def list_moods():
    """Список пресетов для фронтенда — чтобы не хардкодить кнопки в UI."""
    moods = [{"key": k, "label": v["summary"]} for k, v in MOOD_PRESETS.items()]
    return jsonify({"moods": moods}), 200
```

---

## Итоговая структура и порядок сборки

```
moodify-backend/
├── venv/
├── .gitignore
├── .env                     ← секреты
├── .env.example             ← шаблон
├── requirements.txt
├── config.py                ← ШАГ 3
├── run.py                   ← ШАГ 4
└── app/
    ├── __init__.py          ← ШАГ 2 (App Factory), ШАГ 8, ШАГ 11
    ├── exceptions.py        ← ШАГ 5
    ├── schemas.py           ← ШАГ 6
    ├── routes/
    │   ├── __init__.py
    │   └── playlist.py      ← ШАГ 4, ШАГ 8, ШАГ 11
    └── services/
        ├── __init__.py
        ├── spotify.py       ← ШАГ 7
        ├── claude.py        ← ШАГ 9
        └── playlist.py      ← ШАГ 10
```

### Порядок был не случайным:

| Шаг | Файл | Почему именно здесь |
|-----|------|---------------------|
| 1 | `app.py` (один файл) | Убеждаемся что Flask работает |
| 2 | App Factory | Пока мало кода — рефакторинг дёшев |
| 3 | `config.py` | Нужен всем — создаём до первых зависимостей |
| 4 | Blueprint + `/ping` | Структура маршрутизации до реальных роутов |
| 5 | `exceptions.py` | Словарь ошибок до кода который их бросает |
| 6 | `schemas.py` | Форма данных до кода который с ними работает |
| 7 | `SpotifyService` | Первая реальная фича. Тестируем в консоли |
| 8 | Подключение к роутам | Проверяем что Spotify → HTTP работает |
| 9 | `ClaudeService` | Добавляем AI поверх работающего Spotify |
| 10 | `PlaylistService` | Оркестратор — после того как сервисы готовы |
| 11 | Финальные роуты | Убираем заглушки, всё сходится |

---

## Главный принцип, который объединяет всё

> **Сделай минимум → убедись что работает → добавь следующий слой.**

Никогда не пиши код который ты не можешь сразу проверить.  
Если написал сервис — запусти в консоли.  
Если подключил к роуту — проверь curl.  
Если сломал — ты знаешь **какой именно шаг** что-то поломал.

Это называется **tight feedback loop** — короткая петля обратной связи.  
Senior не пишет 300 строк и потом начинает отлаживать.  
Senior пишет 30 строк, проверяет, пишет ещё 30.
