from datetime import datetime
from typing import Tuple

import pytz
from bot.helpers import streak_db_ops
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackContext


def button_builder(user_details: Tuple) -> list:
    user_mentions = user_details[-2]
    user_profile_type = user_details[-1]
    inline_kboard = []
    l = list()
    if user_mentions == 'Off':
        us_mention_cb = 'user_mention_on'
        us_mention_txt = 'Mentions: Off'
    elif user_mentions == 'On':
        us_mention_cb = 'user_mention_off'
        us_mention_txt = 'Mentions: On'
    l.append(InlineKeyboardButton(us_mention_txt, callback_data=us_mention_cb))

    if user_profile_type == 'Public':
        usr_profile_cb = 'user_prof_pvt'
        usr_profile_txt = 'Profile: Public'
    elif user_profile_type == 'Private':
        usr_profile_cb = 'user_prof_pub'
        usr_profile_txt = 'Profile: Private'
    l.append(InlineKeyboardButton(
        usr_profile_txt, callback_data=usr_profile_cb))
    inline_kboard.append(l)
    return inline_kboard


def profile(update: Update, _: CallbackContext) -> None:
    msg = update.effective_message
    user = update.effective_user

    user_details = streak_db_ops.get_details(user.id)
    if user_details is None:
        t = datetime.date(datetime.now().astimezone(
            pytz.timezone('Asia/Kolkata')))
        streak_db_ops.create_user(
            user.id, t.strftime('%m/%d/%Y'), user.full_name)
        user_details = streak_db_ops.get_details(user.id)
    _msg = "Your profile options are listed below.\nTap on the buttons to change them:"
    buttons = button_builder(user_details)
    update.message.reply_text(_msg, reply_markup=InlineKeyboardMarkup(
        buttons), reply_to_message_id=msg.message_id, allow_sending_without_reply=True)


def profile_btn(update: Update, _: CallbackContext) -> None:
    query = update.callback_query
    user = update.callback_query.from_user
    query.answer('Your request has been received!')
    data = query.data
    user_details = streak_db_ops.get_details(user.id)
    cb_type = data.split('_')[1]
    if cb_type == 'mention':
        mention_type = data.split('_')[2]
        if mention_type == 'on':
            streak_db_ops.set_mention(user.id, 'On')
        elif mention_type == 'off':
            streak_db_ops.set_mention(user.id, 'Off')
        user_details = streak_db_ops.get_details(user.id)
        button = button_builder(user_details)
        query.edit_message_text(
            "Your profile options are listed below.\nTap on the buttons to change them:", reply_markup=InlineKeyboardMarkup(button))
    elif cb_type == 'prof':
        profile_type = data.split('_')[2]
        if profile_type == 'pvt':
            streak_db_ops.set_profile_type(user.id, 'Private')
        elif profile_type == 'pub':
            streak_db_ops.set_profile_type(user.id, 'Public')
        user_details = streak_db_ops.get_details(user.id)
        button = button_builder(user_details)
        query.edit_message_text(
            "Your profile options are listed below.\nTap on the buttons to change them:", reply_markup=InlineKeyboardMarkup(button))
