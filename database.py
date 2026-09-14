import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent /'bot.db'


def init_db() -> None:
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute(
            '''
            CREATE TABLE IF NOT EXISTS user_stats (
                user_id INTEGER PRIMARY KEY,
                correct INTEGER NOT NULL DEFAULT 0,
                total INTEGER NOT NULL DEFAULT 0
            )
            '''
        )

        connection.execute(
            '''
            CREATE TABLE IF NOT EXISTS words (
                id INTEGER PRIMARY KEY,
                english TEXT NOT NULL,
                russian TEXT NOT NULL
            )
            '''
        ) 




def update_stats(user_id: int, is_correct: bool) -> None: 
    correct_increment = 1 if is_correct else 0


    with sqlite3.connect(DB_PATH) as connection:
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


def get_stats(user_id: int):

    with sqlite3.connect(DB_PATH) as connection:
        cursor =  connection.execute(
            '''
            SELECT correct, total FROM user_stats WHERE user_id = ?
            ''',
            (user_id,),
        )

        return cursor.fetchone()


