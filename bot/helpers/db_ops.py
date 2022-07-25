import sqlite3
from datetime import datetime
from sqlite3 import Connection
from typing import Tuple, Union

import pytz
from bot import DB_FILENAME

# DB_FILENAME = 'stashscript.db'


def connect_db() -> Connection:
    conn = sqlite3.connect(DB_FILENAME)
    return conn


def seed_db() -> None:
    print('Seeding User DB now')
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE "costs_tracker" (
        "don_received"	INTEGER,
        "don_spent"	INTEGER
    );''')
    cursor.execute('''
    CREATE TABLE "drives_data_tracker" (
        "drive_id"	TEXT,
        "drive_name"	TEXT,
        "drive_type"	TEXT,
        "drive_size"	TEXT
    );''')
    cursor.execute('''
    CREATE TABLE "invite_funcs" (
        "user_id"	INTEGER,
        "action"	TEXT
    );''')
    cursor.execute('''
    CREATE TABLE "invites" (
        "user_id"	INTEGER,
        "user_full_name"	TEXT,
        "invite_code"	TEXT
    );''')
    cursor.execute('''
    CREATE TABLE "members" (
        "id"	INTEGER NOT NULL UNIQUE,
        "telegram_id"	INTEGER UNIQUE,
        "email"	TEXT NOT NULL UNIQUE,
        "payment_method"	TEXT,
        "last_payment_date"	TEXT,
        "access_until"	TEXT,
        "donator_type"	TEXT,
        "total_donations"	INTEGER,
        "privileges"	TEXT,
        "last_email_change_date"	TEXT,
        "has_hw_access"	TEXT,
        "has_curator_access"	TEXT,
        "invites_avail"	INTEGER,
        PRIMARY KEY("id" AUTOINCREMENT)
    );''')
    cursor.execute('''
    CREATE TABLE "price_tracker" (
        "bat_usdt"	NUMERIC,
        "inr_usd"	NUMERIC,
        "usdt_usd"	NUMERIC)
    ;''')
    conn.close()


def close_db(conn: Connection) -> None:
    conn.close()


def get_today_date() -> str:
    return datetime.now().astimezone(pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%d')


def is_donator(telegram_id: int) -> bool:
    conn = connect_db()
    cursor_obj = conn.cursor()
    rows = cursor_obj.execute(
        'SELECT * FROM members WHERE telegram_id = ?', (telegram_id,)).fetchall()
    close_db(conn)
    if len(rows) == 1:
        return True
    return False


def is_staff(telegram_id: int) -> bool:
    conn = connect_db()
    cursor_obj = conn.cursor()
    row = cursor_obj.execute(
        'SELECT donator_type FROM members WHERE telegram_id = ?', (telegram_id,)).fetchone()
    close_db(conn)
    if row is not None:
        if row[0] == 'Staff':
            return True
    return False


def get_donator_details(telegram_id: int) -> tuple:
    conn = connect_db()
    cursor_obj = conn.cursor()
    row = cursor_obj.execute(
        'SELECT * FROM members WHERE telegram_id = ?', (telegram_id,)).fetchall()
    close_db(conn)
    if len(row) == 1:
        return row[0]
    return (None,)


def get_all_donator_details() -> list:
    conn = connect_db()
    cursor_obj = conn.cursor()
    data = cursor_obj.execute('''SELECT * FROM members;''').fetchall()
    conn.close()
    return data


def get_donation_details() -> list:
    conn = connect_db()
    cursor_obj = conn.cursor()
    row = cursor_obj.execute(
        'SELECT don_received, don_spent FROM costs_tracker;').fetchone()
    close_db(conn)
    donation_received = row[0]
    donation_spent = row[1]
    available_balance = donation_received - donation_spent
    return [round(float(donation_received), 2), round(float(donation_spent), 2), round(float(available_balance), 2)]


def get_drive_details(telegram_id: int) -> list:
    conn = connect_db()
    cursor_obj = conn.cursor()
    donator_level = cursor_obj.execute(
        'SELECT donator_type FROM members WHERE telegram_id = ?', (telegram_id, )).fetchone()[0]
    drive_details_rows = cursor_obj.execute(
        'SELECT drive_id, drive_name FROM drives_data_tracker WHERE drive_type = ?', ('Normal',)).fetchall()
    if donator_level == 'Staff' or donator_level == 'LTS':
        extra_drive_details_rows = cursor_obj.execute(
            'SELECT drive_id, drive_name FROM drives_data_tracker WHERE drive_type = ?', ('LTS', )).fetchall()
    else:
        extra_drive_details_rows = None
    close_db(conn)
    if extra_drive_details_rows:
        drive_details_rows.extend(extra_drive_details_rows)
    return drive_details_rows


def get_global_drive_details() -> list:
    conn = connect_db()
    cursor_obj = conn.cursor()
    rows = cursor_obj.execute(
        'SELECT drive_name, drive_type, drive_size, drive_id FROM drives_data_tracker ORDER BY drive_type DESC, drive_name COLLATE NOCASE ASC;').fetchall()
    close_db(conn)
    return rows


def get_price_rates() -> tuple:
    conn = connect_db()
    cursor_obj = conn.cursor()
    row = cursor_obj.execute(
        'SELECT bat_usdt, inr_usd, usdt_usd FROM price_tracker;').fetchone()
    close_db(conn)
    return row


def get_global_drive_ids() -> list:
    conn = connect_db()
    cursor_obj = conn.cursor()
    rows = cursor_obj.execute(
        'SELECT drive_id FROM drives_data_tracker;').fetchall()
    close_db(conn)
    return rows


def set_price_rates(bat: float, inr: float, usdt: float) -> None:
    conn = connect_db()
    cursor_obj = conn.cursor()
    cursor_obj.execute('UPDATE price_tracker SET bat_usdt = ?', (bat,))
    conn.commit()
    cursor_obj.execute('UPDATE price_tracker SET inr_usd = ?', (inr,))
    conn.commit()
    cursor_obj.execute('UPDATE price_tracker SET usdt_usd = ?', (usdt,))
    conn.commit()
    close_db(conn)


def set_drive_sizes(drive_update: list) -> None:
    conn = connect_db()
    cursor_obj = conn.cursor()
    for update in drive_update:
        drive_id = update['drive_id']
        drive_size = update['drive_size'] + " TB"
        cursor_obj.execute(
            'UPDATE drives_data_tracker SET drive_size = ? WHERE drive_id = ?', (drive_size, drive_id))
        conn.commit()
    close_db(conn)


def get_staff_privileges(telegram_id: int) -> list:
    conn = connect_db()
    cursor_obj = conn.cursor()
    row = cursor_obj.execute(
        'SELECT privileges FROM members WHERE telegram_id = ?', (telegram_id,)).fetchone()[0]
    conn.close()
    return row.split(',')[:-1]


def set_staff_privileges(telegram_id: int, privileges: str) -> None:
    conn = connect_db()
    cursor_obj = conn.cursor()
    cursor_obj.execute(
        '''UPDATE members SET privileges = ? WHERE telegram_id = ?''', (privileges, telegram_id))
    conn.commit()
    conn.close()


def add_new_donator(telegram_id: int, email: str, payment_method: str, last_payment_date: str, access_until: str, donator_type: str, amt: int) -> int:
    conn = connect_db()
    cursor_obj = conn.cursor()
    cursor_obj.execute('INSERT INTO members(telegram_id,email,payment_method,last_payment_date,access_until,donator_type,total_donations) VALUES(?,?,?,?,?,?,?)',
                       (telegram_id, email, payment_method, last_payment_date, access_until, donator_type, amt,))
    conn.commit()
    rowid = cursor_obj.lastrowid
    close_db(conn)
    return rowid


def add_payment(amt: float) -> None:
    conn = connect_db()
    cursor_obj = conn.cursor()
    row = cursor_obj.execute(
        'SELECT don_received FROM costs_tracker;').fetchone()[0]
    row = float(row)
    row += amt
    cursor_obj.execute('UPDATE costs_tracker SET don_received = ?', (row,))
    conn.commit()
    close_db(conn)


def del_payment(amt: float) -> None:
    conn = connect_db()
    cursor_obj = conn.cursor()
    row = float(cursor_obj.execute(
        'SELECT don_received FROM costs_tracker;').fetchone()[0])
    row -= amt
    cursor_obj.execute('UPDATE costs_tracker SET don_received = ?', (row,))
    conn.commit()
    close_db(conn)


def remove_donator(telegram_id: int) -> None:
    conn = connect_db()
    cursor_obj = conn.cursor()
    cursor_obj.execute(
        'DELETE FROM members WHERE telegram_id = ?', (telegram_id,))
    conn.commit()
    close_db(conn)


def get_last_email_change_date(telegram_id: int) -> Union[None, str]:
    conn = connect_db()
    cursor_obj = conn.cursor()
    row = cursor_obj.execute(
        'SELECT last_email_change_date FROM members WHERE telegram_id = ?', (telegram_id, )).fetchone()[0]
    close_db(conn)
    print(row)
    print(type(row))


def change_email(telegram_id: int, new_email: str) -> None:
    conn = connect_db()
    cursor_obj = conn.cursor()
    cursor_obj.execute(
        'UPDATE members SET last_email_change_date = ? WHERE telegram_id = ?', (get_today_date(), telegram_id,))
    cursor_obj.execute(
        'UPDATE members SET email = ? WHERE telegram_id = ?', (new_email, telegram_id,))
    conn.commit()
    close_db(conn)


def get_admin_donator_count() -> Tuple[int, int, int]:
    conn = connect_db()
    cursor_obj = conn.cursor()
    rows = cursor_obj.execute('SELECT * FROM members').fetchall()
    close_db(conn)
    is_staff = 0
    is_lts_donator = 0
    is_normal_donator = 0
    for row in rows:
        if row[6] == 'Staff':
            is_staff += 1
        else:
            if row[6] == 'LTS':
                is_lts_donator += 1
            else:
                is_normal_donator += 1
    return is_staff, is_lts_donator, is_normal_donator


def get_nsfw_access(telegram_id: int) -> bool:
    conn = connect_db()
    cursor_obj = conn.cursor()
    row = cursor_obj.execute(
        'SELECT has_hw_access FROM members WHERE telegram_id = ?', (telegram_id,)).fetchone()
    close_db(conn)
    if row is not None:
        if row[0] == 'Yes':
            return True
    return False


def get_curator_access(telegram_id: int) -> bool:
    conn = connect_db()
    cursor_obj = conn.cursor()
    row = cursor_obj.execute(
        'SELECT has_curator_access FROM members WHERE telegram_id = ?', (telegram_id,)).fetchone()
    close_db(conn)
    if row is not None:
        if row[0] == 'Yes':
            return True
    return False


def set_nsfw_access(telegram_id: int) -> None:
    conn = connect_db()
    cursor_obj = conn.cursor()
    cursor_obj.execute(
        'UPDATE members SET has_hw_access = ? WHERE telegram_id = ?', ('Yes', telegram_id,))
    conn.commit()
    close_db(conn)


def set_lts_access(telegram_id: int, payment_method: str, payment_date: str, payment_expiry: str, payment_total_amt: float) -> None:
    conn = connect_db()
    cursor_obj = conn.cursor()
    cursor_obj.execute('UPDATE members SET payment_method = ?, last_payment_date = ?, access_until = ?, donator_type = ?, total_donations = ? WHERE telegram_id = ?',
                       (payment_method, payment_date, payment_expiry, 'LTS', str(payment_total_amt), telegram_id, ))
    conn.commit()
    close_db(conn)


def get_invites(telegram_id: int) -> Union[int, None]:
    conn = connect_db()
    cursor_obj = conn.cursor()
    data: tuple = cursor_obj.execute(
        'SELECT invites_avail FROM members WHERE telegram_id = ?', (telegram_id,)).fetchone()
    close_db(conn)
    if data[0] is not None:
        return data[0]
    return None


def set_invites(telegram_id: int, invites: int) -> None:
    conn = connect_db()
    cursor_obj = conn.cursor()
    cursor_obj.execute(
        '''UPDATE members SET invites_avail = ? WHERE telegram_id = ?''', (invites, telegram_id,))
    conn.commit()
    close_db(conn)


def write_invite(telegram_id: int, full_name: str, inv_code: str) -> None:
    conn = connect_db()
    cursor_obj = conn.cursor()
    cursor_obj.execute('''INSERT INTO invites VALUES (?,?,?)''',
                       (telegram_id, full_name, inv_code))
    conn.commit()
    close_db(conn)


def del_invite(inv_code: str, invalidate: bool = False, telegram_id: Union[None, int] = None) -> None:
    conn = connect_db()
    cursor_obj = conn.cursor()
    cursor_obj.execute(
        '''DELETE FROM invites WHERE invite_code = ?''', (inv_code,))
    conn.commit()
    if invalidate:
        if not is_staff(telegram_id=telegram_id):
            donator_invites = get_invites(telegram_id)
            donator_invites += 1
            set_invites(telegram_id, donator_invites)
    close_db(conn)


def fetch_invite(telegram_id: int) -> Union[str, bool]:
    conn = connect_db()
    cursor_obj = conn.cursor()
    d = cursor_obj.execute(
        '''SELECT invite_code FROM invites WHERE user_id = ?''', (telegram_id,)).fetchone()
    close_db(conn)
    if d is not None:
        return d[0]
    return False


def get_invite_details(inv_code: str) -> Union[tuple, None]:
    conn = connect_db()
    cursor_obj = conn.cursor()
    d = cursor_obj.execute(
        '''SELECT * FROM invites WHERE invite_code = ?''', (inv_code,)).fetchone()
    close_db(conn)
    return d


def set_invite_action(telegram_id: int, action: str) -> None:
    conn = connect_db()
    cursor_obj = conn.cursor()
    cursor_obj.execute(
        '''INSERT INTO invite_funcs VALUES (?,?)''', (telegram_id, action))
    conn.commit()
    conn.close()


def get_invite_action(telegram_id: int) -> Union[tuple, None]:
    conn = connect_db()
    cursor_obj = conn.cursor()
    d = cursor_obj.execute(
        '''SELECT * FROM invite_funcs WHERE user_id = ?''', (telegram_id,)).fetchone()
    conn.close()
    return d


def del_invite_action(telegram_id: Union[int, None] = None, action: Union[str, None] = None) -> Union[None, int]:
    conn = connect_db()
    cursor_obj = conn.cursor()
    data = None
    if action is None:
        cursor_obj.execute(
            '''DELETE FROM invite_funcs WHERE user_id = ?''', (telegram_id,))
    elif action == 'all':
        d = cursor_obj.execute('''SELECT * FROM invite_funcs;''').fetchall()
        data = len(d)
        cursor_obj.execute('''DELETE FROM invite_funcs;''')
    conn.commit()
    conn.close()
    return data


def get_drive_details_from_id(drive_id: str) -> str:
    conn = connect_db()
    cursor_obj = conn.cursor()
    data = cursor_obj.execute(
        '''SELECT * FROM drives_data_tracker WHERE drive_id = ?''', (drive_id,)).fetchone()
    conn.close()
    return data


def delete_drive(drive_id: str) -> None:
    conn = connect_db()
    cursor_obj = conn.cursor()
    cursor_obj.execute(
        '''DELETE FROM drives_data_tracker WHERE drive_id = ?''', (drive_id,))
    conn.commit()
    conn.close()


def add_drive(drive_id: str, drive_name: str, drive_type: str) -> None:
    conn = connect_db()
    cursor_obj = conn.cursor()
    cursor_obj.execute('''INSERT INTO drives_data_tracker(drive_id, drive_name, drive_type) VALUES (?, ?, ?)''',
                       (drive_id, drive_name, drive_type))
    conn.commit()
    conn.close()


def edit_drive(drive_id: str, drive_name: str = None, drive_type: str = None) -> None:
    conn = connect_db()
    cursor_obj = conn.cursor()
    if drive_name is not None:
        cursor_obj.execute(
            '''UPDATE drives_data_tracker SET drive_name = ? WHERE drive_id = ?''', (drive_name, drive_id))
        conn.commit()
        conn.close()
    if drive_type is not None:
        cursor_obj.execute(
            '''UPDATE drives_data_tracker SET drive_type = ? WHERE drive_id = ?''', (drive_type, drive_id))
        conn.commit()
        conn.close()
