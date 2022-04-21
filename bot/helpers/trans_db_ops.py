import sqlite3
from datetime import datetime
from sqlite3 import Connection
from typing import Union

import pytz
from bot import TRANSACTIONS_DB_FILENAME


def connect_db() -> Connection:
    return sqlite3.connect(TRANSACTIONS_DB_FILENAME)


def seed_db() -> None:
    print('Creating transactions DB now!')
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE "transactions" (
        "tran_hash"	TEXT,
        "sender_id"	INTEGER,
        "receiver_id"	INTEGER,
        "amount"	INTEGER,
        "status"	TEXT,
        "tran_time"	INTEGER
    );''')
    cursor.execute('''CREATE TABLE "bot_data" (
        "balance"	INTEGER
    );''')
    cursor.execute('''INSERT INTO bot_data (balance) VALUES (?)''', (0,))
    conn.commit()
    conn.close()


# Getter methods
def get_transaction(hash: str) -> Union[None, tuple]:
    conn = connect_db()
    cursor_obj = conn.cursor()
    d = cursor_obj.execute(
        '''SELECT * FROM transactions WHERE tran_hash = ?''', (hash,)).fetchone()
    conn.close()
    return d


def get_initiated_transactions(sender_id: int) -> list:
    conn = connect_db()
    cursor_obj = conn.cursor()
    d = cursor_obj.execute(
        '''SELECT * FROM transactions WHERE sender_id = ? AND status = ? ORDER BY tran_time DESC LIMIT 5''', (sender_id, 'Complete')).fetchall()
    conn.close()
    return d


def get_received_transactions(receiver_id: int) -> list:
    conn = connect_db()
    cursor_obj = conn.cursor()
    d = cursor_obj.execute(
        '''SELECT * FROM transactions WHERE receiver_id = ? AND status = ? ORDER BY tran_time DESC LIMIT 5''', (receiver_id, 'Complete')).fetchall()
    conn.close()
    return d


def get_pending_transaction(telegram_id: int) -> Union[None, tuple]:
    conn = connect_db()
    cursor_obj = conn.cursor()
    d = cursor_obj.execute(
        '''SELECT * FROM transactions WHERE sender_id = ? AND status = ?''', (telegram_id, 'Pending')).fetchone()
    conn.close()
    return d


def get_all_pending_transactions() -> list:
    conn = connect_db()
    cursor_obj = conn.cursor()
    d = cursor_obj.execute(
        '''SELECT * FROM transactions WHERE status = ?''', ('Pending',)).fetchall()
    conn.close()
    return d


# Setter methods
def add_transaction(hash: str, sender_id: int, receiver_id: int, amount: int) -> None:
    conn = connect_db()
    cursor_obj = conn.cursor()
    t = int(datetime.timestamp(datetime.now().astimezone(
        pytz.timezone('Asia/Kolkata'))) * 1000000)
    cursor_obj.execute('''INSERT INTO transactions VALUES (?,?,?,?,?,?)''',
                       (hash, sender_id, receiver_id, amount, 'Pending', t))
    conn.commit()
    conn.close()


def confirm_transaction(hash: str) -> None:
    conn = connect_db()
    cursor_obj = conn.cursor()
    cursor_obj.execute(
        '''UPDATE transactions SET status = ? WHERE tran_hash = ?''', ('Complete', hash))
    conn.commit()
    conn.close()


def del_transaction(hash: str) -> None:
    conn = connect_db()
    cursor_obj = conn.cursor()
    cursor_obj.execute(
        '''DELETE FROM transactions WHERE tran_hash = ?''', (hash,))
    conn.commit()
    conn.close()


def add_bot_balance(amt: int) -> None:
    conn = connect_db()
    cursor_obj = conn.cursor()
    d = cursor_obj.execute('''SELECT balance FROM bot_data;''').fetchone()[0]
    d = d + amt
    cursor_obj.execute('''UPDATE bot_data SET balance = ?''', (d,))
    conn.commit()
    conn.close()
