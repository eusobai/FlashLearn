import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent /'bot.db'


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db() -> None:
    with get_connection() as connection:

        connection.execute(
            '''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY UNIQUE
            )
            '''
        )


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

        
        connection.execute(
            '''
            CREATE TABLE IF NOT EXISTS favourite_word (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                word TEXT NOT NULL,
                translation TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                UNIQUE(user_id, word, translation) 
            )
            '''
        ) 



def add_user_to_db(user_id: int) -> None:
    with get_connection() as connection:
        connection.execute(
            '''
            INSERT OR IGNORE INTO users (user_id)
            VALUES (?)
            ''',
            (user_id,)
        )



def update_stats_in_db(user_id: int, is_correct: bool) -> None: 
    correct_increment = 1 if is_correct else 0


    with get_connection() as connection:
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


def get_stats_from_db(user_id: int):

    with get_connection() as connection:
        cursor =  connection.execute(
            '''
            SELECT correct, total FROM user_stats WHERE user_id = ?
            ''',
            (user_id,),
        )

        return cursor.fetchone()


def reset_stats_in_db(user_id: int) -> None:
    with get_connection() as connection:
        connection.execute(
            '''
            UPDATE user_stats SET correct = 0,total = 0
            WHERE user_id = ?
            ''',
            (user_id,)
    )

def add_fav_word_to_db(user_id: int, word: str, translation: str) -> None:
    with get_connection() as connection:


        connection.execute(
            '''
            INSERT OR IGNORE INTO favourite_word(user_id, word, translation)
            VALUES(?,?,?)
            ''',
            (user_id, word, translation)
        )
