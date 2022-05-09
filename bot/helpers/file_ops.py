import os
from datetime import datetime
from typing import Union

import pytz
import xlsxwriter


def get_datetime() -> str:
    return datetime.now().astimezone(pytz.timezone('Asia/Kolkata')).strftime('%Y_%m_%d_%H_%M_%S')


type = {
    'main': ['Telegram ID', 'Donator Email', 'Payment Method', 'Last Payment Date', 'Access Until', 'Donator Type', 'Total Donations ($)', 'Admin Privileges', 'Last Email Change Date', 'Has HW Access', 'Has Curator Access', 'Invites Available'],
    'streak': ['Telegram ID', 'XP', 'Streak', 'Points', 'Daily XP Earned', 'Daily XP Granted', 'User Level', 'Last Chat Date', 'User Full Name', 'User Mentions', 'User Profile Type'],
}


def dump_to_file(data: list, dump_type: str) -> Union[str, None]:
    file_name = f'dbdump-{get_datetime()}.xlsx'
    workbook = xlsxwriter.Workbook(filename=file_name)
    worksheet = workbook.add_worksheet()
    bold = workbook.add_format({'bold': True})

    fields: list = type[dump_type]
    for i, j in enumerate(fields):
        worksheet.write(f'{chr(i + 65)}1', j, bold)

    row = 1
    for d in data:
        if dump_type == 'main':
            d = d[1:]
        for i, j in enumerate(d):
            if j is None:
                j = 'None'
            worksheet.write(row, i, j)
        row += 1

    workbook.close()
    if os.path.exists(file_name):
        return file_name
    return None
