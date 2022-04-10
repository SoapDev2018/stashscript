from functools import wraps

from bot.helpers import db_ops
from bot.helpers import generic_ops
from telegram import Update
from telegram.ext.callbackcontext import CallbackContext

def check_chat(update: Update, context: CallbackContext) -> bool:
    chat = update.effective_chat

    if chat.type == 'group' or chat.type == 'supergroup' or chat.type == 'channel':
        if not chat.id in generic_ops.get_auth_chat():
            context.bot.leave_chat(chat.id)
            return
        else:
            return True
    else:
        return False


def restricted(func):
    @wraps(func)
    def wrapped(update: Update, context: CallbackContext, *args, **kwargs):
        user_id = update.effective_user.id
        if not db_ops.is_staff(user_id):
            print(f'Unauthorized access denied for {user_id}')
            update.message.reply_text('Unauthorized access denied')
            return
        return func(update, context, *args, **kwargs)
    return wrapped
