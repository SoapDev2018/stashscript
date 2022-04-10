from typing import Tuple

from bot import dispatcher
from bot.helpers import db_ops, tg_ops
from telegram import ParseMode, Update
from telegram.ext import CommandHandler
from telegram.ext.callbackcontext import CallbackContext


def get_personal_stats(telegram_id: int, drive_stats_details: list) -> Tuple[list, list]:
    personal_normal_drive_stats = list()
    personal_lts_drive_stats = list()
    drive_details = db_ops.get_drive_details(telegram_id)
    for global_drive in drive_stats_details:
        global_drive_id = global_drive[3]
        for drive in drive_details:
            if global_drive_id == drive[0]:
                flag = True
                break
        else:
            flag = False
        personal_drive_dict = {
            'drive_name': global_drive[0],
            'drive_size': global_drive[2],
            'drive_type': global_drive[1],
        }
        if flag == True:
            personal_drive_dict['drive_access'] = True
        else:
            personal_drive_dict['drive_access'] = False
        if personal_drive_dict['drive_type'] == 'Normal':
            personal_normal_drive_stats.append(personal_drive_dict)
        elif personal_drive_dict['drive_type'] == 'LTS':
            personal_lts_drive_stats.append(personal_drive_dict)
    return personal_normal_drive_stats, personal_lts_drive_stats


def is_donator_pvt_stats_text(telegram_id: int, drive_stats_details: list) -> str:
    personal_normal_drive_stats, personal_lts_drive_stats = get_personal_stats(
        telegram_id, drive_stats_details)
    drive_stats_text = '<b>════「 Drive Status: 」════</b>\n'
    for drive in personal_normal_drive_stats:
        drive_stats_text += f'<b>•Drive Name:</b> {drive["drive_name"]}\n<b>•Drive Size:</b> {drive["drive_size"]}\n<b>•Drive Type:</b> {drive["drive_type"]}\n<b>•Drive Access:</b> {drive["drive_access"]}\n━━━━━━━━━▼━━━━━━━━━\n'
    drive_stats_text += '\n<b>LTS Drives</b>\n\n'
    for drive in personal_lts_drive_stats:
        drive_stats_text += f'<b>•Drive Name:</b> {drive["drive_name"]}\n<b>•Drive Size:</b> {drive["drive_size"]}\n<b>•Drive Type:</b> {drive["drive_type"]}\n<b>•Drive Access:</b> {drive["drive_access"]}\n━━━━━━━━━▼━━━━━━━━━\n'
    drive_stats_text = drive_stats_text.strip()
    return drive_stats_text


def stats(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    msg = update.effective_message

    donation_status_details = db_ops.get_donation_details()
    donation_status_text = f'<b>════「 Donation Status: 」════</b>\n<b>•Total Donations Received:</b> {donation_status_details[0]}$\n<b>•Total Spent:</b> {donation_status_details[1]}$\n<b>•Balance Available:</b> {donation_status_details[2]}$'

    drive_stats_details = db_ops.get_global_drive_details()
    drive_stats_text = '<b>════「 Drive Status: 」════</b>\n'
    for row in drive_stats_details:
        drive_stats_text += f'<b>•Drive Name:</b> {row[0]}\n<b>•Drive Size:</b> {row[2]}\n<b>•Drive Type:</b> {row[1]}\n━━━━━━━━━▼━━━━━━━━━\n'
    drive_stats_text = drive_stats_text.strip()
    if chat.type == 'private':
        if db_ops.is_donator(chat.id):
            drive_stats_text = is_donator_pvt_stats_text(
                chat.id, drive_stats_details)
            context.bot.send_message(chat.id, f'Hi there, {chat.full_name}\n{donation_status_text}\n\n{drive_stats_text}',
                                     parse_mode=ParseMode.HTML, reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
            if db_ops.is_staff(chat.id):
                staff_cnt, lts_donator_cnt, normal_donator_cnt = db_ops.get_admin_donator_count()
                additional_staff_stats_text = f'<b>════「 Additional Staff Stats: 」════</b>\n\n<b>•Donator Count:</b> {lts_donator_cnt + normal_donator_cnt}\n<b> ➺LTS Donators:</b> {lts_donator_cnt}\n<b> ➺Normal Donators:</b> {normal_donator_cnt}\n<b>•Staff Count:</b> {staff_cnt}'
                context.bot.send_message(
                    chat.id, additional_staff_stats_text, parse_mode=ParseMode.HTML)
        else:
            context.bot.send_message(
                chat.id, f'Hi there, {chat.full_name}\nYou currently are not a donator!')
    elif tg_ops.check_chat(update, context):
        context.bot.send_message(chat.id, f'Hello {msg.from_user.full_name}, welcome to {chat.title}!\n{donation_status_text}\n\n{drive_stats_text}',
                                     parse_mode=ParseMode.HTML, reply_to_message_id=msg.message_id, allow_sending_without_reply=True)


stats_handler = CommandHandler('stats', stats, run_async=True)
dispatcher.add_handler(stats_handler)
