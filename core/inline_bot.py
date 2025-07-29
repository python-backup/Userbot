import subprocess
import sys
import time
import asyncio
from termcolor import colored
import os
from typing import Optional
from aiogram import Bot
from core.config import INLINE_BOT_SCRIPT, INLINE_BOT_USERNAME
from core.database import (
    get_inline_bot_token, 
    add_inline_bot,
    get_inline_bot_username,
    update_inline_bot_username
)

async def setup_inline_bot() -> bool:
    token = get_inline_bot_token()
    if token:
        print(colored("\nНайден токен инлайн-бота в базе данных", "green"))
        if not get_inline_bot_username():
            print(colored("Предупреждение: username бота не найден в базе данных", "yellow"))
        return True
    return False

async def create_inline_bot(client: 'TelegramClient') -> bool:
    print(colored("\n⌛ Создание инлайн-бота через BotFather...", "cyan"))
    
    try:
        async with client.conversation('BotFather', timeout=60) as conv:
            await conv.send_message('/newbot')
            await asyncio.sleep(3)
            response = await conv.get_response()
            
            if "Alright" not in response.text:
                print(colored("❌ Не удалось начать создание бота. Ответ BotFather:", "red"))
                print(colored(response.text, "yellow"))
                return False
            
            bot_name = f"RUX_Inline_{int(time.time())}"
            await conv.send_message(bot_name)
            await asyncio.sleep(3)
            response = await conv.get_response()
            
            if "Good" not in response.text:
                print(colored("❌ Не удалось задать имя бота. Ответ BotFather:", "red"))
                print(colored(response.text, "yellow"))
                return False
            
            bot_username = f"rux_inline_{int(time.time())}_bot"
            await conv.send_message(bot_username)
            await asyncio.sleep(5)
            response = await conv.get_response()
            
            print(colored("📄 Ответ BotFather при создании бота:", "blue"))
            print(colored(response.text, "yellow"))
            
            token = None
            if '`' in response.text:
                token = response.text.split('`')[1].split('`')[0]
            else:
                for line in response.text.split('\n'):
                    if "token" in line.lower() and ":" in line:
                        token_part = line.split(':')[-1].strip().replace('`', '')
                        if ':' in token_part and token_part.split(':')[0].isdigit() and len(token_part.split(':')[1]) > 0:
                            token = token_part
                            break
            
            if not token:
                print(colored("❌ Не удалось найти токен в ответе. Полный ответ:", "red"))
                print(colored(response.text, "yellow"))
                return False
            
            if not (token.count(':') == 1 and token.split(':')[0].isdigit() and len(token.split(':')[1]) > 0):
                print(colored(f"❌ Некорректный формат токена: {token}", "red"))
                return False
            
            if add_inline_bot(token, bot_username):
                await conv.send_message("/setinline")
                await asyncio.sleep(3)
                await conv.send_message(f"@{bot_username}")
                await asyncio.sleep(3)
                await conv.send_message("rux")
                await asyncio.sleep(3)
                
                await conv.send_message("/setuserpic")
                await asyncio.sleep(3)
                await conv.send_message(f"@{bot_username}")
                await asyncio.sleep(3)
                await conv.send_file("core/data/image.jpg")
                print(colored(f"✅ Инлайн-бот @{bot_username} успешно создан! Токен: {token}", "green"))
                return True
            else:
                print(colored("❌ Не удалось сохранить токен в базе данных", "red"))
                return False
            
    except Exception as e:
        print(colored(f"❌ Ошибка создания бота: {e}", "red"))
        return False

async def run_inline_bot() -> Optional[subprocess.Popen]:
    try:
        if not os.path.exists(INLINE_BOT_SCRIPT):
            raise FileNotFoundError(f"Файл {INLINE_BOT_SCRIPT} не найден")
        
        process = subprocess.Popen(
            [sys.executable, INLINE_BOT_SCRIPT],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
            text=True
        )
        
        print(colored("🟢 Инлайн-бот запущен в отдельном процессе", "green"))
        return process
        
    except Exception as e:
        print(colored(f"❌ Ошибка запуска инлайн-бота: {e}", "red"))
        return None

def get_inline_bot() -> Optional[Bot]:
    token = get_inline_bot_token()
    if token:
        return Bot(token=token)
    return None

async def update_bot_username(new_username: str) -> bool:
    if not new_username.startswith('@'):
        new_username = f"@{new_username}"
    
    if update_inline_bot_username(new_username):
        print(colored(f"✅ Username бота обновлен: {new_username}", "green"))
        return True
    else:
        print(colored("❌ Не удалось обновить username бота", "red"))
        return False