from bot.helpers import db_ops, tg_ops, google_drive_ops
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, ParseMode,
                      Update)
from telegram.ext import (CallbackContext, CallbackQueryHandler,
                          CommandHandler, ConversationHandler, Filters, MessageHandler)


DRIVE_OPTION, REMOVE_DRIVE, REMOVE_DRIVE_BTN, ADD_DRIVE_ID, ADD_DRIVE_TYPE, EDIT_DRIVE, EDIT_DRIVE_BTN, EDIT_DRIVE_BTN_CNF = range(
    8)


def drive(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    msg = update.effective_message

    if chat.type == 'private':
        if not db_ops.is_staff(msg.from_user.id):
            msg.reply_text(f'{msg.from_user.full_name}, you are not authorized to use this command!',
                           reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
            return
        inline_kboard = [
            [
                InlineKeyboardButton('Add Drive', callback_data='drv_add'),
                InlineKeyboardButton('Remove Drive', callback_data='drv_rmv'),
                InlineKeyboardButton('Edit Drive', callback_data='drv_edt'),
            ]
        ]
        msg.reply_text(f'{msg.from_user.full_name}, choose an option:', reply_markup=InlineKeyboardMarkup(
            inline_keyboard=inline_kboard), reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
        return DRIVE_OPTION
    else:
        if tg_ops.check_chat(update, context):
            if db_ops.is_staff(msg.from_user.id):
                context.bot.send_message(chat.id, f'{msg.from_user.full_name}, this command can only be used in bot DM!',
                                         reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
            else:
                context.bot.send_message(chat.id, f'{msg.from_user.full_name}, this is a staff only reserved command!',
                                         reply_to_message_id=msg.message_id, allow_sending_without_reply=True)


def drive_button(update: Update, _: CallbackContext) -> None:
    query = update.callback_query
    callback_data = query.data.split('_')[1]
    if not db_ops.is_staff(query.from_user.id):
        query.answer('This button is not meant for you', show_alert=True)
        return
    query.answer('Request received!')
    if callback_data == 'rmv':
        drive_details = db_ops.get_global_drive_details()
        drive_details_text = ""
        for details in drive_details:
            drive_details_text += f'• {details[0]}: <code>{details[3]}</code> [{details[1]}]\n'
        drive_details_text += '\nPlease send the drive ID you want to remove:'
        query.edit_message_text(drive_details_text, parse_mode=ParseMode.HTML)
        return REMOVE_DRIVE
    elif callback_data == 'add':
        query.edit_message_text(
            'Alright, let\'s add a new drive to the DB! I will need some information.\nPlease enter the drive ID:')
        return ADD_DRIVE_ID
    elif callback_data == 'edt':
        query.edit_message_text('Send a drive ID to edit information:')
        return EDIT_DRIVE


def edit_drive(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    msg = update.effective_message
    drive_id = update.message.text
    tmp_all_drive_id = db_ops.get_global_drive_ids()
    all_drive_id = list()
    for id in tmp_all_drive_id:
        all_drive_id.append(id[0])
    del tmp_all_drive_id
    if drive_id not in all_drive_id:
        context.bot.send_message(chat.id, 'That is not a valid drive ID in DB',
                                 reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
        return ConversationHandler.END
    else:
        inline_kboard = [
            [
                InlineKeyboardButton('Refresh Drive Name',
                                     callback_data=f'drv=ed=ref={drive_id}'),
                InlineKeyboardButton('Change Drive Type',
                                     callback_data=f'drv=ed=chg={drive_id}'),
            ]
        ]
        drive_details = db_ops.get_drive_details_from_id(drive_id)
        context.bot.send_message(chat.id, f'<b>Current Drive Name:</b> {drive_details[1]}\n<b>Current Drive Type:</b> {drive_details[2]}\n\n<u>Choose an option below:</u>', reply_markup=InlineKeyboardMarkup(inline_kboard),
                                 reply_to_message_id=msg.message_id, allow_sending_without_reply=True, parse_mode=ParseMode.HTML)
        return EDIT_DRIVE_BTN


def edit_drive_btn_handler(update: Update, _: CallbackContext) -> None:
    query = update.callback_query
    callback_data = query.data.split('=')[2]
    callback_drive_id = query.data.split('=')[3]
    query.answer('Processing...')
    if callback_data == 'ref':
        drive_old_name = db_ops.get_drive_details_from_id(callback_drive_id)[1]
        drive_new_name, resp = google_drive_ops.fetch_drive_name(
            callback_drive_id)
        if drive_old_name == drive_new_name:
            query.edit_message_text('No changes in drive name!')
            return ConversationHandler.END
        else:
            query.edit_message_text(
                f'Drive name changed from <code>{drive_old_name}</code> to <code>{drive_new_name}</code>', parse_mode=ParseMode.HTML)
            db_ops.edit_drive(drive_id=callback_drive_id,
                              drive_name=drive_new_name)
            return ConversationHandler.END
    elif callback_data == 'chg':
        drive_old_type = db_ops.get_drive_details_from_id(callback_drive_id)[2]
        if drive_old_type == 'Normal':
            drive_new_type = 'LTS'
        else:
            drive_new_type = 'Normal'
        inline_kboard = [
            [
                InlineKeyboardButton(
                    'Yes ✅', callback_data=f'drv=ty=apr={callback_drive_id}'),
                InlineKeyboardButton(
                    'No ❌', callback_data=f'drv=ty=dny={callback_drive_id}'),
            ]
        ]
        query.edit_message_text(
            f'Current drive type is <i>{drive_old_type}</i>\n\nChange to <i>{drive_new_type}</i>?', reply_markup=InlineKeyboardMarkup(inline_kboard), parse_mode=ParseMode.HTML)
        return EDIT_DRIVE_BTN_CNF


def edit_drive_btn_cnf_handler(update: Update, _: CallbackContext) -> None:
    query = update.callback_query
    callback_data = query.data.split('=')[2]
    query.answer()
    if callback_data == 'dny':
        query.edit_message_text('Discarding changes!')
        return ConversationHandler.END
    elif callback_data == 'apr':
        query.edit_message_text('Updating drive type...')
        callback_drive_id = query.data.split('=')[3]
        drive_old_type = db_ops.get_drive_details_from_id(callback_drive_id)[2]
        if drive_old_type == 'Normal':
            drive_new_type = 'LTS'
        else:
            drive_new_type = 'Normal'
        db_ops.edit_drive(drive_id=callback_drive_id,
                          drive_type=drive_new_type)
        google_drive_ops.change_drive_type(
            drive_id=callback_drive_id, drive_type=drive_new_type)
        query.edit_message_text('Drive type updated!')
        return ConversationHandler.END


def add_drive_id(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    msg = update.effective_message
    drive_id = update.message.text
    tmp_all_drive_id = db_ops.get_global_drive_ids()
    all_drive_id = list()
    for id in tmp_all_drive_id:
        all_drive_id.append(id[0])
    del tmp_all_drive_id
    if drive_id in all_drive_id:
        context.bot.send_message(chat.id,
                                 'Drive already exists in DB, ending conversation now!', reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
        return ConversationHandler.END
    m = context.bot.send_message(chat.id, 'Trying to fetch drive name...',
                                 reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
    txt, resp = google_drive_ops.fetch_drive_name(drive_id)
    if resp:
        m.edit_text(f'Error occurred: {txt}\nPlease send drive ID again')
        return ADD_DRIVE_ID
    else:
        inline_kboard = [
            [
                InlineKeyboardButton(
                    'Normal Drive', callback_data='drv_ad_nrm'),
                InlineKeyboardButton('LTS Drive', callback_data='drv_ad_lts'),
            ]
        ]
        context.user_data['drv_details'] = {
            'drive_name': txt, 'drive_id': drive_id}
        m.edit_text(f'Found drive name: {txt}\n\nSelect the type of drive now',
                    reply_markup=InlineKeyboardMarkup(inline_kboard))
        return ADD_DRIVE_TYPE


def add_drive_type_btn_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    callback_data = query.data.split('_')[2]
    query.answer('Processing...')
    if callback_data == 'nrm':
        drive_type = 'Normal'
    elif callback_data == 'lts':
        drive_type = 'LTS'
    db_ops.add_drive(context.user_data['drv_details']['drive_id'],
                     context.user_data['drv_details']['drive_name'], drive_type)
    query.edit_message_text('New drive added to DB!')
    return ConversationHandler.END


def remove_drive(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    drive_id = update.message.text
    tmp_all_drive_id = db_ops.get_global_drive_ids()
    all_drive_id = list()
    for id in tmp_all_drive_id:
        all_drive_id.append(id[0])
    del tmp_all_drive_id
    if drive_id not in all_drive_id:
        context.bot.send_message(
            chat.id, f'That is not a valid drive ID, please send again!')
        return REMOVE_DRIVE
    else:
        inline_kboard = [
            [
                InlineKeyboardButton(
                    'Yes ✅', callback_data=f'drv=rm=yes={drive_id}'),
                InlineKeyboardButton(
                    'No ❌', callback_data=f'drv=rm=no={drive_id}'),
            ]
        ]
        data = db_ops.get_drive_details_from_id(drive_id)
        drive_txt = f"<b>Drive Name:</b> {data[1]}\n<b>Drive Type:</b> {data[2]}\n<b>Last Reported Size:</b> {data[3]}"
        drive_txt += '\n\nAre you sure you want to remove this drive from DB?'
        context.bot.send_message(chat.id, drive_txt, reply_markup=InlineKeyboardMarkup(
            inline_kboard), parse_mode=ParseMode.HTML)
        return REMOVE_DRIVE_BTN


def remove_drive_btn_handler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    callback_data = query.data.split('=')[2]
    query.answer('Processing...')
    if callback_data == 'no':
        query.edit_message_text('Taking no action!')
    elif callback_data == 'yes':
        drive_id = query.data.split('=')[3]
        db_ops.delete_drive(drive_id)
        query.edit_message_text('Done! Drive has been removed from DB!')
    return ConversationHandler.END


def cancel(update: Update, _: CallbackContext) -> None:
    msg = update.effective_message
    msg.reply_text(f'Bye, {msg.from_user.full_name}!\nTo add or edit details of a drive, please press /drive again',
                   reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
    return ConversationHandler.END


drv_conv_handler = ConversationHandler(
    entry_points=[CommandHandler('drive', drive)],
    states={
        DRIVE_OPTION: [CallbackQueryHandler(
            drive_button, pattern=r'drv_(add|rmv|edt)')],
        REMOVE_DRIVE: [MessageHandler(filters=Filters.text & ~Filters.command, callback=remove_drive)],
        REMOVE_DRIVE_BTN: [CallbackQueryHandler(
            remove_drive_btn_handler, pattern=r'drv=rm=(yes|no)=\w+')],
        ADD_DRIVE_ID: [MessageHandler(filters=Filters.text & ~Filters.command, callback=add_drive_id)],
        ADD_DRIVE_TYPE: [CallbackQueryHandler(add_drive_type_btn_handler, pattern=r'drv_ad_(nrm|lts)')],
        EDIT_DRIVE: [MessageHandler(
            Filters.text & ~Filters.command, edit_drive)],
        EDIT_DRIVE_BTN: [CallbackQueryHandler(edit_drive_btn_handler, pattern=r'drv=ed=(ref|chg)=\w+')],
        EDIT_DRIVE_BTN_CNF: [CallbackQueryHandler(edit_drive_btn_cnf_handler, pattern=r'drv=ty=(apr|dny)=\w+')],
    },
    fallbacks=[CommandHandler('cancel', cancel)]
)
