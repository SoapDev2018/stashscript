import html
import re

from bot import HW_GROUP_ID, HW_LOG_CHANNEL_ID, IV_GROUP_ID, dispatcher
from bot.helpers import db_ops, generic_ops, tg_ops
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup, Message,
                      ParseMode, Update)
from telegram.error import BadRequest
from telegram.ext import (CallbackQueryHandler, ChatJoinRequestHandler,
                          CommandHandler)
from telegram.ext.callbackcontext import CallbackContext
from telegram.utils.helpers import create_deep_linked_url, mention_html


def invite(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    msg = update.effective_message

    if tg_ops.check_chat(update, context):
        context.bot.send_message(chat.id, f'{msg.from_user.full_name}, this command can only be used in bot DM!',
                                 reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
    else:
        inline_kboard = [
            [
                InlineKeyboardButton('Homeworks 🔞', callback_data='hw_invite'),
                InlineKeyboardButton('Invite Code 📓', callback_data='inv_code')
            ]
        ]
        context.bot.send_message(chat.id, '<b>Please select where you want invite for:</b>', parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(
            inline_kboard), reply_to_message_id=msg.message_id, allow_sending_without_reply=True)


def inv_code_btn(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    chat = update.effective_chat
    user = update.callback_query.from_user
    if not db_ops.is_donator(user.id):
        # Non donator pressed the button
        query.answer('This button is for donators only', show_alert=True)
        query.delete_message()
        return
    else:
        query.answer('Your request has been received, please have patience!')
        query.delete_message()
        context.bot.send_chat_action(chat.id, 'typing')
        invites_avail = db_ops.get_invites(user.id)
        if invites_avail is None:
            if db_ops.is_staff(user.id):
                invites_avail = -1
            else:
                donator_type = db_ops.get_donator_details(user.id)[6]
                if donator_type == 'LTS':
                    invites_avail = 2
                elif donator_type == 'Normal':
                    invites_avail = 1
            db_ops.set_invites(user.id, invites_avail)
        can_invite = True
        if db_ops.is_staff(user.id):
            msg = 'You have <b>unlimited</b> invites!'
        else:
            if invites_avail > 0:
                msg = f'You have <code>{invites_avail}</code> available invites'
            elif invites_avail == 0:
                can_invite = False
                msg = 'You have <code>0</code> available invites'
        if can_invite:
            inline_kboard = [
                [
                    InlineKeyboardButton('Yes ✅', callback_data='ic_yes'),
                    InlineKeyboardButton('No ❌', callback_data='ic_no'),
                ]
            ]
            msg += '\nWould like to generate an invite?'
            context.bot.send_message(
                chat.id, msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(inline_kboard))
        else:
            context.bot.send_message(chat.id, msg, parse_mode=ParseMode.HTML)


def inv_code_btn_handler(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    query = update.callback_query
    user = query.from_user
    query.answer('Request has been received!')
    data = query.data.split('_')[1]
    if data == 'no':
        # Don't generate invite
        query.edit_message_text('Not generating an invite code')
    elif data == 'yes':
        # Generate an invite, return deeplinked URL
        query.delete_message()
        invite_code = db_ops.fetch_invite(chat.id)
        if not invite_code:
            m = context.bot.send_message(
                chat.id, 'Generating an invite code now...')
            context.bot.send_chat_action(chat.id, 'typing')
            invite_code = generic_ops.generate_hash()
            if not db_ops.is_staff(user.id):
                invites_avail = db_ops.get_invites(user.id)
                invites_avail -= 1
                db_ops.set_invites(user.id, invites_avail)
            db_ops.write_invite(user.id, user.full_name, invite_code)
            context.bot.edit_message_text(
                text='Please forward the following message to your invitee, in their DM:', chat_id=chat.id, message_id=m.message_id)
        else:
            context.bot.send_message(
                chat_id=chat.id, text='You already have an invite code generated!\nPlease forward the following message to your invitee, in their DM:')
        url = create_deep_linked_url(
            context.bot.get_me().username, f'inv_{invite_code}')
        context.bot.send_message(
            chat.id, f'Click the following URL and follow the instructions:\n\n{url}')


def invite_hw_btn(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    chat = update.effective_chat
    query.answer('Your request has been received, please have patience!')
    callback_data = query.data
    if callback_data == 'hw_invite':
        if db_ops.get_nsfw_access(chat.id) or db_ops.is_staff(chat.id):
            # Member is donator and has NSFW access or Member is staff
            if context.bot.get_chat_member(HW_GROUP_ID, chat.id)['status'] == 'left':
                hw_group_link = context.bot.create_chat_invite_link(
                    chat_id=HW_GROUP_ID, member_limit=1)['invite_link']
                context.user_data['hw_group_link'] = hw_group_link
                inline_kboard = [
                    [
                        InlineKeyboardButton(
                            'Check ✅', callback_data='hw_check')
                    ]
                ]
                try:
                    query.edit_message_text(
                        f'Hello {chat.full_name}, you can join our Homeworks group with this link:\n{hw_group_link}\nPlease be advised, this link is valid for one person only!', reply_markup=InlineKeyboardMarkup(inline_kboard), disable_web_page_preview=True)
                except BadRequest as e:
                    print(e)
            elif context.bot.get_chat_member(HW_GROUP_ID, chat.id)['status'] in ['administrator', 'creator', 'member', 'restricted']:
                # Member is already a member
                query.edit_message_text(
                    f'Hello {chat.full_name}, you already have access to HW chat!')
        else:
            # Member is donator, but is neither staff nor has NSFW access
            if context.bot.get_chat_member(HW_GROUP_ID, chat.id)['status'] == 'left':
                try:
                    hw_group_chat_join_rqst_link = context.bot_data['don_hw_chat_rqst_link']
                except KeyError:
                    hw_group_chat_join_rqst_link = context.bot.create_chat_invite_link(
                        chat_id=HW_GROUP_ID, creates_join_request=True)['invite_link']
                    context.bot_data['don_hw_chat_rqst_link'] = hw_group_chat_join_rqst_link
                try:
                    m = query.edit_message_text(
                        f'Hello {chat.full_name}, you can request access to our homework group using the following link:\n{hw_group_chat_join_rqst_link}', disable_web_page_preview=True)
                    context.user_data['m_query'] = m
                except BadRequest as e:
                    print(e)
            elif context.bot.get_chat_member(HW_GROUP_ID, chat.id)['status'] in ['administrator', 'creator', 'member', 'restricted']:
                query.edit_message_text(
                    f'Hello {chat.full_name}, you already have access to HW chat!')


def invite_hw_check_btn(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    chat = update.effective_chat
    query.answer()
    callback_data = query.data

    if callback_data == 'hw_check':
        hw_group_link = context.user_data['hw_group_link']
        member_status = context.bot.get_chat_member(
            HW_GROUP_ID, chat.id)['status']
        if member_status == 'left':
            inline_kboard = [
                [
                    InlineKeyboardButton(
                        'Check ✅', callback_data='hw_check')
                ]
            ]
            try:
                query.edit_message_text(
                    f'{chat.full_name}, you have not joined the group yet!\nPlease join using the following link:\n{hw_group_link}\nAfter joining, please press the below button', reply_markup=InlineKeyboardMarkup(inline_kboard), disable_web_page_preview=True)
            except BadRequest as e:
                print(e)
        else:
            context.bot.revoke_chat_invite_link(HW_GROUP_ID, hw_group_link)
            query.edit_message_text(
                f'{chat.full_name}, thank you for joining our HW group!')
            if db_ops.is_staff(chat.id):
                # Donator is staff, promote in chat
                context.bot.promote_chat_member(HW_GROUP_ID, chat.id, can_change_info=True,
                                                can_delete_messages=True, can_restrict_members=True, can_pin_messages=True)
                context.bot.set_chat_administrator_custom_title(
                    HW_GROUP_ID, chat.id, 'Core Staff')


def chat_join_req(update: Update, context: CallbackContext) -> None:
    user = update.chat_join_request.from_user
    chat = update.chat_join_request.chat
    if chat.id == HW_GROUP_ID:
        inline_kboard = [
            [
                InlineKeyboardButton(
                    'Approve ✅', callback_data=f'approve_{str(user.id)}'),
                InlineKeyboardButton(
                    'Deny ❌', callback_data=f'deny_{str(user.id)}'),
            ]
        ]
        base_chnl_msg = f'{user.mention_html()} is requesting to join HW group\n\n<b>Donator</b>: '
        if db_ops.is_donator(user.id):
            base_chnl_msg += 'Yes'
        else:
            base_chnl_msg += 'No'
        context.bot.send_message(HW_LOG_CHANNEL_ID, base_chnl_msg,
                                 reply_markup=InlineKeyboardMarkup(inline_kboard), parse_mode=ParseMode.HTML)
        try:
            m = context.user_data['m_query']
            context.bot.delete_message(user.id, m.message_id)
        except KeyError as e:
            # IDK how will it even come here
            print(e)
    elif chat.id == IV_GROUP_ID:
        user = update.chat_join_request.from_user
        m: Message = context.user_data['m_ic']
        ic_details_user_id: int = context.user_data['ic_user_id']
        db_ops.set_invite_action(user.id, 'Received')
        context.bot.edit_message_text(chat_id=user.id, message_id=m.message_id,
                                      text='Please wait while your invitee <u>either confirms or declines</u> your invite!', parse_mode=ParseMode.HTML)
        inline_kboard = [
            [
                InlineKeyboardButton(
                    'Yes ✅', callback_data=f'cnf_yes_{str(user.id)}'),
                InlineKeyboardButton(
                    'No ❌', callback_data=f'cnf_no_{str(user.id)}'),
            ]
        ]
        _msg = f'Did you invite the following user?\n\n{html.escape(user.full_name)} [User ID: {user.id}]'
        if user.username:
            _msg += f'\n[Username: @{user.username}]'
        _msg += f'\n\n{mention_html(user.id, user.full_name)} [Tried to mention user]'
        context.bot.send_message(
            ic_details_user_id, _msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(inline_kboard))


def hw_appr_deny_btn(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    cb_from_user_id = query.from_user.id
    if db_ops.is_staff(cb_from_user_id):
        query.answer('Request received!')
        callback_data = query.data

        cb_user_id = re.search(r'\d+', callback_data).group()
        callback_type = callback_data.split('_')[0]
        if callback_type == 'approve':
            # Approved to join HW group
            query.edit_message_text(
                f'Approved join request for {mention_html(cb_user_id, str(cb_user_id))}!', parse_mode=ParseMode.HTML)
            context.bot.approve_chat_join_request(HW_GROUP_ID, cb_user_id)
            context.bot.send_message(
                cb_user_id, f'Hello, your request to join NSFW group has been approved!')
        elif callback_type == 'deny':
            # Declined join request
            query.edit_message_text(
                f'Declined join request for {mention_html(cb_user_id, str(cb_user_id))}!', parse_mode=ParseMode.HTML)
            context.bot.decline_chat_join_request(HW_GROUP_ID, cb_user_id)
            context.bot.send_message(
                cb_user_id, f'Hello, your request to join NSFW group has been denied')
    else:
        query.answer('This is not meant for you!')


def bl_invite(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message
    if not db_ops.is_staff(user.id):
        context.bot.send_message(chat.id, 'This command is only for staff use!',
                                 reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
        return
    if len(update.message.text.split()) == 1:
        context.bot.send_message(chat.id, 'You need to provide a telegram ID to blacklist!',
                                 reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
    else:
        telegram_id = update.message.text.split()[1]
        try:
            telegram_id = int(telegram_id)
            if db_ops.is_donator(telegram_id):
                context.bot.send_message(chat.id, 'That user is already a donator!',
                                         reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
                return
            if db_ops.get_invite_action(telegram_id) is not None:
                if db_ops.get_invite_action(telegram_id=telegram_id)[1] == 'Received' and chat.id == IV_GROUP_ID:
                    context.bot.ban_chat_member(
                        IV_GROUP_ID, telegram_id, revoke_messages=True)
                    context.bot.unban_chat_member(
                        IV_GROUP_ID, telegram_id, only_if_banned=True)
                    db_ops.del_invite_action(telegram_id=telegram_id)
                else:
                    update.message.reply_text('That ID is already blacklisted/denied',
                                              reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
                    return
            cmd = update.message.text.split()[0][1:]
            if cmd == 'blacklist':
                db_ops.set_invite_action(telegram_id, 'Blacklisted')
                _msg = f'The Telegram ID {telegram_id} has been blacklisted!'
            elif cmd == 'deny':
                db_ops.set_invite_action(telegram_id, 'Denied')
                _msg = f'Donation requests will be denied from Telegram ID {telegram_id}'
            context.bot.send_message(chat.id, _msg,
                                     reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
            tg_ops.post_log(update, context, _msg)
        except ValueError:
            context.bot.send_message(chat.id, 'That is not a valid Telegram ID',
                                     reply_to_message_id=msg.message_id, allow_sending_without_reply=True)


def unbl_invite(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message
    if not db_ops.is_staff(user.id):
        context.bot.send_message(chat.id, 'This command is only for staff use!',
                                 reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
        return
    if len(update.message.text.split()) == 1:
        context.bot.send_message(chat.id, 'You need to provide a telegram ID to blacklist!',
                                 reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
        return
    telegram_id = update.message.text.split()[1]
    try:
        telegram_id = int(telegram_id)
        if db_ops.is_donator(telegram_id):
            update.message.reply_text('That ID is already a donator!',
                                      reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
            return
        if db_ops.get_invite_action(telegram_id) is None:
            update.message.reply_text('That ID is not blacklisted or denied',
                                      reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
            return
        else:
            db_ops.del_invite_action(telegram_id=telegram_id)
            update.message.reply_text('The ID has been unblacklisted!',
                                      reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
    except ValueError:
        if telegram_id == 'all':
            d = db_ops.del_invite_action(action='all')
            update.message.reply_text(f'A total of {d} IDs were unblacklisted!',
                                      reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
        else:
            update.message.reply_text('This is not a valid Telegram ID',
                                      reply_to_message_id=msg.message_id, allow_sending_without_reply=True)


invite_handler = CommandHandler('invite', invite)
dispatcher.add_handler(invite_handler)
dispatcher.add_handler(ChatJoinRequestHandler(chat_join_req, run_async=True))
dispatcher.add_handler(CallbackQueryHandler(
    invite_hw_btn, pattern=r'hw_invite'))
dispatcher.add_handler(CallbackQueryHandler(
    invite_hw_check_btn, pattern=r'hw_check'))
dispatcher.add_handler(CallbackQueryHandler(
    hw_appr_deny_btn, pattern=r'[ad]\w{3,6}\_\d+'))
dispatcher.add_handler(CallbackQueryHandler(inv_code_btn, pattern=r'inv_code'))
dispatcher.add_handler(CallbackQueryHandler(
    inv_code_btn_handler, pattern=r'ic\_[ny][eo]s?'))
