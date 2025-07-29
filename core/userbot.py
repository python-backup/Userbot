import os
import random
import string
import sqlite3
import time
from termcolor import colored
from telethon import TelegramClient, events, errors
from typing import Dict, Optional, List, Any
from module.loader import load_all_modules, ModuleBase, DATABASE_FILE as LOADER_DB_FILE
from core.config import BOT_SESSION_PREFIX, DATABASE_FILE as CORE_DB_FILE
from core.database import ensure_db_exists, migrate_db
from core.inline_bot import create_inline_bot, run_inline_bot

DATABASE_FILE = CORE_DB_FILE or LOADER_DB_FILE or 'bot_data.db'

def generate_session_name() -> str:
    chars = string.ascii_uppercase + string.digits
    return f"RUX_USERBOT_{''.join(random.choice(chars) for _ in range(6))}"

def add_session(api_id: int, api_hash: str, phone: str, password: str = None) -> Optional[Dict]:
    session_name = generate_session_name()
    try:
        with sqlite3.connect(DATABASE_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO telegram_config (api_id, api_hash, phone_number, session_name, password) VALUES (?, ?, ?, ?, ?)",
                (api_id, api_hash, phone, session_name, password)
            )
            conn.commit()
            return {
                'session_id': cursor.lastrowid,
                'session_name': session_name,
                'phone': phone,
                'api_id': api_id,
                'api_hash': api_hash,
                'password': password
            }
    except sqlite3.Error as e:
        print(colored(f"Ошибка добавления сессии: {e}", "red"))
        return None

async def setup_userbot_session() -> bool:
    print(colored("\nНастройка юзер-бота:", "cyan"))
    try:
        api_id = int(input("Введите API ID: ").strip())
        api_hash = input("Введите API Hash: ").strip()
        phone = input("Введите номер телефона (с кодом страны): ").strip()
        password = input("Введите пароль 2FA (если есть, иначе Enter): ").strip() or None
        
        session_data = add_session(api_id, api_hash, phone, password)
        if not session_data:
            return False
            
        print(colored(
            f"\nСоздана новая сессия: {session_data['session_name']}\n"
            f"API ID: {session_data['api_id']}\n"
            f"Номер: {session_data['phone']}",
            "green"
        ))
        return True
    except ValueError as e:
        print(colored(f"Ошибка ввода данных: {e}", "red"))
        return False
    except Exception as e:
        print(colored(f"Неожиданная ошибка: {e}", "red"))
        return False

async def run_userbot_session(session_data: Dict):
    ensure_db_exists()
    migrate_db()
    
    session_file = f"{BOT_SESSION_PREFIX}{session_data['session_name']}"
    client = TelegramClient(
        session_file,
        session_data['api_id'],
        session_data['api_hash']
    )
    
    try:
        await client.connect()
        if not await client.is_user_authorized():
            print(colored(f"\nАвторизация сессии {session_data['session_name']}...", "yellow"))
            
            if os.path.exists(f"{session_file}.session"):
                await client.start(phone=lambda: session_data['phone'])
            else:
                sent_code = await client.send_code_request(session_data['phone'])
                print(colored(f"Код подтверждения отправлен (тип: {sent_code.type})", "yellow"))
                
                code = input(colored("Введите код из Telegram: ", "yellow")).strip()
                try:
                    await client.sign_in(session_data['phone'], code, password=session_data.get('password'))
                except errors.SessionPasswordNeededError:
                    password = session_data.get('password') or input(colored("Введите пароль 2FA: ", "yellow"))
                    await client.sign_in(password=password)
        
        if not client.is_connected():
            await client.connect()
        
        me = await client.get_me()
        print(colored(f"\nСессия {session_data['session_name']} запущена как @{me.username}", "green"))
        
        with sqlite3.connect(DATABASE_FILE) as conn:
            conn.execute(
                "INSERT OR IGNORE INTO admins (user_id, username, session_id) VALUES (?, ?, ?)",
                (me.id, me.username, session_data['session_id'])
            )
            conn.commit()
        
        from core.inline_bot import setup_inline_bot
        if not await setup_inline_bot():
            print(colored("\nСоздаем нового инлайн-бота...", "cyan"))
            if await create_inline_bot(client):
                await run_inline_bot()
        
        loaded_modules = load_all_modules(client, DATABASE_FILE)
        print(colored(
            f"\nЗагружено модулей:\n"
            f"Системных: {len(loaded_modules['system'])}\n"
            f"Пользовательских: {len(loaded_modules['user'])}",
            "cyan"
        ))
        
        await client.run_until_disconnected()
        
    except Exception as e:
        print(colored(f"Ошибка в сессии {session_data['session_name']}: {str(e)}", "red"))
    finally:
        if client.is_connected():
            await client.disconnect()