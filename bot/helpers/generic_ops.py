import hashlib
from datetime import datetime

import pytz

from bot import AUTH_CHATS, HW_GROUP_ID, IV_GROUP_ID
AUTH_CHATS = AUTH_CHATS + [HW_GROUP_ID, IV_GROUP_ID]


def get_auth_chat() -> list:
    return AUTH_CHATS


def generate_hash() -> str:
    dt = datetime.now().astimezone(pytz.timezone(
        'Asia/Kolkata')).strftime("%m/%d/%Y, %H:%M:%S:%f")
    return hashlib.sha224(dt.encode()).hexdigest()
