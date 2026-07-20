# Telegram AI Assistant

Telegram AI Assistant — это Telegram-бот на Python с поддержкой искусственного интеллекта. Проект построен на многослойной архитектуре и поддерживает текстовые диалоги, анализ изображений, обработку голосовых сообщений и хранение истории общения.

## Возможности

- Текстовый чат с AI
- Контекст диалога
- Память пользователя
- Анализ изображений
- Распознавание голосовых сообщений
- PostgreSQL для хранения данных
- Redis для ограничения запросов и состояний
- Docker Compose для быстрого запуска
- Возможность заменить AI-провайдера без изменения бизнес-логики

## Стек

- Python 3.12
- aiogram 3
- SQLAlchemy 2.0
- PostgreSQL
- Redis
- Google Gemini API
- Alembic
- Docker

## Структура проекта

```
app/
bot/
config/
database/
services/
tests/
utils/
```

Основная логика находится в `services`. Telegram-обработчики отвечают только за получение и отправку сообщений.

## Запуск

Клонировать репозиторий

```bash
git clone https://github.com/Gyso4ka/telegram-ai-assistant.git
cd telegram-ai-assistant
```

Создать файл окружения

```bash
cp .env.example .env
```

Заполнить необходимые переменные

```env
BOT_TOKEN=...
GEMINI_API_KEY=...
```

Запустить проект

```bash
docker compose up --build
```

## Тестирование

```bash
pytest
```

## Архитектура

Проект разделён на несколько слоёв:

```
Telegram
    │
Handlers
    │
Services
    ├── AI
    ├── Database
    └── Memory
```

Бизнес-логика не находится в Telegram-хендлерах. Работа с AI, памятью и базой данных вынесена в отдельные сервисы.

## Планы

- Добавление новых AI-провайдеров
- Векторная память
- Webhook-режим
- Web-интерфейс

## License

MIT