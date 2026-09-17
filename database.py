# =========================
# ИМПОРТЫ
# =========================


import sqlite3
from pathlib import Path

# Путь к файлу базы данных.
#
# __file__ — путь к текущему файлу database.py.
# resolve() превращает его в абсолютный путь.
# parent — папка, в которой находится database.py.
#
# В результате база bot.db будет находиться
# в папке проекта рядом с database.py.
DB_PATH = Path(__file__).resolve().parent /'bot.db'

# =========================
# ПОДКЛЮЧЕНИЕ К БАЗЕ ДАННЫХ
# =========================


def get_connection():
    # Открываем соединение с SQLite.
    connection = sqlite3.connect(DB_PATH)

    # Включаем поддержку FOREIGN KEY.
    #
    # Без этого SQLite не будет проверять связи
    # между таблицами users, user_stats
    # и favourite_word.
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


# =========================
# СОЗДАНИЕ ТАБЛИЦ
# =========================


def init_db() -> None:

    # Открываем соединение с базой данных.
    # После выхода из with изменения сохраняются,
    # а соединение автоматически закрывается.
    with get_connection() as connection:

        # -------------------------
        # Таблица пользователей
        # -------------------------


        # Храним Telegram ID пользователей.
        #
        # user_id — PRIMARY KEY, поэтому
        # два одинаковых пользователя
        # существовать не могут.
        connection.execute(
            '''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY UNIQUE
            )
            '''
        )


        # -------------------------
        # Таблица статистики
        # -------------------------


        # Для каждого пользователя хранится:
        # correct — количество правильных ответов;
        # total — общее количество попыток.
        #
        # user_id одновременно является:
        # PRIMARY KEY — у пользователя только одна строка статистики;
        # FOREIGN KEY — пользователь должен существовать в таблице users.
        connection.execute(
            '''
            CREATE TABLE IF NOT EXISTS user_stats (
                user_id INTEGER PRIMARY KEY,
                correct INTEGER NOT NULL DEFAULT 0,
                total INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (user_id) 
                    REFERENCES users(user_id)
                    ON DELETE CASCADE
            )
            '''
        )


        # -------------------------
        # Таблица избранных слов
        # -------------------------

        # Храним слова, которые пользователь добавил в избранное.
        #
        # Один пользователь может иметь много избранных слов.
        #
        # id — уникальный номер записи;
        # user_id — какому пользователю принадлежит слово;
        # word — английское слово;
        # translation — его перевод.        
        connection.execute(
            '''
            CREATE TABLE IF NOT EXISTS favourite_words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                word TEXT NOT NULL,
                translation TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                UNIQUE(user_id, word, translation) 
            )
            '''
        ) 


# =========================
# ДОБАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯ
# =========================


def add_user_to_db(user_id: int) -> None:

    with get_connection() as connection:

        # Добавляем пользователя в таблицу.
        #
        # INSERT OR IGNORE означает:
        # если такой user_id уже существует,
        # ничего не делать и не выдавать ошибку.
        connection.execute(
            '''
            INSERT OR IGNORE INTO users (user_id)
            VALUES (?)
            ''',
            (user_id,)
        )


# =========================
# ОБНОВЛЕНИЕ СТАТИСТИКИ
# =========================


def update_stats_in_db(user_id: int, is_correct: bool) -> None: 

    # Если ответ правильный — увеличиваем correct на 1.
    # Если неправильный — correct увеличивать не нужно.
    correct_increment = 1 if is_correct else 0


    with get_connection() as connection:

        # Если пользователь проходит тест впервые,
        # создаём для него новую строку статистики.
        #
        # Если статистика уже существует,
        # обновляем существующую строку.
        connection.execute(
            
            '''
            INSERT INTO user_stats (user_id, correct, total)
            VALUES (?, ?, 1)
            ON CONFLICT(user_id) DO UPDATE SET
                correct = correct + excluded.correct,
                total = total + 1
            ''',
            (user_id, correct_increment),
        )


# =========================
# ПОЛУЧЕНИЕ СТАТИСТИКИ
# =========================


def get_stats_from_db(user_id: int):

    with get_connection() as connection:

        # Ищем статистику конкретного пользователя.
        cursor =  connection.execute(
            '''
            SELECT correct, total FROM user_stats WHERE user_id = ?
            ''',
            (user_id,),
        )

        # fetchone() получает одну найденную строку.
        #
        # Например:
        # (8, 10)
        #
        # Если записи нет:
        # None
        return cursor.fetchone()


# =========================
# СБРОС СТАТИСТИКИ
# =========================


def reset_stats_in_db(user_id: int) -> None:

    with get_connection() as connection:

        # Обнуляем статистику только конкретного пользователя.
        connection.execute(
            '''
            UPDATE user_stats SET correct = 0,total = 0
            WHERE user_id = ?
            ''',
            (user_id,)
    )


# =========================
# ДОБАВЛЕНИЕ В ИЗБРАННОЕ
# =========================


def add_fav_word_to_db(
    user_id: int, 
    word: str, 
    translation: str
) -> None:

    with get_connection() as connection:

        # Сохраняем:
        # ID пользователя,
        # английское слово,
        # перевод.
        #
        # INSERT OR IGNORE означает:
        # если точно такая запись уже существует,
        # SQLite не создаст дубликат.
        connection.execute(
            '''
            INSERT OR IGNORE INTO favourite_words(user_id, word, translation)
            VALUES(?,?,?)
            ''',
            (user_id, word, translation)
        )


# =========================
# ПОЛУЧЕНИЕ ИЗБРАННОГО СЛОВА 
# =========================


def get_fav_words_in_db(user_id: int):

    with get_connection() as connection:

        # Ищем избранных слов конкретного пользователя
        cursor = connection.execute(
            '''
            SELECT word, translation FROM favourite_words WHERE user_id = ?
            ''',
            (user_id,)
        )

        return cursor.fetchall()