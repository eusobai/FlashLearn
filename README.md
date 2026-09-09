````markdown
# English Learning Telegram Bot

Telegram-бот для изучения английского языка.

## Что умеет сейчас

- отвечает на команду `/start`;
- приветствует пользователя;
- получает текстовые сообщения;
- повторяет отправленный текст;
- выводит сообщения пользователей в терминал для отладки.

## Что планируется

- карточки с английскими словами;
- тесты на перевод слов;
- игра на сопоставление слова и перевода;
- сохранение прогресса пользователя;
- статистика изучения слов;
- кнопки и удобное меню.

## Технологии

- Python
- aiogram 3
- Telegram Bot API
- python-dotenv

## Установка

Клонируй репозиторий:

```bash
git clone https://github.com/eusobai/FlashLearn.git
cd FlashLearn
```

Создай виртуальное окружение:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Установи зависимости:

```powershell
py -m pip install -r requirements.txt
```

## Настройка токена

Создай файл `.env` в корне проекта:

```env
BOT_TOKEN=твой_токен_от_BotFather
```

Никогда не загружай `.env` в GitHub. Файл уже должен быть добавлен в `.gitignore`.

## Запуск

```powershell
py main.py
```

После успешного запуска в терминале появится:

```text
Бот запустился
```

Открой Telegram, найди своего бота и отправь:

```text
/start
```

## Структура проекта

```text
.
├── main.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```