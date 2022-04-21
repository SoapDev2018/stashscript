import re
from datetime import datetime

import pytz
from bot import dispatcher
from bot.helpers import db_ops, group_ops, streak_db_ops, tg_ops
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup,
                      ReplyKeyboardMarkup, ReplyKeyboardRemove, Update)
from telegram.ext import (CallbackContext, CallbackQueryHandler,
                          CommandHandler, ConversationHandler, Filters,
                          MessageHandler)
from telegram.parsemode import ParseMode
from telegram.utils.helpers import mention_html

ADMIN_OPTION, ADD_TELEGRAM_ID, ADD_EMAIL, ADD_PAYMENT_AMOUNT, ADD_PAYMENT_METHOD, MORE_OPTION, STAFF_OPTION, VIEW_DETAILS, REMOVE_DONATOR, APPOINT_ADMIN, DISMISS_ADMIN, DONATOR_FUNCTIONS, DONATOR_FUNC_CHOOSE, LTS_PAYMENT_AMT, LTS_PAYMENT_METHOD = range(
    15)


def form_staff_keyboard(reply_keyboard: list, telegram_id: int) -> list:
    staff_privileges = db_ops.get_staff_privileges(telegram_id)
    if 'add_staff' in staff_privileges or 'edit_staff' in staff_privileges:
        reply_keyboard.append('Staff Functions')
    return reply_keyboard


