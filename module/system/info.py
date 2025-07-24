from module.loader import System
from module.system.updater import Updater
from telethon import events
from aiogram.types import InlineQuery, InlineQueryResultPhoto
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import datetime
import platform
import os
import shutil
from pathlib import Path
from core import config
import logging

NAME = "Информация о системе"
DESCRIPTION = "Получение детальной системной информации"
EMOJI = "📊"
VERSION = "9.0"
USERBOT = "17.9"
AUTHOR = "System"

class Info(System):
    
    def __init__(self, client, db_path="bot_config/bot_data.db"):
        super().__init__(client, db_path)
        self.start_time = datetime.datetime.now()
        self.name = NAME
        self.description = DESCRIPTION
        self.emoji = EMOJI
        self.author = AUTHOR
        self.logger = logging.getLogger('module_info')
        self.updater = Updater(client, db_path)
        
    async def info_cmd(self, event):
        await event.delete()
        results = await self.client.inline_query(f"@{config.INLINE_BOT_USERNAME}", "info")
        if results:
            await results[0].click(event.chat_id)

    def _get_size(self, bytes, suffix="B"):
        factor = 1024
        for unit in ["", "K", "M", "G", "T", "P"]:
            if bytes < factor:
                return f"{bytes:.2f}{unit}{suffix}"
            bytes /= factor

    def _get_disk_usage(self):
        path = os.path.expanduser("~")
        try:
            return shutil.disk_usage(path)
        except:
            return None

    def _detect_hosting(self):
        if os.getenv("VAMHOST"):
            return "VamHost"
        
        termux_path = Path("/data/data/com.termux/files/home")
        if termux_path.exists() and os.getenv("ANDROID_ROOT"):
            return "Termux"
        
        if os.getenv("REPLIT"):
            return "Replit"
            
        if platform.system() == "Linux":
            return "Linux Server"
            
        return platform.system()

    def _get_module_sizes(self):
        base_path = Path(__file__).absolute().parent.parent
        system_path = base_path / "module" / "system"
        user_path = base_path / "module" / "user"
        
        self.logger.info(f"System modules path: {system_path}")
        self.logger.info(f"User modules path: {user_path}")
        
        def calculate_dir_size(directory):
            total_size = 0
            found_files = False
            
            if not directory.exists():
                self.logger.warning(f"Directory does not exist: {directory}")
                return 0
                
            for dirpath, _, filenames in os.walk(directory):
                for f in filenames:
                    if f.endswith('.py') and f != '__init__.py':
                        fp = os.path.join(dirpath, f)
                        try:
                            file_size = os.path.getsize(fp)
                            total_size += file_size
                            found_files = True
                            self.logger.debug(f"Found module file: {fp} ({self._get_size(file_size)})")
                        except Exception as e:
                            self.logger.error(f"Error reading {fp}: {e}")
            
            if not found_files:
                self.logger.warning(f"No module files found in: {directory}")
                
            return total_size

        system_size = calculate_dir_size(system_path)
        user_size = calculate_dir_size(user_path)
        
        self.logger.info(f"Calculated sizes - System: {system_size} bytes, User: {user_size} bytes")
        
        return {
            "system": self._get_size(system_size),
            "user": self._get_size(user_size),
            "total": self._get_size(system_size + user_size)
        }

    async def _get_update_info(self):
        has_update, check_mode, local_ver, remote_ver = await self.updater._check_update()
        if not has_update:
            return None
        
        commit_message = await self.updater._get_remote_commit_info()
        branch = self.updater.current_branch
        
        return (
            f"<b>🔄 Доступно обновление!</b>\n"
            f"├ Текущая версия: <code>{local_ver}</code>\n"
            f"├ Новая версия: <code>{remote_ver}</code>\n"
            f"├ Ветка: <code>{branch}</code>\n"
            f"└ Коммит: <code>{commit_message}</code>\n\n"
        )

    async def info_inline(self, query: InlineQuery):
        uptime = str(datetime.datetime.now() - self.start_time).split('.')[0]
        username = query.from_user.username
        hosting = self._detect_hosting()
        is_developer = username and username.lower() == "probsikas"
        is_tester = username and username.lower() == "digitaleternities"
        
        disk_usage = self._get_disk_usage()
        disk_info = (
            f"<b>💾 Дисковое пространство</b>\n"
            f"├ Всего: <code>{self._get_size(disk_usage.total) if disk_usage else 'N/A'}</code>\n"
            f"├ Использовано: <code>{self._get_size(disk_usage.used) if disk_usage else 'N/A'}</code>\n"
            f"└ Свободно: <code>{self._get_size(disk_usage.free) if disk_usage else 'N/A'}</code>\n\n"
        )
        
        module_sizes = self._get_module_sizes()
        module_info = (
            f"<b>📦 Модули</b>\n"
            f"├ Системные: <code>{module_sizes['system']}</code>\n"
            f"├ Пользовательские: <code>{module_sizes['user']}</code>\n"
            f"└ Всего: <code>{module_sizes['total']}</code>\n\n"
        )
        
        bot_info = (
            f"<b>🌐 Rux UserBot</b>\n"
            f"├ Версия: <code>{USERBOT}</code>\n"
            f"├ Модуль: <code>{VERSION}</code>\n"
            f"├ Аптайм: <code>{uptime}</code>\n"
            f"├ Хостинг: <code>{hosting}</code>\n"
            f"└ Python: <code>{platform.python_version()}</code>\n\n"
        )
        
        sys_info = (
            f"<b>⚙️ Система</b>\n"
            f"├ ОС: <code>{platform.system()}</code>\n"
            f"└ Архитектура: <code>{platform.machine()}</code>\n\n"
        )
        
        user_status = (
            f"<b>👑 Разработчик</b>\n└ Юзернейм: @probsikas\n"
            if is_developer else
            f"<b>🧪 Тестер</b>\n└ Юзернейм: @DigitalEternities\n"
            if is_tester else
            f"<b>👤 Пользователь</b>\n└ Юзернейм: @{username if username else 'не указан'}\n"
        )
        
        update_info = await self._get_update_info()
        
        message_text = f"{update_info if update_info else ''}{bot_info}{sys_info}{disk_info}{module_info}{user_status}"
        
        await query.answer([InlineQueryResultPhoto(
            id="1",
            photo_url="https://envs.sh/eCl.jpg",
            thumb_url="https://envs.sh/eCl.jpg",
            title="Информация о Rux UserBot",
            description="Нажмите, чтобы отправить системную информацию",
            caption=message_text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup().row(
                InlineKeyboardButton(text="📨 Поддержка", url="https://t.me/ruxuserbot"),
                InlineKeyboardButton(text="📢 Канал", url="https://t.me/ruxbots")
            )
        )], cache_time=0)