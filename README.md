```
app/
├── config.py              # Конфиги для dev/test/prod
├── __init__.py            # App Factory
├── models/
│   └── schemas.py         # Pydantic-схемы (валидация данных)
├── routes/
│   └── playlist.py
├── services/
│   ├── music_service.py    # Работа с Spotify API
│   ├── ai_service.py       # Интерпретация текста через Claude
│   └── playlist_service.py # Бизнес-логика (оркестратор)
└── utils/
    └── exceptions.py      # Кастомные исключения
```