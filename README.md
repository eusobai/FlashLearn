# English Learning Telegram Bot

Telegram-бот для изучения английского языка с карточками, тестами.


## Возможности

- `/start` — запуск бота.
- `/card` — случайное английское слово.
- `/quiz` — тренировка случайных слов.
- `/stats` — статистика ответов.
- `/favourites` — сохранённые слова.
- `/help` — помощь.
- Добавление слов в избранное через inline-кнопку.
- Тренировка только по сохранённым словам.
- Несколько допустимых переводов одного слова.
- Подсчёт правильных и общих ответов.
- Расчёт точности.
- Логирование работы бота.

## Главное меню

- 📚 Учить слова
- 🧠 Тренировка
- 📖 Мои слова
- 📊 Моя статистика
- ❓ Помощь

В разделе «📖 Мои слова» есть кнопка **🧠 Тренировка моих слов**. После нажатия бот выбирает случайное слово только из избранного пользователя.

## Технологии

- Python
- aiogram 3
- PostgreSQL
- Supabase
- psycopg2
- python-dotenv

## Структура проекта

```text
FlashLearn/
├── main.py
├── database.py
├── .env
├── .env.example
├── requirements.txt
├── .gitignore
└── logs/
    └── bot.log
```

### `main.py`

Основная логика Telegram-бота: команды, клавиатуры, карточки слов, тренировки, проверка ответов, избранные слова, статистика и логирование.

### `database.py`

Работа с PostgreSQL: подключение к базе, пользователи, статистика, избранные слова и получение слов.

## База данных

FlashLearn использует PostgreSQL в Supabase.

Основные таблицы:

```text
users
user_stats
favourite_words
topics
levels
parts_of_speech
words
```

### `users`

```text
user_id
```

### `user_stats`

```text
user_id
correct
total
```

### `favourite_words`

```text
id
user_id
word_id
```

Используется ограничение:

```text
UNIQUE(user_id, word_id)
```

### `words`

```text
id
english
russian
definition
example
topic_id
level_id
part_of_speech_id
pronunciation
created_at
```

### Справочные таблицы

```text
topics
levels
parts_of_speech
```

Они связывают слово с темой, уровнем английского и частью речи.

Уровни:

```text
A1
A2
B1
B2
C1
C2
```

## Несколько переводов

Одно слово может иметь несколько допустимых переводов:

```text
причина; довод
```

Перед проверкой ответов строка разделяется:

```python
correct_answers = [
    answer.strip().lower()
    for answer in word["russian"].split(";")
]
```

Получается:

```python
["причина", "довод"]
```

Любой вариант считается правильным.

## Переменные окружения

Секреты не хранятся в Git.

```env
BOT_TOKEN=your_bot_token_here
DATABASE_URL=your_database_url_here
```

Реальные токены, пароли и ключи нельзя добавлять в GitHub.

## Установка

```bash
git clone https://github.com/eusobai/FlashLearn.git
cd FlashLearn
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

Установить зависимости:

```bash
pip install -r requirements.txt
```

Создать `.env` и указать:

```env
BOT_TOKEN=...
DATABASE_URL=...
```

Запустить:

```bash
python main.py
```

## Логирование

Логи записываются в:

```text
logs/bot.log
```

Например:

```text
Quiz answered | user_id=... | correct=True
```


## Планируемое развитие

- категории и фильтрация слов;
- выбор уровня английского;
- новые типы тренировок;
- улучшение статистики;
- система прогресса;
- улучшение интерфейса;
- масштабирование словаря;
- монетизация.