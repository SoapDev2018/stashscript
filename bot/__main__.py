import html
import math
import os
import re
from datetime import datetime

from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, ParseMode,
                      Update)
from telegram.error import BadRequest
from telegram.ext import (CallbackContext, CallbackQueryHandler,
                          CommandHandler, MessageHandler)
from telegram.ext.filters import Filters
from telegram.utils.helpers import mention_html

from bot import (AUTH_CHATS, DB_FILENAME, DONATORS_GROUP_ID, IV_GROUP_ID,
                 STREAK_DB_FILENAME, TRANSACTIONS_DB_FILENAME, dispatcher,
                 updater)
from bot.helpers import generic_ops, google_drive_ops, tg_ops

from .admin import donator
from .helpers import db_ops, streak_db_ops, trans_db_ops
from .modules import invite, stats, updates
from .modules.invite import bl_invite, unbl_invite
from .modules.profile import profile, profile_btn
from .modules.store import send, send_btn, cancel_trans, get_pending_trans
from .modules.streaks import get_xp, leaderboards, reset_daily_xp
from .admin.dbwork import dbdump
from .admin.drive import drv_conv_handler


def start(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user

    if chat.type == 'private':
        if len(context.args) > 0 and context.args[0].startswith('inv_'):
            inv_code = context.args[0].split('_')[1]
            ic_details = db_ops.get_invite_details(inv_code)
            if ic_details is None:
                context.bot.send_message(
                    chat.id, '<b>Invalid invite code</b> 😒', parse_mode=ParseMode.HTML, reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
                return
            else:
                ic_details_user_id = ic_details[0]
                if ic_details_user_id == user.id:
                    context.bot.send_message(chat.id, 'You aren\'t supposed to click this link\n<b>Send the link to your invitee!</b>',
                                             parse_mode=ParseMode.HTML, reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
                    return
                else:
                    if db_ops.is_donator(user.id):
                        context.bot.send_message(
                            chat.id, f'You are already a donator {html.escape(user.full_name)}, this URL is not meant for you!', reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
                        return
                    else:
                        inv_data = db_ops.get_invite_action(chat.id)
                        if inv_data is None:
                            try:
                                iv_group_rqst_link = context.bot_data['iv_group_rqst_link']
                            except KeyError:
                                iv_group_rqst_link = context.bot.create_chat_invite_link(
                                    IV_GROUP_ID, creates_join_request=True).invite_link
                                context.bot_data['iv_group_rqst_link'] = iv_group_rqst_link
                            _msg = f'You have been invited to join {iv_group_rqst_link}\n\nAfter you send a join request <b>and your inviter confirms your invite</b>, you\'ll be able to join the interview group.\n\nWe\'ll hold a short interview <u>and only then</u> shall we accept any donation for joining.'
                            m = context.bot.send_message(chat.id, _msg, parse_mode=ParseMode.HTML,
                                                         reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
                            context.user_data['m_ic'] = m
                            context.user_data['ic_user_id'] = ic_details_user_id
                        else:
                            if inv_data[1] == 'Received':
                                context.bot.send_message(chat.id, 'You have <b>already received</b> an invite',
                                                         parse_mode=ParseMode.HTML, reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
                                db_ops.del_invite(
                                    inv_code=inv_code, invalidate=True, telegram_id=ic_details_user_id)
                                _msg = f'The person you invited, {mention_html(user.id, user.full_name)} had already received an invited.\nWe have <b>revoked</b> your invite code'
                                if not db_ops.is_staff(ic_details_user_id):
                                    _msg += ' and 1 invite token has been refunded back to you!'
                                context.bot.send_message(
                                    ic_details_user_id, _msg, parse_mode=ParseMode.HTML)
                            elif inv_data[1] == 'Blacklisted':
                                context.bot.send_message(chat.id, 'You have been <b>blacklisted</b> from receiving an invite!',
                                                         parse_mode=ParseMode.HTML, reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
                                db_ops.del_invite(
                                    inv_code=inv_code, invalidate=True, telegram_id=ic_details_user_id)
                                _msg = f'The person you invited, {mention_html(user.id, user.full_name)} was blacklisted from receiving an invite.\nWe have <b>revoked</b> your invite code'
                                if not db_ops.is_staff(ic_details_user_id):
                                    _msg += ' and 1 invite token has been refunded back to you!'
                                context.bot.send_message(
                                    ic_details_user_id, _msg, parse_mode=ParseMode.HTML)
                            elif inv_data[1] == 'Denied':
                                context.bot.send_message(chat.id, 'We have decided <b>not to move further</b> with your donation request and you won\'t be able to receive an invite further!',
                                                         parse_mode=ParseMode.HTML, reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
                                db_ops.del_invite(
                                    inv_code=inv_code, invalidate=True, telegram_id=ic_details_user_id)
                                _msg = f'We have denied donation request from {mention_html(user.id, user.full_name)}.\nWe have <b>revoked</b> your invite code'
                                if not db_ops.is_staff(ic_details_user_id):
                                    _msg += ' and 1 invite token has been refunded back to you!'
                                context.bot.send_message(
                                    ic_details_user_id, _msg, parse_mode=ParseMode.HTML)
        else:
            if db_ops.is_donator(chat.id):
                if context.bot.get_chat_member(DONATORS_GROUP_ID, chat.id)['status'] == 'left':
                    group_link = context.bot.create_chat_invite_link(
                        chat_id=DONATORS_GROUP_ID, member_limit=1)['invite_link']
                    context.user_data['invite_link'] = group_link
                    inline_kboard = [
                        [
                            InlineKeyboardButton(
                                'Check ✅', callback_data='start_check')
                        ],
                    ]
                    context.bot.send_message(chat.id, f'Hello {chat.full_name}, thank you for becoming a new donator!\nPlease click on the following link and join the group to access the donator\'s specific group:\n{group_link}\nPlease be advised, this link is valid for one person only!\n\nPlease press /help to get a list of all available commands!',
                                             reply_markup=InlineKeyboardMarkup(inline_kboard), reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
                else:
                    context.bot.send_message(
                        chat.id, f'Hello {chat.full_name}\nTo get a list of all available commands, press /help', reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
            else:
                context.bot.send_message(
                    chat.id, f'Hello {chat.full_name}, you can only use /price and /invite\nYou currently are not a donator!', reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
    elif tg_ops.check_chat(update, context):
        # if len(context.args) > 0 and context.args[0].startswith('inv_'):
        #     context.bot.send_message(chat.id, f'Hello {msg.from_user.full_name}, this link cannot be used in a public group. We\'ve invalidated this invite code, please obtain another from your invitee',
        #                              reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
        context.bot.send_message(
            chat.id, f'Hello {msg.from_user.full_name}, welcome to {chat.title}!\nTo get a list of all available commands, press /help', reply_to_message_id=msg.message_id, allow_sending_without_reply=True)


def start_invite_btn(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    user = query.from_user
    query.answer()
    callback_data = query.data.split('_')[1]
    callback_data_user_id = query.data.split('_')[2]

    if callback_data == 'no':
        inv_code = db_ops.fetch_invite(user.id)
        db_ops.del_invite(inv_code=inv_code, invalidate=True,
                          telegram_id=user.id)
        _msg = 'Alright, we have invalidated that invite code.\nPlease re-generate your invite from /invite'
        if not db_ops.is_staff(user.id):
            _msg += '\nYou have been refunded one invite token.'
        query.edit_message_text(_msg)
        context.bot.decline_chat_join_request(
            IV_GROUP_ID, callback_data_user_id)
        context.bot.send_message(
            callback_data_user_id, 'Your inviter has <b>declined</b> that they didn\'t invite you', parse_mode=ParseMode.HTML)
    elif callback_data == 'yes':
        inv_code = db_ops.fetch_invite(user.id)
        db_ops.del_invite(inv_code=inv_code)
        query.edit_message_text('Thank you for confirming your invite!')
        context.bot.approve_chat_join_request(
            IV_GROUP_ID, callback_data_user_id)
        context.bot.send_message(
            callback_data_user_id, 'Your inviter has <b>confirmed</b> that they did invite you.\nYour chat join request has been accepted!', parse_mode=ParseMode.HTML)


def start_callback_btn(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    chat = update.effective_chat
    query.answer()
    callback_data = query.data

    if callback_data == 'start_check':
        group_link = context.user_data['invite_link']
        member_status = context.bot.get_chat_member(
            DONATORS_GROUP_ID, chat.id)['status']
        if member_status == 'left':
            inline_kboard = [
                [
                    InlineKeyboardButton(
                        'Check ✅', callback_data='start_check')
                ],
            ]
            try:
                query.edit_message_text(
                    f'{chat.full_name}, you have not joined the group yet!\nPlease join using the following link:\n{group_link}\nAfter joining, please press the below button', reply_markup=InlineKeyboardMarkup(inline_kboard))
            except BadRequest as e:
                print(e)
        else:
            context.bot.revoke_chat_invite_link(DONATORS_GROUP_ID, group_link)
            query.edit_message_text(
                f'{chat.full_name}, thank you for joining our group!\n\nPlease press /help to get a list of all available commands!')


def bot_help(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    msg = update.effective_message

    help_string = "<b>User Commands:</b>\n/help: To get this message\n/stats: To get information about donation & drive status\n/status: To get information about your donation status (works only in private)\n/price: Current BAT/USDT conversion price and INR/USD conversion price\n/paypal amt: Get the amount you would need to send for us to receive your intented amount\n/drives: Drives you have accessible based on your donation level"

    if db_ops.is_donator(chat.id) or tg_ops.check_chat(update, context):
        if db_ops.is_staff(chat.id):
            help_string += '\n\n<b>Additional Staff Commands:</b>\n/admin: To see staff functionality'
        context.bot.send_message(chat.id, help_string,
                                 reply_to_message_id=msg.message_id, allow_sending_without_reply=True, parse_mode=ParseMode.HTML)
    else:
        if chat.type == 'private':
            context.bot.send_message(
                chat.id, f'Hello {chat.full_name}, you are not authorized to use this command!', reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
        else:
            context.bot.leave_chat(chat.id)


def status(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    msg = update.effective_message

    if tg_ops.check_chat(update, context):
        context.bot.send_message(
            chat.id, 'This command cannot be used in group/supergroup. Please DM me for details!', reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
    elif chat.type == 'private':
        if not db_ops.is_donator(chat.id):
            user_details = streak_db_ops.get_details(chat.id)
            if user_details is None:
                update.message.reply_text(
                    '<b>No data found!</b>', reply_to_message_id=msg.message_id, allow_sending_without_reply=True, parse_mode=ParseMode.HTML)
            else:
                update.message.reply_text(
                    f'<b>You\'re not a donator!</b>\n\n<b>════「 Streak Details: 」════</b>\n<b>•XP:</b> {user_details[1]}\n<b>•Streak:</b> {user_details[2]} Days\n<b>•User Level:</b> Level {user_details[6]}\n<b>•Points:</b> {user_details[3]}\n<b>•Daily XP:</b> {user_details[4]}', reply_to_message_id=msg.message_id, allow_sending_without_reply=True, parse_mode=ParseMode.HTML)
        else:
            donator_details = db_ops.get_donator_details(chat.id)
            donator_email = donator_details[2]
            donator_payment_method = donator_details[3]
            donator_last_payment_date = donator_details[4]
            donator_access_until = donator_details[5]
            donator_type = donator_details[6]
            donator_total_amount = donator_details[7]
            donator_last_email_change_date = donator_details[9]
            donator_invites = donator_details[12]
            donator_has_hw_access = db_ops.get_nsfw_access(
                chat.id) or db_ops.is_staff(chat.id)
            donator_has_curator_access = db_ops.get_curator_access(
                chat.id) or db_ops.is_staff(chat.id)
            donator_streak_details = streak_db_ops.get_details(chat.id)
            if donator_type == 'Normal':
                donator_type_text = 'Normal Donator'
            elif donator_type == 'LTS':
                donator_type_text = 'Long Term Support Donator'
            else:
                donator_type_text = 'Staff'
            text = f'<b>════「 Donator Status: 」════</b>\n<b>•Email:</b> {donator_email}\n<b>•Payment Method:</b> {donator_payment_method}\n<b>•Last Payment Date:</b> {donator_last_payment_date}\n<b>•Total Donated:</b> {donator_total_amount}$\n<b>•Access Until:</b> {donator_access_until}\n<b>•Member Type:</b> {donator_type_text}'
            if donator_invites == -1:
                text += '\n<b>•Invites Available:</b> Unlimited'
            else:
                text += f'\n<b>•Invites Available:</b> {str(donator_invites)}'
            if donator_last_email_change_date is not None:
                text += f'\n<b>•Last Email Change Date:</b> {donator_last_email_change_date}'
            if donator_has_hw_access:
                text += '\n<b>•NSFW 🔞 Access:</b> Yes'
            if donator_has_curator_access:
                text += '\n<b>•Curator ✏️ Access:</b> Yes'
            if donator_streak_details is not None:
                text += f'\n\n<b>════「 Streak Details: 」════</b>\n<b>•XP:</b> {donator_streak_details[1]}\n<b>•Streak:</b> {donator_streak_details[2]} Days\n<b>•User Level:</b> Level {donator_streak_details[6]}\n<b>•Points:</b> {donator_streak_details[3]}\n<b>•Daily XP:</b> {donator_streak_details[4]}'
            inline_kboard = [
                [
                    InlineKeyboardButton(
                        'Change My Email 📧', callback_data=f'chan_em_{chat.id}')
                ],
                [
                    InlineKeyboardButton(
                        'View Transactions 📈', callback_data='view_trans')
                ]
            ]
            context.bot.send_message(chat.id, text,
                                     parse_mode=ParseMode.HTML, reply_to_message_id=msg.message_id, allow_sending_without_reply=True, reply_markup=InlineKeyboardMarkup(inline_kboard))


def status_trans_callback_btn(update: Update, _: CallbackContext) -> None:
    query = update.callback_query
    user = query.from_user
    query.answer('Request received')
    _msg = ""
    sent_transactions = trans_db_ops.get_initiated_transactions(user.id)
    if len(sent_transactions) > 0:
        _msg = '<b>5 Latest transactions initated by you:</b>\n\n'
        for t in sent_transactions:
            _msg += f'<b>To:</b> <code>{t[2]}</code>\n<b>Amount:</b> <code>{t[3]}</code>\n<b>Timestamp:</b> {datetime.fromtimestamp(int(t[5]) / 1000000).strftime("%m/%d/%Y, %H:%M:%S")}\n\n'

    received_transactions = trans_db_ops.get_received_transactions(user.id)
    if len(received_transactions) > 0:
        _msg = '\n<b>5 Latest transactions where you received points:</b>\n\n'
        for t in received_transactions:
            _msg += f'<b>From:</b> <code>{t[1]}</code>\n<b>Amount:</b> <code>{t[3]}</code>\n<b>Timestamp:</b> {datetime.fromtimestamp(int(t[5]) / 1000000).strftime("%m/%d/%Y, %H:%M:%S")}\n\n'

    if len(_msg) > 0:
        query.edit_message_text(_msg, parse_mode=ParseMode.HTML)
        return
    query.edit_message_text(
        '<b>No transactions found!</b>', parse_mode=ParseMode.HTML)


def status_callback_btn(update: Update, _: CallbackContext) -> None:
    query = update.callback_query
    chat = update.effective_chat
    callback_data = query.data
    cb_donator_id = re.search(r'\d+', callback_data).group()
    if int(cb_donator_id) != int(chat.id):
        query.answer(f'{chat.full_name} this is not for you!')
        return
    query.answer(
        'Request has been received, please do not press button again!')
    don_last_email_change_date = db_ops.get_donator_details(chat.id)[9]
    if don_last_email_change_date is not None:
        get_today_date = db_ops.get_today_date()
        get_today_date_obj = datetime.strptime(get_today_date, '%Y-%m-%d')
        don_last_email_change_date_obj = datetime.strptime(
            don_last_email_change_date, '%Y-%m-%d')
        if (get_today_date_obj - don_last_email_change_date_obj).days < 90:
            try:
                query.edit_message_text(
                    f'A cooldown period of 90 days is present between changing emails\nYour last email change date was: {don_last_email_change_date}')
                return
            except BadRequest as e:
                print(e)
    try:
        query.edit_message_text('Please send your new email')
    except BadRequest as e:
        print(e)


def status_email_chg_msg_handler(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    msg = update.message
    new_donator_email = msg.text
    context.user_data['new_donator_email'] = new_donator_email
    inline_kboard = [
        [
            InlineKeyboardButton(
                'Yes ✅', callback_data=f'change_email_yes_{chat.id}'),
            InlineKeyboardButton(
                'No ❌', callback_data=f'change_email_no_{chat.id}'),
        ]
    ]
    context.bot.send_message(
        chat.id, f'Received new email ID: {new_donator_email}\nAre you sure you want to update?', reply_markup=InlineKeyboardMarkup(inline_kboard))


def email_chg_btn(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    query = update.callback_query
    callback_data = query.data
    cb_donator_id = re.search(r'\d+', callback_data).group()
    if int(cb_donator_id) != int(chat.id):
        query.answer(f'{chat.full_name} this is not for you!')
        return
    query.answer(
        'Request has been received, please do not press button again!')
    change_opt = callback_data.split('_')[2]
    if change_opt == 'no':
        query.edit_message_text('Not changing email!')
        return
    donator_details = db_ops.get_donator_details(chat.id)
    donator_old_email = donator_details[2]
    db_ops.change_email(chat.id, context.user_data['new_donator_email'])
    donator_type = donator_details[6]
    donator_has_hw_access = donator_details[10]
    donator_has_curator_access = donator_details[11]
    context.bot.send_chat_action(chat.id, 'typing')
    return_msgs = google_drive_ops.change_donator_email(
        donator_old_email, context.user_data['new_donator_email'], donator_type, donator_has_hw_access, donator_has_curator_access)
    _log = f'User <code>{chat.id}</code> changed email from {donator_old_email} to {context.user_data["new_donator_email"]}'
    tg_ops.post_log(update, context, _log)
    if len(return_msgs) > 0:
        query.edit_message_text('Issues occurred ⚠️: \n')
    flag = False
    for msg in return_msgs:
        flag = True
        msg_txt = f'{msg}\n'
    if flag:
        context.bot.send_message(chat.id, msg_txt)
        return
    query.edit_message_text('Successfully changed email! ✅')


def drives(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    msg = update.effective_message

    if tg_ops.check_chat(update, context):
        context.bot.send_message(
            chat.id, 'This command cannot be used in group/supergroup. Please DM me for details!', reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
    elif chat.type == 'private':
        if not db_ops.is_donator(chat.id):
            context.bot.send_message(chat.id, f'Hello {chat.full_name}, you are not authorized to use this command!',
                                     reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
        else:
            donator_drive_details = db_ops.get_drive_details(chat.id)
            donator_drive_text = '<b>════「 Drive Details: 」════</b>\n\n<u>Drives displayed here are based on donator access level</u>\n\n'
            for row in donator_drive_details:
                drive_url = f'https://drive.google.com/drive/folders/{row[0]}'
                drive_name = row[1]
                donator_drive_text += f'<b>•</b><a href=\'{drive_url}\'>{drive_name}</a>\n'
            donator_drive_text = donator_drive_text.strip()
            context.bot.send_message(chat.id, donator_drive_text, parse_mode=ParseMode.HTML,
                                     reply_to_message_id=msg.message_id, allow_sending_without_reply=True)


def prices(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    msg = update.effective_message

    coin_tickers = db_ops.get_price_rates()
    bat_price = coin_tickers[0]
    inr_usd_rate = coin_tickers[1]
    usdt_usd_rate = coin_tickers[2]
    bat_to_send = int(math.ceil(3/float(bat_price)))
    bat_to_send_lts = int(math.ceil(10/float(bat_price)))

    if chat.type == 'group' or chat.type == 'supergroup' or chat.type == 'channel':
        if not chat.id in generic_ops.get_auth_chat():
            context.bot.leave_chat(chat.id)
            return
    message_text = f'<b>════「 Price Details: 」════</b>\n\n<b>•BAT/USD Rate:</b> {bat_price}\n<b>•INR/USD Rate:</b> {inr_usd_rate}\n<b>•USDT/USD Rate:</b> {usdt_usd_rate}\n\n<b>For normal donator, you need to send {bat_to_send} BAT\nFor LTS donator, you need to send {bat_to_send_lts} BAT</b>'
    context.bot.send_message(chat.id, message_text, parse_mode=ParseMode.HTML,
                             reply_to_message_id=msg.message_id, allow_sending_without_reply=True)


def main():
    start_handler = CommandHandler('start', start, run_async=True)
    help_handler = CommandHandler('help', bot_help, run_async=True)
    status_handler = CommandHandler(['status', 'my'], status, run_async=True)
    drives_handler = CommandHandler('drives', drives, run_async=True)
    prices_handler = CommandHandler('price', prices, run_async=True)

    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(status_handler)
    dispatcher.add_handler(drives_handler)
    dispatcher.add_handler(prices_handler)
    dispatcher.add_handler(CallbackQueryHandler(
        start_callback_btn, pattern='start_.*'))
    dispatcher.add_handler(CallbackQueryHandler(
        status_callback_btn, pattern=r'chan_em_\d+'))
    dispatcher.add_handler(CallbackQueryHandler(
        email_chg_btn, pattern=r'change_email_\w{2,3}_\d+'))
    # Fixes the bug where this MessageHandler was being called in groups
    dispatcher.add_handler(MessageHandler(
        Filters.regex(r'[a-z0-9]+@[a-z]+\.[a-z]{2,3}') & Filters.chat_type.private, status_email_chg_msg_handler))
    dispatcher.add_handler(CallbackQueryHandler(
        start_invite_btn, pattern=r'cnf_[ny][eo]s?_\d+'))
    if not os.path.exists(DB_FILENAME):
        db_ops.seed_db()
    if not os.path.exists(STREAK_DB_FILENAME):
        streak_db_ops.seed_db()
    if not os.path.exists(TRANSACTIONS_DB_FILENAME):
        trans_db_ops.seed_db()

    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command & Filters.chat(
        AUTH_CHATS) & ~Filters.forwarded & ~Filters.update.edited_message, get_xp))
    dispatcher.add_handler(CommandHandler(
        'leaderboard', leaderboards, filters=Filters.chat(AUTH_CHATS)))
    dispatcher.add_handler(CommandHandler(
        ['blacklist', 'deny'], bl_invite, filters=Filters.chat(generic_ops.get_auth_chat())))
    dispatcher.add_handler(CommandHandler(
        'unblacklist', unbl_invite, filters=Filters.chat(generic_ops.get_auth_chat())))
    dispatcher.add_handler(CommandHandler(
        'profile', profile, filters=Filters.chat_type.private))
    dispatcher.add_handler(CallbackQueryHandler(
        profile_btn, pattern=r'user\_[mp][a-z]{3,6}\_[op][a-z]{1,2}'))
    dispatcher.add_handler(CommandHandler(
        'send', send, filters=Filters.chat(AUTH_CHATS) | Filters.chat_type.private))
    dispatcher.add_handler(CallbackQueryHandler(
        send_btn, pattern=r'tr_[ny][eo]s?_[A-Fa-f0-9]{56}'))
    dispatcher.add_handler(CommandHandler(
        'ctrans', cancel_trans, filters=Filters.chat_type.private))
    dispatcher.add_handler(CommandHandler(
        'pending', get_pending_trans, filters=Filters.chat_type.private))
    dispatcher.add_handler(CallbackQueryHandler(
        status_trans_callback_btn, pattern=r'view_trans'))
    dispatcher.add_handler(CommandHandler('dump', dbdump, filters=Filters.chat(
        generic_ops.get_auth_chat()) | Filters.chat_type.private))
    dispatcher.add_handler(drv_conv_handler)
    j = dispatcher.job_queue
    j.run_repeating(reset_daily_xp, interval=300, first=6)

    updater.start_polling(drop_pending_updates=True)
    print('Bot Started!')
    updater.idle()


main()