def admin(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    msg = update.effective_message

    if chat.type == 'private':
        if not db_ops.is_staff(chat.id):
            context.bot.send_message(chat.id, f'{chat.full_name}, you are not authorized to use this command!',
                                     reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
        else:
            reply_keyboard = [['Add a Donator', 'Update Donator Details']]
            reply_keyboard_extra = ['More...']
            reply_keyboard_extra = form_staff_keyboard(
                reply_keyboard_extra, chat.id)
            reply_keyboard.append(reply_keyboard_extra)
            context.bot.send_message(chat.id, 'Please select an option:', reply_markup=ReplyKeyboardMarkup(
                reply_keyboard, True, True), reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
            return ADMIN_OPTION
    else:
        if tg_ops.check_chat(update, context):
            if db_ops.is_staff(msg.from_user.id):
                context.bot.send_message(chat.id, f'{msg.from_user.full_name}, this command can only be used in bot DM!',
                                         reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
            else:
                context.bot.send_message(chat.id, f'{msg.from_user.full_name}, this is a staff only reserved command!',
                                         reply_to_message_id=msg.message_id, allow_sending_without_reply=True)


def form_more_keyboard(telegram_id: int) -> list:
    staff_privileges = db_ops.get_staff_privileges(telegram_id)
    reply_keyboard = ['View Donator Details']
    if 'remove_donator' in staff_privileges:
        reply_keyboard.append('Remove Donator')
    if 'edit_donator' in staff_privileges:
        reply_keyboard.append('Donator Functions')
    return reply_keyboard


def form_extra_staff_keyboard(telegram_id: int) -> list:
    staff_privileges = db_ops.get_staff_privileges(telegram_id)
    reply_keyboard = list()
    if 'add_staff' in staff_privileges:
        reply_keyboard.append('Appoint Admin')
    if 'edit_staff' in staff_privileges:
        reply_keyboard.append('Dismiss Admin')
    return reply_keyboard


def admin_option(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    msg = update.effective_message

    _option = update.message.text
    if _option == 'Add a Donator':
        staff_privileges = db_ops.get_staff_privileges(chat.id)
        if 'add_donator' not in staff_privileges:
            context.bot.send_message(chat.id, f'{chat.full_name}, you do not have the required privileges to add a donator',
                                     reply_markup=ReplyKeyboardRemove(), reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
        else:
            context.bot.send_message(chat.id, f'Okay, {chat.full_name}, I will need some details to add a new donator!\nPlease send Telegram ID of the user!',
                                     reply_markup=ReplyKeyboardRemove(), reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
            return ADD_TELEGRAM_ID
    elif _option == 'Update Donator Details':
        # TODO: Add logic to edit an already existing donators' details
        pass
    elif _option == 'More...':
        reply_keyboard = list()
        reply_keyboard.append(form_more_keyboard(chat.id))
        context.bot.send_message(chat.id, f'{chat.full_name}, please select one option', reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, True, True), reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
        return MORE_OPTION
    elif _option == 'Staff Functions':
        reply_keyboard = list()
        reply_keyboard.append(form_extra_staff_keyboard(chat.id))
        context.bot.send_message(chat.id, f'{chat.full_name}, please select one option', reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, True, True), reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
        return STAFF_OPTION


def more_options(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    msg = update.effective_message

    _option = update.message.text
    if _option == 'View Donator Details':
        context.bot.send_message(chat.id, 'Send me the Telegram ID for which you want to see donation details',
                                 reply_markup=ReplyKeyboardRemove(), reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
        return VIEW_DETAILS
    elif _option == 'Remove Donator':
        context.bot.send_message(chat.id, 'Send me the Telegram ID of the donator to remove', reply_markup=ReplyKeyboardRemove(
        ), reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
        return REMOVE_DONATOR
    elif _option == 'Donator Functions':
        context.bot.send_message(chat.id, 'Send me the Telegram ID to give LTS/NSFW access',
                                 reply_markup=ReplyKeyboardRemove(), reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
        return DONATOR_FUNCTIONS


def staff_options(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    msg = update.effective_message

    _option = update.message.text
    if _option == 'Appoint Admin':
        context.bot.send_message(chat.id, 'Send me Telegram ID which you want to appoint as staff. Please be aware, the member must already be a donator',
                                 reply_markup=ReplyKeyboardRemove(), reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
        return APPOINT_ADMIN
    elif _option == 'Dismiss Admin':
        context.bot.send_message(chat.id, 'Send me Telegram ID of staff to dismiss', reply_markup=ReplyKeyboardRemove(
        ), reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
        return DISMISS_ADMIN


def donator_functions(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    msg = update.effective_message

    try:
        telegram_id = int(update.message.text)
        donator_details = db_ops.get_donator_details(telegram_id)
        if donator_details[0] is not None:
            reply_kboard = [['Add to NSFW 🔞', 'Promote to LTS 📈']]
            context.bot.send_message(chat.id, f'{chat.full_name}\nPlease select an option for {mention_html(telegram_id, str(telegram_id))}', parse_mode=ParseMode.HTML, reply_markup=ReplyKeyboardMarkup(
                reply_kboard, True, True, reply_to_message_id=msg.message_id, allow_sending_without_reply=True))
            context.chat_data['donator_func_telegram_id'] = str(telegram_id)
            return DONATOR_FUNC_CHOOSE
    except ValueError as e:
        context.bot.send_message(chat.id, f'{update.message.text} is not a valid Telegram ID',
                                 reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
        return ConversationHandler.END


def donator_func_choose(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    msg = update.effective_message

    _option = update.message.text
    telegram_id = int(context.chat_data['donator_func_telegram_id'])
    if _option == 'Add to NSFW 🔞':
        donator_details = db_ops.get_donator_details(telegram_id)
        if donator_details[0] is not None:
            _donator_email = donator_details[2]
            _donator_payment_method = donator_details[3]
            _donator_last_payment_date = donator_details[4]
            _donator_access_until = donator_details[5]
            _donator_type = donator_details[6]
            _donator_total_donations = donator_details[7]
            inline_kboard = [
                [
                    InlineKeyboardButton(
                        'Yes ✅🔞', callback_data=f'donator_nsfw_yes_{str(telegram_id)}'),
                    InlineKeyboardButton(
                        'No ❌', callback_data=f'donator_nsfw_no_{str(telegram_id)}')
                ],
            ]
            context.bot.send_message(chat.id, f'<b>Here are the donator details:</b>\n<b>•Telegram ID:</b> {mention_html(telegram_id, str(telegram_id))}\n<b>•Donator Email:</b> {_donator_email}\n<b>•Payment Method:</b> {_donator_payment_method}\n<b>•Total Donations:</b> {_donator_total_donations}\n<b>•Last Donation:</b> {_donator_last_payment_date}\n<b>•Access Until:</b> {_donator_access_until}\n<b>•Donator Type:</b> {_donator_type}',
                                     parse_mode=ParseMode.HTML, reply_to_message_id=msg.message_id, allow_sending_without_reply=True, reply_markup=InlineKeyboardMarkup(inline_kboard))
        else:
            context.bot.send_message(chat.id, f'{chat.full_name}, <code>{telegram_id}</code> is not a valid donator\'s Telegram ID',
                                     parse_mode=ParseMode.HTML, reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
        return ConversationHandler.END
    elif _option == 'Promote to LTS 📈':
        context.bot.send_message(chat.id, f'{chat.full_name}, I will need some details to promote {mention_html(telegram_id, str(telegram_id))} to LTS.\nPlease send new donation amount (in USD)', parse_mode=ParseMode.HTML,
                                 reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
        return LTS_PAYMENT_AMT
    else:
        context.bot.send_message(chat.id, f'{chat.full_name} that is not a valid option!',
                                 reply_to_message_id=msg.message_id, allow_sending_without_reply=True)


def donator_nsfw_access_btn(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    query = update.callback_query
    callback_data = query.data
    cb_donator_id = re.search(r'\d+', callback_data).group()
    query.answer(
        'Request has been received, please do not press the button again!')
    don_email = db_ops.get_donator_details(int(cb_donator_id))[2]
    change_opt = callback_data.split('_')[2]
    if change_opt == 'no':
        query.edit_message_text('Not granting NSFW access!')
        return
    context.bot.send_chat_action(chat.id, 'typing')
    flag = db_ops.get_nsfw_access(
        cb_donator_id) or db_ops.is_staff(cb_donator_id)
    if flag:
        query.edit_message_text('Member already has NSFW access!')
        return
    db_ops.set_nsfw_access(int(cb_donator_id))
    add_nsfw_status = group_ops.set_nsfw_access(don_email)
    if add_nsfw_status != 'Success':
        query.edit_message_text(f'Issue occurred ⚠️: \n{add_nsfw_status}')
        return
    query.edit_message_text('Successfully given NSFW access to email! ✅🔞')


def lts_payment_amt(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    msg = update.effective_message

    lts_donation_amt = update.message.text
    context.chat_data['lts_donation_amt'] = lts_donation_amt
    context.bot.send_message(chat.id, f'Okay, {chat.full_name}, now send me payment method',
                             reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
    return LTS_PAYMENT_METHOD


def lts_payment_method(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    msg = update.effective_message

    lts_donation_method = update.message.text
    context.chat_data['lts_donation_method'] = lts_donation_method
    inline_kboard = [
        [
            InlineKeyboardButton(
                'Yes ✅📈', callback_data=f'donator_lts_yes_{str(context.chat_data["donator_func_telegram_id"])}'),
            InlineKeyboardButton(
                'No ❌', callback_data=f'donator_lts_no_{str(context.chat_data["donator_func_telegram_id"])}')
        ],
    ]
    context.bot.send_message(
        chat.id, f'{chat.full_name}, alright, got all info!\nDo you want to upgrade {mention_html(int(context.chat_data["donator_func_telegram_id"]), context.chat_data["donator_func_telegram_id"])} to LTS?', parse_mode=ParseMode.HTML, reply_to_message_id=msg.message_id, allow_sending_without_reply=True, reply_markup=InlineKeyboardMarkup(inline_kboard))
    return ConversationHandler.END


def donator_lts_access_btn(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    query = update.callback_query
    callback_data = query.data
    cb_donator_id = re.search(r'\d+', callback_data).group()
    query.answer(
        'Request has been received, please do not press the button again!')
    change_opt = callback_data.split('_')[2]
    if change_opt == 'no':
        query.edit_message_text('Not granting LTS access')
        return
    context.bot.send_chat_action(chat.id, 'typing')
    lts_donation_amt = context.chat_data['lts_donation_amt']
    lts_donation_method = context.chat_data['lts_donation_method']
    donator_details = db_ops.get_donator_details(cb_donator_id)
    if db_ops.is_staff(cb_donator_id) or donator_details[6] == 'LTS':
        query.edit_message_text(
            f'Telegram ID {mention_html(cb_donator_id, str(cb_donator_id))} is already staff or LTS member!')
        return
    new_donation_amt = round(
        float(donator_details[7]), 2) + round(float(lts_donation_amt), 2)
    if lts_donation_method != donator_details[3]:
        # Payment methods are not the same
        new_payment_method = f'{donator_details[3]}, {lts_donation_method}'
    else:
        new_payment_method = lts_donation_method
    new_payment_date = db_ops.get_today_date()
    new_payment_date_split = new_payment_date.split('-')
    new_payment_date_expiry_year = int(new_payment_date_split[0]) + 1
    new_payment_date_split[0] = str(new_payment_date_expiry_year)
    new_payment_date_expiry = "-".join(new_payment_date_split)
    db_ops.set_lts_access(cb_donator_id, new_payment_method,
                          new_payment_date, new_payment_date_expiry, new_donation_amt)
    db_ops.add_payment(round(float(lts_donation_amt), 2))
    add_lts_status = group_ops.set_lts_access(donator_details[2])
    if add_lts_status != 'Success':
        query.edit_message_text(f'Issue occurred ⚠️: \n{add_lts_status}')
        return
    query.edit_message_text('Successfully given LTS access to email! ✅📈')


def _view_details(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    msg = update.effective_message

    try:
        telegram_id = int(update.message.text)
        donator_details = db_ops.get_donator_details(telegram_id)
        if donator_details[0] is not None:
            _donator_email = donator_details[2]
            _donator_payment_method = donator_details[3]
            _donator_last_payment_date = donator_details[4]
            _donator_access_until = donator_details[5]
            _donator_type = donator_details[6]
            _donator_total_donations = donator_details[7]
            context.bot.send_message(chat.id, f'<b>Here are the donator details:</b>\n<b>•Telegram ID:</b> {mention_html(telegram_id, str(telegram_id))}\n<b>•Donator Email:</b> {_donator_email}\n<b>•Payment Method:</b> {_donator_payment_method}\n<b>•Total Donations:</b> {_donator_total_donations}\n<b>•Last Donation:</b> {_donator_last_payment_date}\n<b>•Access Until:</b> {_donator_access_until}\n<b>•Donator Type:</b> {_donator_type}',
                                     parse_mode=ParseMode.HTML, reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
        else:
            context.bot.send_message(chat.id, f'{chat.full_name}, <code>{telegram_id}</code> is not a valid donator\'s Telegram ID',
                                     parse_mode=ParseMode.HTML, reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
        return ConversationHandler.END
    except ValueError:
        context.bot.send_message(chat.id, f'{update.message.text} is not a valid Telegram ID',
                                 reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
        return ConversationHandler.END


def _remove_donator(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    msg = update.effective_message

    try:
        telegram_id = int(update.message.text)
        donator_details = db_ops.get_donator_details(telegram_id)
        if donator_details[0] is not None:
            _donator_email = donator_details[2]
            _donator_payment_method = donator_details[3]
            _donator_last_payment_date = donator_details[4]
            _donator_access_until = donator_details[5]
            _donator_type = donator_details[6]
            _donator_total_donations = donator_details[7]
            inline_kboard = [
                [
                    InlineKeyboardButton(
                        'Yes ✅', callback_data=f'dismiss_donator_yes_{str(telegram_id)}'),
                    InlineKeyboardButton(
                        'No ❌', callback_data='dismiss_donator_no')
                ],
            ]
            context.bot.send_message(chat.id, f'<b>Here are the donator details:</b>\n<b>•Telegram ID:</b> {mention_html(telegram_id, str(telegram_id))}\n<b>•Donator Email:</b> {_donator_email}\n<b>•Payment Method:</b> {_donator_payment_method}\n<b>•Total Donations:</b> {_donator_total_donations}\n<b>•Last Donation:</b> {_donator_last_payment_date}\n<b>•Access Until:</b> {_donator_access_until}\n<b>•Donator Type:</b> {_donator_type}\n\nAre you sure you want to dismiss this donator?',
                                     parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(inline_kboard), reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
        else:
            context.bot.send_message(chat.id, f'{chat.full_name}, <code>{telegram_id}</code> is not a valid donator\'s Telegram ID',
                                     parse_mode=ParseMode.HTML, reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
        return ConversationHandler.END
    except ValueError:
        context.bot.send_message(chat.id, f'{update.message.text} is not a valid Telegram ID',
                                 reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
        return ConversationHandler.END


def _remove_donator_btn(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    msg = update.effective_message
    query = update.callback_query
    query.answer()
    callback_data = query.data

    re_search = re.search(r'\d+', callback_data)
    if re_search:
        telegram_id = re_search.group()
        staff_privileges = db_ops.get_staff_privileges(chat.id)
        if db_ops.is_staff(telegram_id):
            if 'edit_staff' not in staff_privileges:
                query.edit_message_text(
                    'You are not allowed to dismiss a staff!')
            else:
                query.edit_message_text(
                    'Dismissing staff can be done from staff menu')
        else:
            donator_details = db_ops.get_donator_details(int(telegram_id))
            _donator_email = donator_details[2]
            _donator_type = donator_details[5]
            db_ops.remove_donator(telegram_id)
            flag = group_ops.remove_from_group(_donator_email, _donator_type)
            query.edit_message_text(
                f'Successfully removed donator <code>{str(telegram_id)}</code>', parse_mode=ParseMode.HTML)
            msg_obj = context.bot.send_message(chat.id, 'Trying to remove from googlegroup now...',
                                               reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
            if flag == 'Success':
                context.bot.edit_message_text(
                    'Successfully removed from googlegroup', chat_id=chat.id, message_id=msg_obj.message_id)
            else:
                context.bot.edit_message_text(
                    flag, chat_id=chat.id, message_id=msg_obj.message_id)
    elif callback_data == 'dismiss_donator_no':
        query.edit_message_text('Not dismissing donator!')


def telegram_id(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    msg = update.effective_message

    _telegram_id = update.message.text
    try:
        _telegram_id = int(_telegram_id)
        if db_ops.is_donator(_telegram_id):
            context.bot.send_message(chat.id, f'{chat.full_name}, {_telegram_id} is already a donator, exiting this conversation now',
                                     reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
            return ConversationHandler.END
        else:
            context.user_data['donator_telegram_id'] = _telegram_id
            context.bot.send_message(chat.id, f'{chat.full_name}, alright, now send me the email of the donator',
                                     reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
            return ADD_EMAIL
    except ValueError as e:
        context.bot.send_message(chat.id, f'{chat.full_name} dum dum, that\'s not a Telegram ID, exiting this conversation now',
                                 reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
        return ConversationHandler.END


def email_add(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    msg = update.effective_message

    _donator_email = update.message.text
    context.user_data['donator_email'] = _donator_email
    context.bot.send_message(chat.id, f'{chat.full_name}, alright, now send me payment amount (in USD)',
                             reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
    return ADD_PAYMENT_AMOUNT


def payment_amount(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    msg = update.effective_message

    _donator_amt = update.message.text
    try:
        _donator_amt = float(_donator_amt)
        context.user_data['donator_amt'] = round(_donator_amt, 1)
        if round(_donator_amt, 1) >= 10:
            context.user_data['donator_type'] = 'LTS'
        else:
            context.user_data['donator_type'] = 'Normal'
        context.bot.send_message(chat.id, f'{chat.full_name}, alright, now send me payment method',
                                 reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
        return ADD_PAYMENT_METHOD
    except ValueError as e:
        context.bot.send_message(chat.id, f'{chat.full_name}, that\'s not a valid amount, exiting this conversation now',
                                 reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
        return ConversationHandler.END


def payment_method(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    msg = update.effective_message

    _payment_method = update.message.text
    context.user_data['payment_method'] = _payment_method
    _donation_date = db_ops.get_today_date()
    _donation_date_split = _donation_date.split('-')
    _donation_date_expiry_year = int(_donation_date_split[0]) + 1
    _donation_date_split[0] = str(_donation_date_expiry_year)
    _donation_date_expiry = "-".join(_donation_date_split)
    context.user_data['donation_date'] = _donation_date
    context.user_data['donation_date_expiry'] = _donation_date_expiry

    # All data has been fetched to add new donator, alert the administrator
    _telegram_id = context.user_data['donator_telegram_id']
    donator_email = context.user_data['donator_email']
    _payment_method = context.user_data['payment_method']
    donation_amt = context.user_data['donator_amt']

    _msg = f"<b>New Donator Details</b>\n\n<b>•Telegram ID:</b> {mention_html(_telegram_id, str(_telegram_id))}\n<b>•Donator Email:</b> <code>{donator_email}</code>\n"
    _msg += f'<b>•Donation Amount:</b> {donation_amt}$\n<b>•Donation Method:</b> {_payment_method}\n<b>•Access From:</b> {_donation_date}\n<b>•Access Until:</b> {_donation_date_expiry}\n\n'
    _msg += 'Are you sure this data is okay?'

    inline_kboard = [
        [
            InlineKeyboardButton('Yes!', callback_data='add_yes'),
            InlineKeyboardButton('No :(', callback_data='add_no'),
        ],
    ]

    context.bot.send_message(chat.id, _msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(
        inline_kboard), reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
    return ConversationHandler.END


def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    chat = update.effective_chat
    query.answer()
    callback_data = query.data

    if callback_data == 'add_yes':
        _telegram_id = context.user_data['donator_telegram_id']
        donator_email = context.user_data['donator_email']
        _payment_method = context.user_data['payment_method']
        donator_type = context.user_data['donator_type']
        donation_amt = context.user_data['donator_amt']
        _donation_date = context.user_data['donation_date']
        _donation_date_expiry = context.user_data['donation_date_expiry']

        msg_obj = query.edit_message_text(
            f'{chat.full_name}, all data needed to a donator has been fetched, adding new donator now!')
        rowid = db_ops.add_new_donator(_telegram_id, donator_email, _payment_method,
                                       _donation_date, _donation_date_expiry, donator_type, donation_amt)
        t = datetime.now().astimezone(pytz.timezone('Asia/Kolkata'))
        t = datetime.date(t)
        streak_db_ops.create_user(_telegram_id, t.strftime('%m/%d/%Y'), None)
        if rowid > 0:
            context.bot.edit_message_text(
                'Data insertion successful!', chat_id=chat.id, message_id=msg_obj.message_id)
        else:
            context.bot.edit_message_text(
                'Data insertion failure, check logs!', chat_id=chat.id, message_id=msg_obj.message_id)
        donator_type = db_ops.get_donator_details(_telegram_id)[6]
        if donator_type == 'LTS':
            invites_avail = 2
        elif donator_type == 'Normal':
            invites_avail = 1
        db_ops.set_invites(_telegram_id, invites_avail)

        db_ops.add_payment(donation_amt)

        staff_privileges = db_ops.get_staff_privileges(chat.id)
        if 'add_email' in staff_privileges:
            msg_obj = context.bot.send_message(
                chat.id, f'Trying to add {donator_email} to group(s) now')
        status = group_ops.add_to_group(donator_email, donation_amt)
        print(status)
        if status == 'Success':
            context.bot.edit_message_text(
                f'Added {donator_email} to group(s)', chat_id=chat.id, message_id=msg_obj.message_id)
            _log = f'New donator added with ID: <code>{_telegram_id}</code>\nEmail: {donator_email}\nPayment Method: {_payment_method}\nDonation Date: {_donation_date}\nDonation Expiry: {_donation_date_expiry}\nAmount: {donation_amt}'
            tg_ops.post_log(update, context, _log)
        else:
            context.bot.edit_message_text(
                f'Error, could not add {donator_email} to group(s), due to {status}', chat_id=chat.id, message_id=msg_obj.message_id)
    elif callback_data == 'add_no':
        query.edit_message_text(f'{chat.full_name}, discarding all data now!')


def cancel(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    msg = update.effective_message

    context.bot.send_message(chat.id, f'Bye, {chat.full_name}!\nTo add or edit details of a donator, please press /admin again',
                             reply_markup=ReplyKeyboardRemove(), reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
    return ConversationHandler.END


conv_handler = ConversationHandler(
    entry_points=[CommandHandler('admin', admin)],
    states={
        ADMIN_OPTION: [MessageHandler(Filters.text & ~Filters.command, admin_option)],
        ADD_TELEGRAM_ID: [MessageHandler(Filters.text & ~Filters.command, telegram_id)],
        ADD_EMAIL: [MessageHandler(Filters.text & ~Filters.command, email_add)],
        ADD_PAYMENT_AMOUNT: [MessageHandler(Filters.text & ~Filters.command, payment_amount)],
        ADD_PAYMENT_METHOD: [MessageHandler(Filters.text & ~Filters.command, payment_method)],
        MORE_OPTION: [MessageHandler(Filters.text & ~Filters.command, more_options)],
        STAFF_OPTION: [MessageHandler(Filters.text & ~Filters.command, staff_options)],
        VIEW_DETAILS: [MessageHandler(Filters.text & ~Filters.command, _view_details)],
        REMOVE_DONATOR: [MessageHandler(Filters.text & ~Filters.command, _remove_donator)],
        DONATOR_FUNCTIONS: [MessageHandler(Filters.text & ~Filters.command, donator_functions)],
        DONATOR_FUNC_CHOOSE: [MessageHandler(Filters.text & ~Filters.command, donator_func_choose)],
        LTS_PAYMENT_AMT: [MessageHandler(Filters.text & ~Filters.command, lts_payment_amt)],
        LTS_PAYMENT_METHOD: [MessageHandler(Filters.text & ~Filters.command, lts_payment_method)],
    },
    fallbacks=[CommandHandler('cancel', cancel)]
)

dispatcher.add_handler(conv_handler)
dispatcher.add_handler(CallbackQueryHandler(button, pattern=r'add_.*'))
dispatcher.add_handler(CallbackQueryHandler(
    _remove_donator_btn, pattern=r'd\w{6}_d\w{6}_[yn]\w{1,2}_*\d*'))
dispatcher.add_handler(CallbackQueryHandler(
    donator_nsfw_access_btn, pattern=r'd\w{6}\_n\w{3}\_[yn]\w{1,2}\_\d+'))
dispatcher.add_handler(CallbackQueryHandler(
    donator_lts_access_btn, pattern=r'd\w{6}\_l\w{2}\_[yn]\w{1,2}\_\d+'))
