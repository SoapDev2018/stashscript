from datetime import datetime
import pytz

from telegram import ParseMode, Update
from telegram.ext import CallbackContext
from telegram.utils.helpers import mention_html

from bot import OWNER_ID
from bot.helpers import streak_db_ops as db_ops
from bot.helpers import tg_ops


def get_xp(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user
    t = datetime.now().astimezone(pytz.timezone('Asia/Kolkata'))
    t = datetime.date(t)
    user_details = db_ops.get_details(user.id)
    if user_details is None:
        db_ops.create_user(user.id, t.strftime('%m/%d/%Y'), user.full_name)
        user_details = db_ops.get_details(user.id)
    if user_details[-3] is None:
        db_ops.set_user_full_name(user.id, user.full_name)
    else:
        if user_details[-3] != user.full_name:
            db_ops.set_user_full_name(user.id, user.full_name)
    if msg.via_bot:
        return
    else:
        text = msg.text
        if len(text.split()) < 5:
            pass
        else:
            xp = 0
            for word in text.split():
                l_word = len(word)
                xp += l_word // 2
                if xp >= 10:
                    xp = 10
                    break
            date_diff = (
                t - datetime.date(datetime.strptime(user_details[7], '%m/%d/%Y'))).days
            streak_broken = False
            if date_diff == 0:
                pass
            elif date_diff == 1:
                db_ops.set_streak(user.id, (1 + int(user_details[2])))
            else:
                db_ops.set_streak(user.id, 0)
                streak_broken = True
            db_ops.set_last_chat_date(user.id, t.strftime('%m/%d/%Y'))
            user_details = db_ops.get_details(user.id)
            current_streak = 1 + user_details[2]
            extra_xp = current_streak - 1
            if extra_xp > 10:
                extra_xp = 10
            daily_xp_granted = user_details[5]
            if daily_xp_granted == 'No':
                xp += extra_xp
                db_ops.set_daily_xp_granted(user.id)
            else:
                extra_xp = 0
            daily_xp = user_details[4]
            prev_xp = user_details[1]
            if (daily_xp + (xp - extra_xp)) > 100:
                xp = 100 - daily_xp
            if xp > 0:
                db_ops.set_daily_xp(user.id, (xp - extra_xp))
                xp += prev_xp
                db_ops.set_xp(user.id, xp)
            user_details = db_ops.get_details(user.id)
            current_lvl = user_details[6]
            current_xp = user_details[1]
            level_upgrade = False
            if current_xp >= (100 + 150 * current_lvl):
                db_ops.set_level(user.id, (1 + current_lvl))
                level_upgrade = True
                points = (100 + 150 * current_lvl) // 10
                db_ops.set_points(user.id, points)
            _msg = ""
            _log = ""
            if level_upgrade:
                _msg += f'Congratulations, {mention_html(user.id, user.full_name)}, you reached <b>level {1 + current_lvl}!</b>\nYou also earned <b>{points}</b> points!\nYou now have <b>{xp}</b> XP!'
                _log += f'{mention_html(user.id, user.full_name)} [User ID: <code>{user.id}</code>] reached <b>level {1 + current_lvl}</b>\nThey also earned <b>{points}</b> points\nThey now have <b>{xp}</b> XP'
            if streak_broken:
                _msg += f'\nOops, {mention_html(user.id, user.full_name)}, your daily streak was <b>reset</b>!\n'
                _log += f'\n{mention_html(user.id, user.full_name)} daily streak was <b>reset</b>\n'
            else:
                if extra_xp > 0:
                    _msg += f'\n{mention_html(user.id, user.full_name)}, you were granted <b>{extra_xp}</b> XP for your daily streak!\n'
                    _msg += f'You now have a <u>{int(user_details[2])} day streak</u>!'
                    _log += f'\n{mention_html(user.id, user.full_name)} [User ID: <code>{user.id}</code>] was granted <b>{extra_xp}</b> XP for their daily streak\nThey now have a <u>{int(user_details[2])} day streak</u>'
            if len(_msg.strip()) > 0:
                if user_details[-1] == 'Public':
                    context.bot.send_message(
                        chat.id, _msg.strip(), parse_mode=ParseMode.HTML)
                tg_ops.post_log(update, context, _log)


def reset_daily_xp(context: CallbackContext) -> None:
    print('Added job reset')
    try:
        daily_reset = context.bot_data['daily_reset']
    except KeyError:
        daily_reset = False
        context.bot_data['daily_reset'] = daily_reset
    d = datetime.now().astimezone(pytz.timezone('Asia/Kolkata')).strftime('%H')
    if int(d) == 0:
        if not daily_reset:
            print('Resetting daily XP now')
            data = db_ops.get_all_details()
            if len(data) > 0:
                for d in data:
                    db_ops.reset_daily_xp_granted(d[0])
                    db_ops.reset_daily_xp(d[0])
                context.bot.send_message(OWNER_ID, 'Daily XP has been reset')
            daily_reset = True
            context.bot_data['daily_reset'] = daily_reset
    else:
        context.bot_data['daily_reset'] = False
        print('Daily XP has not been reset!')


def leaderboards(update: Update, context: CallbackContext) -> None:
    chat = update.effective_chat
    msg = update.effective_message
    if len(update.message.text.split()) > 1:
        type = update.message.text.split()[1]
        if type == 'level':
            data = db_ops.get_lvl_leaderboard()
            if len(data) > 0:
                _msg = "<b>Top 5 scorers by level:</b>\n\n"
                for d in data:
                    if d[-2] == 'Off':
                        _msg += f'{d[-3]} [User ID: <code>{d[0]}</code>]: <b>Level {d[6]}</b>\n'
                    elif d[-2] == 'On':
                        _msg += f'{mention_html(d[0], str(d[-3]))}: <b>Level {d[6]}</b>\n'
            else:
                _msg = "<b>No data found in database!</b>"
        else:
            _msg = "<b>That is not a valid leaderboard type</b>"
    else:
        data = db_ops.get_leaderboard()
        if len(data) > 0:
            _msg = "<b>Top 5 scorers by XP earned:</b>\n\n"
            for d in data:
                if d[-2] == 'Off':
                    _msg += f'{d[-3]} [User ID: <code>{d[0]}</code>]: <b>{d[1]} XP</b>\n'
                elif d[-2] == 'On':
                    _msg += f'{mention_html(d[0], str(d[-3]))}: <b>{d[1]} XP</b>\n'
        else:
            _msg = "<b>No data found in database!</b>"
    context.bot.send_message(chat.id, _msg, parse_mode=ParseMode.HTML,
                             reply_to_message_id=msg.message_id, allow_sending_without_reply=True)
