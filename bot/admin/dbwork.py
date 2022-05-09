import os

from bot.helpers import db_ops, file_ops, streak_db_ops, tg_ops
from bot.helpers.tg_ops import post_log, restricted
from telegram import ParseMode, Update
from telegram.ext import CallbackContext
from telegram.utils.helpers import mention_html


@restricted
def dbdump(update: Update, _: CallbackContext):
    chat = update.effective_chat
    msg = update.message
    _msg = update.effective_message
    user = update.effective_user
    if chat.type in ['group', 'supergroup', 'channel']:
        msg.reply_text('Command can only be used in PMs',
                       reply_to_message_id=_msg.message_id, allow_sending_without_reply=True)
        return
    command = update.message.text.split()[0]
    if len(update.message.text.split()) == 1:
        msg.reply_text(f'<b>You need to provide what type of dump do you need</b>\n\n<u>Correct Usage:</u> <code>/dump main</code> or <code>/dump streak</code>',
                       parse_mode=ParseMode.HTML, reply_to_message_id=_msg.message_id, allow_sending_without_reply=True)
        return
    dump_type = update.message.text.split()[1]
    staff_privileges = db_ops.get_staff_privileges(user.id)
    if not 'dump_db' in staff_privileges:
        msg.reply_text('<b>You are not authorized to perform a DB dump!</b>\n\nAsk for permission from a super-administrator for access',
                       parse_mode=ParseMode.HTML, reply_to_message_id=_msg.message_id, allow_sending_without_reply=True)
        return
    if dump_type == 'main':
        all_data = db_ops.get_all_donator_details()
        return_data = file_ops.dump_to_file(all_data, dump_type)
        if return_data is None:
            msg.reply_text('Some error occurred during dumping of data',
                           reply_to_message_id=_msg.message_id, allow_sending_without_reply=True)
            return
        else:
            msg.reply_document(open(
                return_data, 'rb'), caption=f'Here is your {dump_type} DB dump', reply_to_message_id=_msg.message_id, allow_sending_without_reply=True)
            os.remove(return_data)
            log = f'\n{mention_html(user.id, user.full_name)} [User ID: <code>{user.id}</code>] <b>dumped main DB</b>\n'
            tg_ops.post_log(update, _, log)
    elif dump_type == 'streak':
        all_data = streak_db_ops.get_all_details()
        return_data = file_ops.dump_to_file(all_data, dump_type)
        if return_data is None:
            msg.reply_text('Some error occurred during dumping of data',
                           reply_to_message_id=_msg.message_id, allow_sending_without_reply=True)
            return
        else:
            msg.reply_document(open(
                return_data, 'rb'), caption=f'Here is your {dump_type} DB dump', reply_to_message_id=_msg.message_id, allow_sending_without_reply=True)
            os.remove(return_data)
            log = f'\n{mention_html(user.id, user.full_name)} [User ID: <code>{user.id}</code>] <b>dumped streaks DB</b>\n'
            tg_ops.post_log(update, _, log)
    else:
        msg.reply_text('<b>That is not a valid DB dump type, duh!</b>', parse_mode=ParseMode.HTML,
                       reply_to_message_id=_msg.message_id, allow_sending_without_reply=True)
        return
