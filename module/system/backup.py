import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from telethon import types
from module.loader import ModuleBase
import zipfile

class BackupModule(ModuleBase):
    
    NAME = "Backup"
    DESCRIPTION = "Модуль для работы с бэкапами"
    EMOJI = "💾"
    VERSION = "1.1"  # Обновили версию
    
    async def backup_cmd(self, event):

        args = event.pattern_match.group(1).strip().split()
        
        if not args:
            await event.respond("ℹ️ Укажите имя файла для бэкапа\nПример: `!backup main.py`")
            return
            
        source_file = args[0]
        dest_name = args[1] if len(args) > 1 else source_file
        
        if not os.path.exists(source_file):
            await event.respond(f"⛔ Файл {source_file} не найден")
            return
            
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_file = os.path.join(temp_dir, dest_name)
                shutil.copy2(source_file, temp_file)
                await event.respond(
                    f"📁 Бэкап файла `{source_file}`",
                    file=temp_file
                )
                if self.DEBUG:
                    print(f"Отправлен бэкап файла: {source_file}")
        except Exception as e:
            await event.respond(f"⛔ Ошибка при создании бэкапа: {str(e)}")
            if self.DEBUG:
                print(f"Ошибка в backup_cmd: {str(e)}")
    
    async def backup_module_cmd(self, event):

        args = event.pattern_match.group(1).strip()
        
        if not args:
            await event.respond("ℹ️ Укажите имя модуля для бэкапа\nПример: `!backup_module backup`")
            return
            
        module_name = args + '.py'
        system_path = os.path.join("module", "system", module_name)
        user_path = os.path.join("module", "user", module_name)
        
        source_file = None
        if os.path.exists(system_path):
            source_file = system_path
        elif os.path.exists(user_path):
            source_file = user_path
        else:
            await event.respond(f"⛔ Модуль {module_name} не найден ни в system, ни в user модулях")
            return
            
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_file = os.path.join(temp_dir, module_name)
                shutil.copy2(source_file, temp_file)
                await event.respond(
                    f"📦 Бэкап модуля `{module_name}`",
                    file=temp_file
                )
                if self.DEBUG:
                    print(f"Отправлен бэкап модуля: {module_name}")
        except Exception as e:
            await event.respond(f"⛔ Ошибка при создании бэкапа модуля: {str(e)}")
            if self.DEBUG:
                print(f"Ошибка в backup_module_cmd: {str(e)}")
    
    async def backup_all_cmd(self, event):
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                zip_name = f"bot_backup_{timestamp}.zip"
                zip_path = os.path.join(temp_dir, zip_name)
                
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    if os.path.exists("main.py"):
                        zipf.write("main.py", "main.py")
                    
                    if os.path.exists("bot_config"):
                        for root, dirs, files in os.walk("bot_config"):
                            for file in files:
                                file_path = os.path.join(root, file)
                                arcname = os.path.relpath(file_path, start=".")
                                zipf.write(file_path, arcname)
                    
                    system_dir = os.path.join("module", "system")
                    if os.path.exists(system_dir):
                        for root, dirs, files in os.walk(system_dir):
                            for file in files:
                                if file.endswith('.py') and not file.startswith('__'):
                                    file_path = os.path.join(root, file)
                                    arcname = os.path.relpath(file_path, start=".")
                                    zipf.write(file_path, arcname)
                    
                    user_dir = os.path.join("module", "user")
                    if os.path.exists(user_dir):
                        for root, dirs, files in os.walk(user_dir):
                            for file in files:
                                if file.endswith('.py') and not file.startswith('__'):
                                    file_path = os.path.join(root, file)
                                    arcname = os.path.relpath(file_path, start=".")
                                    zipf.write(file_path, arcname)
                
                await event.respond(
                    "📦 Полный бэкап бота",
                    file=zip_path
                )
                
                if self.DEBUG:
                    print("Отправлен полный бэкап бота")
                    
        except Exception as e:
            await event.respond(f"⛔ Ошибка при создании полного бэкапа: {str(e)}")
            if self.DEBUG:
                print(f"Ошибка в backup_all_cmd: {str(e)}")