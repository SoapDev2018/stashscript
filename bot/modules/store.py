from telegram import Update, ParseMode, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from bot.helpers import streak_db_ops, trans_db_ops, generic_ops, tg_ops
from bot.helpers.tg_ops import restricted
from telegram.utils.helpers import mention_html


def send(update: Update, context: CallbackContext) -> None:
    msg = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    if len(update.message.text.split()) == 1 or len(update.message.text.split()) == 2:
        update.message.reply_text('You need to provide a user ID and amount to send.\nCorrect usage: <code>/send ID amount</code>',
                                  parse_mode=ParseMode.HTML, reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
        return
    pending = trans_db_ops.get_pending_transaction(user.id)
    if pending is not None:
        update.message.reply_text('<b>You already have a pending transaction, please confirm/deny it before trying another transaction</b>',
                                  parse_mode=ParseMode.HTML, reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
        return
    telegram_id = update.message.text.split()[1]
    amt_to_send = update.message.text.split()[2]
    try:
        telegram_id = int(telegram_id)
    except ValueError:
        update.message.reply_text('<b>That is not a valid Telegram ID</b>', parse_mode=ParseMode.HTML,
                                  reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
        return
    try:
        amt_to_send = int(amt_to_send)
    except ValueError:
        update.message.reply_text('<b>That is not a valid points amount to send</b>', parse_mode=ParseMode.HTML,
                                  reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
        return
    member_details = streak_db_ops.get_details(telegram_id)
    if member_details is None:
        update.message.reply_text('<b>Cannot send to that user!</b>', parse_mode=ParseMode.HTML,
                                  reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
        return
    elif member_details[-3] is None:
        update.message.reply_text('<b>That user has not been online recently, can\'t send points to them</b>',
                                  parse_mode=ParseMode.HTML, reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
        return
    if amt_to_send < 10:
        update.message.reply_text('<b>You cannot send less than 10 points to someone else</b>',
                                  parse_mode=ParseMode.HTML, reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
        return
    elif amt_to_send > member_details[3]:
        update.message.reply_text('<b>You cannot send more points than you have!</b>',
                                  parse_mode=ParseMode.HTML, reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
        return
    context.bot.send_chat_action(chat.id, 'typing')
    hash = generic_ops.generate_hash()
    while(trans_db_ops.get_transaction(hash) is not None):
        hash = generic_ops.generate_hash()
    trans_db_ops.add_transaction(hash, user.id, telegram_id, amt_to_send)
    kboard = [
        [
            InlineKeyboardButton('Yes ✅', callback_data=f'tr_yes_{hash}'),
            InlineKeyboardButton('No ❌', callback_data=f'tr_no_{hash}'),
        ]
    ]
    tax = amt_to_send // 10
    if tax > 10:
        tax = 10
    _msg = f'You are sending {amt_to_send} points to {member_details[-3]} [User ID: <code>{telegram_id}</code>]\nPress <b>Yes ✅</b> to confirm the transaction or <b>No ❌</b> to cancel the transaction'
    _msg += f'\nThe receiver will receive {amt_to_send - tax} points'
    _msg += f'\n\n<i>The system will take a tax of {tax} points</i>'
    _log = f'A transaction of <b>{amt_to_send} points</b> was initiated by <code>{user.id}</code> to be sent to <code>{telegram_id}</code>\nThe system will levy a tax of <b>{tax} points</b>\nTransaction Hash: <code>{hash}</code>'
    tg_ops.post_log(update, context, _log)
    update.message.reply_text(_msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(
        kboard), reply_to_message_id=msg.message_id, allow_sending_without_reply=True)


def send_btn(update: Update, _: CallbackContext) -> None:
    query = update.callback_query
    user = query.from_user
    transaction_hash = query.data.split('_')[2]
    transaction_details = trans_db_ops.get_transaction(transaction_hash)
    if int(transaction_details[1]) != user.id:
        query.answer('This button is not meant for you', show_alert=True)
        return
    transaction_type = query.data.split('_')[1]
    query.answer('Request received')
    if transaction_type == 'no':
        trans_db_ops.del_transaction(transaction_hash)
        query.edit_message_text(
            '<b>Cancelled the transaction!</b>', parse_mode=ParseMode.HTML)
        _log = f'A transaction of <b>{transaction_details[3]} points</b> from <code>{transaction_details[1]}</code> to <code>{transaction_details[2]}</code> was cancelled by <code>{transaction_details[1]}</code>'
    elif transaction_type == 'yes':
        trans_db_ops.confirm_transaction(transaction_hash)
        receiver_details = streak_db_ops.get_details(transaction_details[2])
        tax = int(transaction_details[3]) // 10
        if tax > 10:
            tax = 10
        amount = transaction_details[3] - tax
        streak_db_ops.send_points(user.id, transaction_details[2], amount, tax)
        trans_db_ops.add_bot_balance(tax)
        query.edit_message_text(
            f'Transferred {transaction_details[3] - tax} points to {mention_html(transaction_details[2], receiver_details[-3])} [User ID: <code>{transaction_details[2]}</code>]', parse_mode=ParseMode.HTML)
        _log = f'A transaction of <b>{transaction_details[3]} points</b> from <code>{transaction_details[1]}</code> to <code>{transaction_details[2]}</code> was confirmed by <code>{transaction_details[1]}</code>\nThe system levied a tax of <b>{tax} points</b>'
    tg_ops.post_log(update, _, _log)


@restricted
def cancel_trans(update: Update, _: CallbackContext) -> None:
    msg = update.effective_message

    if len(update.message.text.split()) == 1:
        update.message.reply_text('<b>Invalid command usage!</b>\nCorrect usage: <code>/ctrans transaction_hash</code>',
                                  parse_mode=ParseMode.HTML, allow_sending_without_reply=True, reply_to_message_id=msg.message_id)
        return

    transaction_hash = update.message.text.split()[1]
    transaction_details = trans_db_ops.get_transaction(transaction_hash)
    if transaction_details is None:
        update.message.reply_text('<b>That is not a valid transaction hash</b>', parse_mode=ParseMode.HTML,
                                  reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
        return
    trans_db_ops.del_transaction(transaction_hash)
    update.message.reply_text(f'<b>Cancelled transaction with hash</b> <code>{transaction_hash}</code>',
                              parse_mode=ParseMode.HTML, reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
    _log = f'A transaction of <b>{transaction_details[3]} points</b> from <code>{transaction_details[1]}</code> to <code>{transaction_details[2]}</code> was cancelled by <b>Staff</b>'
    tg_ops.post_log(update, _, _log)


@restricted
def get_pending_trans(update: Update, _: CallbackContext) -> None:
    msg = update.effective_message

    transactions = trans_db_ops.get_all_pending_transactions()
    _msg = ""
    if len(transactions) > 0:
        for t in transactions:
            _msg += f'<b>Transaction Hash:</b> <code>{t[0]}</code>\n<b>Sender ID:</b> <code>{t[1]}</code>\n<b>Receiver ID:</b> <code>{t[2]}</code>\n<b>Amount:</b> <code>{t[3]}</code>\n\n'
        update.message.reply_text(_msg, parse_mode=ParseMode.HTML,
                                  reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
    else:
        update.message.reply_text('<b>No pending transactions!</b>', parse_mode=ParseMode.HTML,
                                  reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
