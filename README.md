# Сервис бронирования переговорных комнат

## Описание проекта

Веб-сервис для автоматизации бронирования переговорных комнат в коворкинге. 
Система предотвращает наложения встреч, проверяет вместимость комнат и 
разграничивает права доступа пользователей.

## Возможности

- Просмотр доступных комнат и временных слотов
- Создание и отмена бронирований
- Автоматическая проверка пересечений времени
- Проверка вместимости комнаты
- Регистрация и аутентификация пользователей
- Разграничение прав доступа (сотрудник/администратор)
- Валидация данных через Pydantic
- Документация API

## Технологический стек

- **Язык:** Python 3.11+
- **Фреймворк:** FastAPI
- **База данных:** PostgreSQL 15
- **ORM:** SQLAlchemy
- **Аутентификация:** JWT
- **Валидация:** Pydantic
- **Тестирование:** pytest
- **Контейнеризация:** Docker

## Установка

```bash
git clone <repository-url>
cd meeting-room-booking
poetry install
```

## Запуск

### Через Docker

```bash
docker-compose up --build
```

### Локально

```bash
poetry run uvicorn app.main:app --reload
```

## Примеры работы

### Регистрация

```bash
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@mail.ru",
  "password": "secure123",
  "full_name": "Иван Иванов"
}
```

### Создание бронирования

```bash
POST /api/bookings
Authorization: Bearer <token>
Content-Type: application/json

{
  "room_id": 1,
  "date": "2026-06-25",
  "time_slot": "11:00-13:00",
  "participants_count": 5
}
```

## Тестирование

```bash
poetry run pytest tests/ -v
```
