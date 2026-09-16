# Telegram Assistant + Mini App

Личный Telegram-ассистент: задачи, Google Calendar, напоминания, утренние и вечерние дайджесты. Mini App позволяет работать с задачами и календарём внутри Telegram. Разбор сообщений и голосовых записей использует Gemini.

Стек: Python, aiogram, FastAPI, SQLite; интерфейс Mini App — HTML/CSS/JavaScript.

## Быстрый запуск

Требуется Python 3.12+. Команды выполняются из корня репозитория.

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Заполните локальный `.env`:

- `BOT_TOKEN` — токен бота из BotFather.
- `GEMINI_API_KEY` — ключ Gemini для разбора текста и голоса.
- `OAUTH_STATE_SECRET` — собственная случайная строка, постоянная между запусками. Она также используется для шифрования Google refresh tokens; сохраните её в надёжном месте.
- `PUBLIC_BASE_URL` — публичный HTTPS-адрес сервера без завершающего `/`.
- При необходимости измените `HOST`, `PORT`, `USER_TIMEZONE` и пути хранения.

Сгенерировать OAuth-секрет локально:

```powershell
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(48))"
```

В Google Cloud включите Calendar API и настройте OAuth consent screen. Создайте OAuth client типа Web application, скачайте его JSON в `client_secret.json` в корне проекта. Добавьте redirect URI: `https://YOUR_DOMAIN/oauth/google/callback` (домен должен совпадать с `PUBLIC_BASE_URL`). Если приложение в режиме тестирования, добавьте свой Google-аккаунт в test users.

```powershell
.\.venv\Scripts\python.exe main.py
```

Альтернатива в Windows: `./start.ps1`. На Linux/macOS используйте `python3 -m venv .venv`, затем `.venv/bin/python` вместо Windows-пути и `cp .env.example .env`.

Сервер по умолчанию слушает порт 8080; проверка состояния: `/health`. Настройте HTTPS через свой reverse proxy или туннель, затем укажите в BotFather адрес Mini App `https://YOUR_DOMAIN/app`. Откройте бота в Telegram и подключите Google Calendar через настройки. Бот получает сообщения через polling; запускайте один экземпляр на токен.

## Структура

- `main.py` — запуск HTTP-сервера, polling и напоминаний.
- `app/` — логика бота, календаря, хранилища и API.
- `app/static/miniapp.html` — интерфейс Mini App.
- `tests/` — существующие автоматические проверки.
- `.env.example` — шаблон конфигурации без секретов.

## Проверки

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## Приватные данные

`.env`, OAuth credentials, ключи, `data/`, базы SQLite, логи, архивы и виртуальные окружения исключены через `.gitignore`. Не добавляйте их принудительно через `git add -f`. Шаблон `.env.example` должен содержать только заглушки. Нестандартные файлы секретов вне исключённых путей нужно отдельно добавлять в `.gitignore`.

Репозиторий рекомендуется хранить приватным. Размещение исходников на GitHub само по себе не запускает бота: ему нужен постоянно работающий сервер. Резервные копии базы и OAuth-секрета храните отдельно от Git.
