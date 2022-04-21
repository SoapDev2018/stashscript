from dotenv import load_dotenv
import os
from telegram.ext import Updater

load_dotenv('config.env')


def get_config(name: str) -> str:
    return os.environ[name]


try:
    BOT_TOKEN = get_config('BOT_TOKEN')
    DONATORS_GROUP_ID = get_config('DONATORS_GROUP_ID')
    DB_FILENAME = get_config('DB_FILENAME')
    CURATORS_GROUP_ID = get_config('CURATORS_GROUP_ID')
    HW_GROUP_ID = get_config('HW_GROUP_ID')
    HW_LOG_CHANNEL_ID = get_config('HW_LOG_CHANNEL_ID')
    IV_GROUP_ID = get_config('IV_GROUP_ID')
    STREAK_DB_FILENAME = get_config('STREAK_DB_FILENAME')
    OWNER_ID = get_config('OWNER_ID')
    BOT_LOG_CHANNEL_ID = get_config('BOT_LOG_CHANNEL_ID')
    TRANSACTIONS_DB_FILENAME = get_config('TRANSACTIONS_DB_FILENAME')
except KeyError as e:
    print('One or more required env variables are missing, exiting...')
    exit(1)

try:
    DONATORS_GROUP_ID = int(DONATORS_GROUP_ID)
except ValueError as e:
    print('Donators\' group ID should be an integer')
    exit(1)

try:
    CURATORS_GROUP_ID = int(CURATORS_GROUP_ID)
except ValueError as e:
    print('Curator\'s group ID should be an integer')
    exit(1)

try:
    HW_GROUP_ID = int(HW_GROUP_ID)
except ValueError as e:
    print('HW group ID should be an integer')
    exit(1)

try:
    HW_LOG_CHANNEL_ID = int(HW_LOG_CHANNEL_ID)
except ValueError as e:
    print('HW log channel ID should be an integer')
    exit(1)

try:
    IV_GROUP_ID = int(IV_GROUP_ID)
except ValueError:
    print('IV_GROUP_ID must be an integer')
    exit(1)

try:
    OWNER_ID = int(OWNER_ID)
except ValueError as e:
    print('OWNER_ID must be an integer')
    exit(1)

try:
    BOT_LOG_CHANNEL_ID = int(BOT_LOG_CHANNEL_ID)
except ValueError:
    print('BOT_LOG_CHANNEL_ID must be an integer')
    exit(1)

AUTH_CHATS = [DONATORS_GROUP_ID] + [CURATORS_GROUP_ID] + [-1001668132824]
updater = Updater(token=BOT_TOKEN)
bot = updater.bot
dispatcher = updater.dispatcher
