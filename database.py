# =========================
# ИМПОРТЫ
# =========================

# psycopg2 — библиотека, которая позволяет Python
# подключаться и работать с PostgreSQL.
import psycopg2

# os позволяет получать значения переменных окружения.
# Например, DATABASE_URL из файла .env.
import os

# load_dotenv() загружает переменные из файла .env
# в переменные окружения Python.
from dotenv import load_dotenv 

# Загружаем данные из файла .env
load_dotenv()

# Получаем адрес подключения к PostgreSQL.
#
# В .env у нас находится примерно:
#
# DATABASE_URL=postgresql://...
#
# os.getenv() достаёт значение DATABASE_URL.
DATABASE_URL = os.getenv('DATABASE_URL')

# =========================
# ПОДКЛЮЧЕНИЕ К БАЗЕ ДАННЫХ
# =========================



def get_connection():
        
    # Открываем соединение с PostgreSQL.
    # psycopg2.connect() создаёт connection —
    # соединение Python с PostgreSQL.
    return psycopg2.connect(DATABASE_URL)





# =========================
# ДОБАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯ
# =========================


def add_user_to_db(user_id: int) -> None:
    # Открываем соединение с PostgreSQL.
    #
    # with автоматически завершит работу
    # с connection после выполнения блока.
    with get_connection() as connection:

        # cursor — объект, через который
        # мы отправляем SQL-запросы в PostgreSQL.
        #
        # connection — это соединение с базой,
        # cursor — инструмент для выполнения SQL.        
        cursor = connection.cursor()
        
        # Добавляем пользователя в таблицу users.
        cursor.execute(
            '''
            INSERT INTO users (user_id)
            VALUES (%s)
            ON CONFLICT DO NOTHING
            ''',
            (user_id,)
        )

       # Закрываем cursor после выполнения запроса.
        cursor.close()

# =========================
# ОБНОВЛЕНИЕ СТАТИСТИКИ
# =========================


def update_stats_in_db(user_id: int, is_correct: bool) -> None: 

    # Если ответ правильный:
    #
    # is_correct = True
    # correct_increment = 1
    #
    # Если ответ неправильный:
    #
    # is_correct = False
    # correct_increment = 0
    correct_increment = 1 if is_correct else 0


    with get_connection() as connection:

        # Если пользователь проходит тест впервые,
        # создаём для него новую строку статистики.
        #
        # Если статистика уже существует,
        # обновляем существующую строку.
        cursor = connection.cursor() 

        cursor.execute(    
            '''
            INSERT INTO user_stats (user_id, correct, total)
            VALUES (%s, %s, 1)
            ON CONFLICT(user_id) DO UPDATE SET
                correct = user_stats.correct + EXCLUDED.correct,
                total = user_stats.total + 1
            ''',
            (user_id, correct_increment),
        )

        cursor.close()

# =========================
# ПОЛУЧЕНИЕ СТАТИСТИКИ
# =========================


def get_stats_from_db(user_id: int):

    with get_connection() as connection:

        cursor = connection.cursor()  
        
        # Ищем статистику конкретного пользователя.
        cursor.execute(
            '''
            SELECT correct, total FROM user_stats WHERE user_id = %s
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
        result = cursor.fetchone()

        cursor.close()

       # Возвращаем результат в main.py.
        return result

# =========================
# СБРОС СТАТИСТИКИ
# =========================


def reset_stats_in_db(user_id: int) -> None:

    with get_connection() as connection:

        cursor = connection.cursor()

        # Обнуляем статистику только конкретного пользователя.
        cursor.execute(
            '''
            UPDATE user_stats SET correct = 0,total = 0
            WHERE user_id = %s
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

        cursor = connection.cursor()

        # Сохраняем:
        #
        # ID пользователя,
        # английское слово,
        # перевод.
        cursor.execute(
            '''
            INSERT INTO favourite_words(user_id, word, translation)
            VALUES( %s, %s, %s )
            ON CONFLICT DO NOTHING
            ''',
            (user_id, word, translation)
        )

        cursor.close()

# =========================
# ПОЛУЧЕНИЕ ИЗБРАННОГО СЛОВА 
# =========================


def get_fav_words_in_db(user_id: int):

    with get_connection() as connection:

        # Ищем избранных слов конкретного пользователя
        cursor = connection.cursor()
        
        cursor.execute(
            '''
            SELECT word, translation FROM favourite_words WHERE user_id = %s 
            ''',
            (user_id,)
        )

        result = cursor.fetchall()
        
        cursor.close()
    
        return result