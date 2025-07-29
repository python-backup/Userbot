import importlib
import os
import inspect
from pathlib import Path
from termcolor import colored
import sqlite3
import asyncio
import re
from functools import wraps
from telethon import events
import importlib.util
import json
import hashlib
from typing import Dict, Optional, Tuple, Union, List, Any
from aiogram import Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InlineQuery
from aiogram.dispatcher.filters import BoundFilter

class AdminFilter(BoundFilter):
    key = 'is_admin'

    def __init__(self, is_admin: bool):
        self.is_admin = is_admin

    async def check(self, message: types.Message):
        return await self.check_admin(message)

    async def check_admin(self, message: types.Message) -> bool:
        user_id = message.from_user.id if hasattr(message, 'from_user') else None
        if not user_id:
            return False
            
        with sqlite3.connect(DATABASE_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM admins WHERE user_id=?", (user_id,))
            return cursor.fetchone() is not None


DEBUG_MODE = False
DATABASE_FILE = 'bot_config/bot_data.db'
USER_MODULES_DIR = 'User'

DEBUG = DEBUG_MODE

class LoaderSecurity:
    def __init__(self, db_path=DATABASE_FILE):
        self.db_path = db_path
        self._ensure_db_exists()
    
    def _ensure_db_exists(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS module_hashes (
                    file_path TEXT PRIMARY KEY,
                    file_hash TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS loader_lock (
                    locked INTEGER DEFAULT 0,
                    reason TEXT
                )
            """)
            conn.execute("""
                INSERT OR IGNORE INTO loader_lock (locked, reason) 
                VALUES (0, '')
            """)
    
    def calculate_file_hash(self, file_path: str) -> str:
        hasher = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                while chunk := f.read(4096):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception:
            return ""
    
    def load_hashes(self) -> Dict[str, str]:
        hashes = {}
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT file_path, file_hash FROM module_hashes")
                for file_path, file_hash in cursor.fetchall():
                    hashes[file_path] = file_hash
        except Exception:
            pass
        return hashes
    
    def save_hashes(self, hashes: Dict[str, str]) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM module_hashes")
                for file_path, file_hash in hashes.items():
                    conn.execute(
                        "INSERT INTO module_hashes (file_path, file_hash) VALUES (?, ?)",
                        (file_path, file_hash)
                    )
                conn.commit()
            return True
        except Exception:
            return False
    
    def is_locked(self) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT locked FROM loader_lock LIMIT 1")
                result = cursor.fetchone()
                return result and result[0] == 1
        except Exception:
            return False
    
    def lock_loader(self, reason: str = "") -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "UPDATE loader_lock SET locked = 1, reason = ?",
                    (reason,)
                )
                conn.commit()
            return True
        except Exception:
            return False
    
    def unlock_loader(self) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "UPDATE loader_lock SET locked = 0, reason = ''"
                )
                conn.commit()
            return True
        except Exception:
            return False
    
    def get_lock_reason(self) -> str:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT reason FROM loader_lock LIMIT 1")
                result = cursor.fetchone()
                return result[0] if result else "Неизвестная причина"
        except Exception:
            return "Неизвестная причина"

def verify_system_integrity(security: LoaderSecurity) -> Tuple[bool, str]:
    critical_files = [
        "main.py",
        "module/loader.py"
    ]
    
    system_dir = Path("module/system")
    if system_dir.exists():
        for file in system_dir.glob("*.py"):
            if file.name != "__init__.py":
                critical_files.append(str(file))
    
    current_hashes = security.load_hashes()
    changes = []
    missing_files = []
    
    for file in critical_files:
        if not os.path.exists(file):
            missing_files.append(file)
            continue
        
        current_hash = security.calculate_file_hash(file)
        if not current_hash:
            continue
            
        if file in current_hashes and current_hashes[file] != current_hash:
            changes.append(file)
    
    if missing_files and any(f in current_hashes for f in missing_files):
        return False, f"Критические файлы отсутствуют: {', '.join(missing_files)}"
    
    if changes:
        return False, f"Обнаружены изменения в файлах: {', '.join(changes)}"
    
    return True, "OK"

def save_current_hashes(security: LoaderSecurity):
    hashes = {}
    
    required_files = ["main.py", "module/loader.py"]
    for file in required_files:
        if os.path.exists(file):
            hashes[file] = security.calculate_file_hash(file)
    
    system_dir = Path("module/system")
    if system_dir.exists():
        for file in system_dir.glob("*.py"):
            if file.name != "__init__.py":
                hashes[str(file)] = security.calculate_file_hash(str(file))
    
    security.save_hashes(hashes)

class ModuleBase:
    PREFIX = "!"
    CONFIG_PATH = "bot_config/config.json"
    
    def __init__(self, client: Union['TelegramClient', 'Bot', 'Dispatcher'], db_path: str = DATABASE_FILE):
        self.client = client
        self.db_path = db_path
        self.security = LoaderSecurity(db_path)
        self._ensure_db_exists()
        self._load_prefix()
        self._commands = self._auto_discover_commands()
        self._inline_handlers = self._auto_discover_inline_handlers()
        self._callback_handlers = self._auto_discover_callback_handlers()
        self._is_hybrid = False
    
    def _ensure_db_exists(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS admins (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT
                )
            """)
    
    def _load_prefix(self):
        try:
            os.makedirs(os.path.dirname(self.CONFIG_PATH), exist_ok=True)
            
            if not os.path.exists(self.CONFIG_PATH):
                with open(self.CONFIG_PATH, 'w') as f:
                    json.dump({"prefix": self.PREFIX}, f)
                return
            
            with open(self.CONFIG_PATH, 'r') as f:
                config = json.load(f)
                self.PREFIX = config.get("prefix", self.PREFIX)
                
            if DEBUG:
                print(f"Загружен префикс из JSON: {self.PREFIX}")
                
        except Exception as e:
            print(f"Ошибка загрузки префикса из JSON: {e}")
    
    async def set_prefix(self, new_prefix: str) -> bool:
        if not new_prefix or len(new_prefix) > 3:
            return False
        
        try:
            config = {}
            if os.path.exists(self.CONFIG_PATH):
                with open(self.CONFIG_PATH, 'r') as f:
                    config = json.load(f)
            
            config["prefix"] = new_prefix
            
            with open(self.CONFIG_PATH, 'w') as f:
                json.dump(config, f, indent=4)
            
            self.PREFIX = new_prefix
            if DEBUG:
                print(f"Префикс изменен на: {self.PREFIX}")
            return True
            
        except Exception as e:
            print(f"Ошибка сохранения префикса: {e}")
            return False
    
    async def check_admin(self, event) -> bool:
        if isinstance(event, CallbackQuery):
            user_id = event.from_user.id
        elif hasattr(event, 'from_user'):
            user_id = event.from_user.id
        else:
            user_id = getattr(event, 'sender_id', None)
        
        if not user_id:
            return False
            
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM admins WHERE user_id=?", (user_id,))
            return cursor.fetchone() is not None
    
    def _auto_discover_commands(self) -> Dict[str, Dict]:
        commands = {}
        for name, method in inspect.getmembers(self, inspect.ismethod):
            if name.endswith('_cmd'):
                cmd_name = name[:-4]
                pattern = f'^{re.escape(self.PREFIX)}{cmd_name}(?: |$)(.*)?'
                
                method = self._admin_wrapper(method)
                
                commands[name] = {
                    'pattern': re.compile(pattern, re.IGNORECASE),
                    'method': method,
                    'doc': inspect.getdoc(method) or "",
                    'admin': True,
                    'name': cmd_name
                }
        return commands
    
    def _auto_discover_inline_handlers(self) -> Dict[str, Dict]:
        handlers = {}
        for name, method in inspect.getmembers(self, inspect.ismethod):
            if name.endswith('_inline'):
                handler_name = name[:-7]
                handlers[handler_name] = {
                    'method': method,
                    'doc': inspect.getdoc(method) or "",
                    'admin': True,
                    'name': handler_name
                }
        return handlers
    
    def _auto_discover_callback_handlers(self) -> Dict[str, Dict]:
        handlers = {}
        for name, method in inspect.getmembers(self, inspect.ismethod):
            if name.endswith('_callback'):
                handler_name = name[:-9]
                handlers[handler_name] = {
                    'method': method,
                    'doc': inspect.getdoc(method) or "",
                    'admin': True,
                    'name': handler_name
                }
        return handlers
    
    def _admin_wrapper(self, method):
        @wraps(method)
        async def wrapper(event):
            instance = getattr(method, '__self__', self)
            if not await instance.check_admin(event):
                if isinstance(event, CallbackQuery):
                    await event.answer("⛔ Недостаточно прав", show_alert=True)
                elif isinstance(event, InlineQuery):
                    await event.answer(
                        results=[],
                        switch_pm_text="⛔ Доступ только для админов",
                        switch_pm_parameter="admin_only",
                        cache_time=0
                    )
                elif hasattr(event, 'answer'):
                    await event.answer("⛔ Недостаточно прав", show_alert=True)
                else:
                    msg = await event.respond("⛔ Недостаточно прав")
                    await asyncio.sleep(3)
                    await msg.delete()
                return
            return await method(event)
        return wrapper
    
    def register_handlers(self, dp: Optional[Dispatcher] = None):
        if hasattr(self.client, 'add_event_handler'):
            for cmd in self._commands.values():
                handler = cmd['method']
                self.client.add_event_handler(
                    handler,
                    events.NewMessage(pattern=cmd['pattern'])
                )

        if dp is not None:
            for cmd in self._commands.values():
                method = cmd['method']
                dp.register_message_handler(
                    method,
                    commands=[cmd['name']]
                )
            
            for handler_name, handler in self._inline_handlers.items():
                method = handler['method']
                if handler['admin']:
                    method = self._admin_wrapper(method)
                
                async def inline_wrapper(query: InlineQuery, hname=handler_name, m=method):
                    if not query.query or query.query == hname or query.query.startswith(hname + ' '):
                        return await m(query)
                
                dp.register_inline_handler(
                    inline_wrapper,
                    lambda q, h=handler_name: not q.query or q.query == h or q.query.startswith(h + ' ')
                )
            
            for handler_name, handler in self._callback_handlers.items():
                method = handler['method']
                if handler['admin']:
                    method = self._admin_wrapper(method)
                
                async def callback_wrapper(call: CallbackQuery, hname=handler_name, m=method):
                    if call.data == hname or call.data.startswith(hname + '_'):
                        return await m(call)
                
                dp.register_callback_query_handler(
                    callback_wrapper,
                    lambda c, h=handler_name: c.data == h or c.data.startswith(h + '_'),
                    state='*'
                )

class System(ModuleBase):
    pass

class User(ModuleBase):
    pass

def load_all_modules(client_or_dp: Union['TelegramClient', 'Dispatcher'], 
                   db_path: str = DATABASE_FILE) -> Dict[str, Dict]:
    security = LoaderSecurity(db_path)
    
    if security.is_locked():
        lock_reason = security.get_lock_reason()
        print(colored(f"⛔ Загрузчик заблокирован. Причина: {lock_reason}", "red"))
        return {"system": {}, "user": {}}
    
    integrity_ok, integrity_msg = verify_system_integrity(security)
    if not integrity_ok:
        print(colored(f"⛔ Ошибка проверки целостности: {integrity_msg}", "red"))
        security.lock_loader(f"Обнаружены изменения: {integrity_msg}")
        return {"system": {}, "user": {}}
    
    base_dir = Path(__file__).parent
    modules = {"system": {}, "user": {}}
    success_message_printed = False
    
    is_aiogram = isinstance(client_or_dp, Dispatcher)
    dp = client_or_dp if is_aiogram else None
    client = client_or_dp if not is_aiogram else None
    
    for mtype, dir_name in [("system", "system"), ("user", "user")]:
        dir_path = base_dir / dir_name
        if dir_path.exists():
            loaded = _load_from_dir(client, dp, dir_path, mtype, db_path)
            modules[mtype].update(loaded)
            
            if loaded and not success_message_printed and not DEBUG:
                print(colored("\n✅ Бот успешно запустил все модули", "cyan"))
                success_message_printed = True
    
    if integrity_ok:
        save_current_hashes(security)
    
    if not is_aiogram:
        client.loaded_modules = modules
    
    return modules

def _load_from_dir(client: Optional['TelegramClient'],
                  dp: Optional[Dispatcher],
                  dir_path: Path,
                  expected_type: str,
                  db_path: str) -> Dict[str, Dict]:
    modules = {}
    
    for file in dir_path.glob("*.py"):
        if file.name.startswith("_"):
            continue
        
        module_name = file.stem
        try:
            spec = importlib.util.spec_from_file_location(
                f"module.{dir_path.name}.{module_name}", file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if obj.__module__ == module.__name__:
                    if issubclass(obj, (System, User, ModuleBase)):
                        module_class = obj(client if client else dp, db_path)
                        module_type = ("system" if issubclass(obj, System) 
                                     else "user" if issubclass(obj, User)
                                     else expected_type)
                        
                        module_class.register_handlers(dp)
                        
                        commands = [
                            f"{module_class.PREFIX}{cmd['name']} (admin)"
                            for cmd in module_class._commands.values()
                        ]
                        
                        inline_handlers = [
                            f"{handler['name']} (admin)" if handler['admin'] else handler['name']
                            for handler in module_class._inline_handlers.values()
                        ]
                        
                        callback_handlers = [
                            f"{handler['name']} (admin)" if handler['admin'] else handler['name']
                            for handler in module_class._callback_handlers.values()
                        ]
                        
                        modules[module_name] = {
                            'name': getattr(module, 'NAME', module_name),
                            'description': getattr(module, 'DESCRIPTION', ""),
                            'emoji': getattr(module, 'EMOJI', "🔹"),
                            'version': getattr(module, 'VERSION', "1.0"),
                            'author': getattr(module, 'AUTHOR', "Unknown"),
                            'commands': commands,
                            'inline_handlers': inline_handlers,
                            'callback_handlers': callback_handlers,
                            'type': module_type,
                            'status': '✅'
                        }
                        
                        if DEBUG:
                            print(colored(
                                f"✅ {modules[module_name]['emoji']} Загружен {module_type} модуль: "
                                f"{modules[module_name]['name']} "
                                f"(команды: {', '.join(commands)}, "
                                f"инлайн: {', '.join(inline_handlers)}, "
                                f"callback: {', '.join(callback_handlers)})",
                                "green"))
                        break
        
        except Exception as e:
            print(colored(f"❌ Ошибка загрузки {module_name}: {str(e)}", "red"))
            modules[module_name] = {
                'name': module_name,
                'description': f"Ошибка: {str(e)}",
                'emoji': "❌",
                'status': 'error',
                'type': 'unknown'
            }
    
    return modules