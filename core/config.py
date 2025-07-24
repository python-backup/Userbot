import os
from typing import Final, Optional

BOT_CONFIG_DIR: Final = 'bot_config'
if not os.path.exists(BOT_CONFIG_DIR):
    os.makedirs(BOT_CONFIG_DIR)

DATABASE_FILE: Final = os.path.join(BOT_CONFIG_DIR, 'bot_data.db')
BOT_SESSION_PREFIX: Final = os.path.join(BOT_CONFIG_DIR, 'session_')
USER_MODULES_DIR: Final = 'User'
INLINE_BOT_SCRIPT: Final = 'inline.py'
DEBUG_MODE: Final = False

UPDATE_CHANNEL = -1002264100781
UPDATE_CODE = "1010"

INLINE_BOT_USERNAME: Final[Optional[str]] = None
try:
    from core.database import get_inline_bot_username
    INLINE_BOT_USERNAME = get_inline_bot_username() or None
except:
    pass
print(INLINE_BOT_USERNAME)