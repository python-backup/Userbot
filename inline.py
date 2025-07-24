from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
import logging
import os
from core.database import get_inline_bot_token
from module.loader import load_all_modules

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

BOT_TOKEN = get_inline_bot_token()

async def on_startup(dp: Dispatcher):
    logger.info("Бот запущен")
    load_all_modules(dp)

async def on_shutdown(dp: Dispatcher):
    logger.info("Бот остановлен")

if __name__ == '__main__':
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(bot)
    
    executor.start_polling(
        dp,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True
    )