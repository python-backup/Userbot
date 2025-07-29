# module/system/installer.py
from telethon import events
import telethon.types
import os
import importlib.util
import asyncio
from termcolor import colored
from module.loader import System, User, load_all_modules
import sys
import inspect
import importlib

NAME = "Установка модулей"
DESCRIPTION = "установка модулей в rux"
EMOJI = "📦"
AUTHOR = "Система"
VERSION = "1.7"

class Installer(System):
    def __init__(self, client, db_path="bot_config/bot_data.db"):
        super().__init__(client, db_path)
        self.name = NAME
        self.description = DESCRIPTION 
        self.emoji = EMOJI 
        self.version = VERSION 
        self.author = AUTHOR
    
    async def install_cmd(self, event):
        if not await self.check_admin(event):
            msg = await event.respond("⛔ Только для администраторов")
            await asyncio.sleep(3)
            await msg.delete()
            return
            
        await event.delete()
        
        try:
            if not event.is_reply:
                msg = await event.respond("ℹ️ Ответьте этой командой на сообщение с файлом модуля (.py)")
                await asyncio.sleep(5)
                await msg.delete()
                return
                
            reply_msg = await event.get_reply_message()
            
            if not reply_msg.media or not hasattr(reply_msg.media, 'document'):
                msg = await event.respond("❌ В сообщении нет файла")
                await asyncio.sleep(3)
                await msg.delete()
                return
                
            doc = reply_msg.media.document
            file_name = None
            
            for attr in doc.attributes:
                if isinstance(attr, telethon.types.DocumentAttributeFilename):
                    file_name = attr.file_name
                    break
                    
            if not file_name or not file_name.endswith('.py'):
                msg = await event.respond("❌ Файл должен быть с расширением .py")
                await asyncio.sleep(3)
                await msg.delete()
                return
                
            user_modules_dir = os.path.join(os.path.dirname(__file__), '..', 'user')
            os.makedirs(user_modules_dir, exist_ok=True)
            
            module_path = os.path.join(user_modules_dir, file_name)
            module_name = file_name[:-3]
            
            await self._full_unload_module(module_name)
            
            await self.client.download_media(doc, file=module_path)
            
            if not self._validate_module(module_path):
                os.remove(module_path)
                msg = await event.respond("❌ Модуль не прошел проверку (должен наследовать User класс)")
                await asyncio.sleep(5)
                await msg.delete()
                return
                
            await self._install_dependencies(module_path, event)
            
            self.client.loaded_modules = load_all_modules(self.client, self.db_path)
            
            if module_name in self.client.loaded_modules.get('user', {}):
                await event.respond(f"✅ Модуль {file_name} успешно установлен и загружен!")
            else:
                await event.respond(f"⚠️ Модуль {file_name} установлен, но не загрузился")
            
        except Exception as e:
            await event.respond(f"⚠️ Ошибка: {str(e)}")
    
    async def _full_unload_module(self, module_name):
        if not hasattr(self.client, 'loaded_modules'):
            return
            
        await self._purge_all_handlers()
        
        user_modules_dir = os.path.join(os.path.dirname(__file__), '..', 'user')
        pyc_path = os.path.join(user_modules_dir, f"{module_name}.pyc")
        if os.path.exists(pyc_path):
            os.remove(pyc_path)
        
        full_module_name = f"module.user.{module_name}"
        if full_module_name in sys.modules:
            del sys.modules[full_module_name]
        
        if module_name in self.client.loaded_modules.get('user', {}):
            del self.client.loaded_modules['user'][module_name]
        
        import gc
        gc.collect()
    
    async def _purge_all_handlers(self):
        if not hasattr(self.client, 'list_event_handlers'):
            return
            
        handlers = self.client.list_event_handlers()
        for handler in handlers:
            if isinstance(handler, events.NewMessage):
                try:
                    self.client.remove_event_handler(handler.callback)
                except:
                    pass
        
        if hasattr(self.client, '_event_builders'):
            self.client._event_builders.clear()
    
    def _validate_module(self, module_path):
        try:
            parent_dir = os.path.dirname(os.path.dirname(module_path))
            sys.path.insert(0, parent_dir)
            
            spec = importlib.util.spec_from_file_location("user_module", module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            for name, obj in vars(module).items():
                if (isinstance(obj, type) and 
                    issubclass(obj, User) and 
                    obj is not User and 
                    obj.__module__ == "user_module"):
                    return True
            return False
        except Exception as e:
            print(f"Validation error: {e}")
            return False
        finally:
            if parent_dir in sys.path:
                sys.path.remove(parent_dir)
            
    async def _install_dependencies(self, module_path, event):
        try:
            with open(module_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if 'import ' not in content and 'from ' not in content:
                return
                
            dependencies = set()
            if 'import requests' in content:
                dependencies.add('requests')
            if 'import numpy' in content:
                dependencies.add('numpy')
            if 'import pandas' in content:
                dependencies.add('pandas')
                
            if dependencies:
                status = await event.respond(f"🔍 Обнаружены зависимости: {', '.join(dependencies)}")
                try:
                    import pip
                    for dep in dependencies:
                        pip.main(['install', dep])
                    await status.edit(f"✅ Зависимости установлены: {', '.join(dependencies)}")
                except:
                    await status.edit("⚠️ Не удалось установить зависимости. Установите их вручную")
                await asyncio.sleep(5)
                await status.delete()
        except:
            pass