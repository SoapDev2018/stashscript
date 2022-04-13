import sqlite3
from sqlite3 import Connection
from typing import Union

from bot import STREAK_DB_FILENAME


def connect_db() -> Connection:
    return sqlite3.connect(STREAK_DB_FILENAME)


def seed_db() -> None:
    print('Seeding streaks DB now!')
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS "xp_points" (
        "telegram_id"	INTEGER,
        "xp"	INTEGER,
        "streak"	INTEGER,
        "points"	INTEGER,
        "daily_xp"	INTEGER,
        "daily_xp_granted"	TEXT,
        "user_level"	INTEGER,
        "last_chat_date"	TEXT,
        "user_full_name"	TEXT,
        "mentions"	TEXT,
        "profile_type"	TEXT
    );''')
    conn.close()


# Getter methods
def get_details(telegram_id: int) -> Union[tuple, None]:
    conn = connect_db()
    cursor_obj = conn.cursor()
    d = cursor_obj.execute(
        '''SELECT * FROM xp_points WHERE telegram_id = ?''', (telegram_id,)).fetchone()
    conn.close()
    return d


def get_all_details() -> list:
    conn = connect_db()
    cursor_obj = conn.cursor()
    d = cursor_obj.execute('''SELECT * FROM xp_points;''').fetchall()
    conn.close()
    return d


def get_leaderboard() -> list:
    conn = connect_db()
    cursor_obj = conn.cursor()
    d = cursor_obj.execute(
        '''SELECT * FROM xp_points WHERE xp > 0 ORDER BY xp DESC LIMIT 5;''').fetchall()
    conn.close()
    return d


def get_lvl_leaderboard() -> list:
    conn = connect_db()
    cursor_obj = conn.cursor()
    d = cursor_obj.execute(
        '''SELECT * FROM xp_points WHERE user_level > 0 ORDER BY user_level DESC LIMIT 5;''').fetchall()
    conn.close()
    return d

# Setter methods


def create_user(telegram_id: int, time: str, user_full_name: Union[str, None]) -> None:
    conn = connect_db()
    cursor_obj = conn.cursor()
    if user_full_name is None:
        user_full_name = 'NoName'
    cursor_obj.execute(
        '''INSERT INTO xp_points VALUES (?,?,?,?,?,?,?,?,?,?,?)''', (telegram_id, 0, 0, 0, 0, 'No', 0, time, user_full_name, "Off", "Public"))
    print(f'Created new user {telegram_id}')
    conn.commit()
    conn.close()


def set_xp(telegram_id: int, xp: int) -> None:
    conn = connect_db()
    cursor_obj = conn.cursor()
    cursor_obj.execute(
        '''UPDATE xp_points SET xp = ? WHERE telegram_id = ?''', (xp, telegram_id,))
    conn.commit()
    conn.close()


def set_daily_xp(telegram_id: int, daily_xp: int) -> None:
    conn = connect_db()
    cursor_obj = conn.cursor()
    d = cursor_obj.execute(
        '''SELECT daily_xp FROM xp_points WHERE telegram_id = ?''', (telegram_id,)).fetchone()
    if d is not None:
        d = int(d[0])
    daily_xp += d
    cursor_obj.execute(
        '''UPDATE xp_points SET daily_xp = ? WHERE telegram_id = ?''', (daily_xp, telegram_id,))
    conn.commit()
    conn.close()


def reset_daily_xp(telegram_id: int) -> None:
    conn = connect_db()
    cursor_obj = conn.cursor()
    cursor_obj.execute(
        '''UPDATE xp_points SET daily_xp = ? WHERE telegram_id = ?''', (0, telegram_id,))
    conn.commit()
    conn.close()


def set_streak(telegram_id: int, streak: int) -> None:
    conn = connect_db()
    cursor_obj = conn.cursor()
    cursor_obj.execute(
        '''UPDATE xp_points SET streak = ? WHERE telegram_id = ?''', (streak, telegram_id,))
    conn.commit()
    conn.close()


def set_daily_xp_granted(telegram_id: int) -> None:
    conn = connect_db()
    cursor_obj = conn.cursor()
    cursor_obj.execute(
        '''UPDATE xp_points SET daily_xp_granted = ? WHERE telegram_id = ?''', ('Yes', telegram_id,))
    conn.commit()
    conn.close()


def reset_daily_xp_granted(telegram_id: int) -> None:
    conn = connect_db()
    cursor_obj = conn.cursor()
    cursor_obj.execute(
        '''UPDATE xp_points SET daily_xp_granted = ? WHERE telegram_id = ?''', ('No', telegram_id,))
    conn.commit()
    conn.close()


def set_level(telegram_id: int, level: int) -> None:
    conn = connect_db()
    cursor_obj = conn.cursor()
    cursor_obj.execute(
        '''UPDATE xp_points SET user_level = ? WHERE telegram_id = ?''', (level, telegram_id))
    conn.commit()
    conn.close()


def set_points(telegram_id: int, points: int) -> None:
    conn = connect_db()
    cursor_obj = conn.cursor()
    cursor_obj.execute(
        '''UPDATE xp_points SET points = ? WHERE telegram_id = ?''', (points, telegram_id,))
    conn.commit()
    conn.close()


def set_last_chat_date(telegram_id: int, date: str) -> None:
    conn = connect_db()
    cursor_obj = conn.cursor()
    cursor_obj.execute(
        '''UPDATE xp_points SET last_chat_date = ? WHERE telegram_id = ?''', (date, telegram_id,))
    conn.commit()
    conn.close()


def set_user_full_name(telegram_id: int, user_full_name: str) -> None:
    conn = connect_db()
    cursor_obj = conn.cursor()
    cursor_obj.execute(
        '''UPDATE xp_points SET user_full_name = ? WHERE telegram_id = ?''', (user_full_name, telegram_id))
    conn.commit()
    conn.close()


def set_mention(telegram_id: int, choice: str) -> None:
    conn = connect_db()
    cursor_obj = conn.cursor()
    cursor_obj.execute(
        '''UPDATE xp_points SET mentions = ? WHERE telegram_id = ?''', (choice, telegram_id))
    conn.commit()
    conn.close()


def set_profile_type(telegram_id: int, profile_type: str) -> None:
    conn = connect_db()
    cursor_obj = conn.cursor()
    cursor_obj.execute(
        '''UPDATE xp_points SET profile_type = ? WHERE telegram_id = ?''', (profile_type, telegram_id))
    conn.commit()
    conn.close()
