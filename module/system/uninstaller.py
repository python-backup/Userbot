from module.loader import System, load_all_modules
from telethon import events
import os
import asyncio
import sys
from termcolor import colored
import inspect

NAME = "очистка"
DESCRIPTION = "Удаление модулей"
EMOJI = "🧹"
VERSION = "1.0"
AUTHOR = "система"

class Uninstaller(System):
    def __init__(self, client, db_path="bot_config/bot_data.db"):
        super().__init__(client, db_path)
        self.name = NAME
        self.description = DESCRIPTION 
        self.emoji = EMOJI
        self.version = VERSION 
        self.author = AUTHOR

    async def uninstall_cmd(self, event):
        if not await self.check_admin(event):
            msg = await event.respond("⛔ Только для администраторов")
            await asyncio.sleep(3)
            await msg.delete()
            return
            
        args = event.pattern_match.group(1)
        if not args:
            msg = await event.respond("ℹ️ Укажите название модуля из помощи: !uninstall <название>")
            await asyncio.sleep(5)
            await msg.delete()
            return
            
        module_name = args.strip().lower()
        await self._uninstall_module_by_display_name(event, module_name)
    
    async def _uninstall_module_by_display_name(self, event, display_name):
        user_modules_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            'user'
        )
        
        modules = self.client.loaded_modules.get('user', {})
        
        found_module = None
        for file_name, module_data in modules.items():
            if module_data['name'].lower() == display_name:
                found_module = file_name
                break
        
        if not found_module:
            await event.respond(f"❌ Модуль с названием '{display_name}' не найден")
            return
            
        if found_module in ['installer', 'uninstaller']:
            await event.respond("❌ Нельзя удалять системные модули!")
            return
            
        module_path = os.path.join(user_modules_dir, f"{found_module}.py")
        
        if not os.path.exists(module_path):
            await event.respond(f"❌ Файл модуля '{found_module}.py' не найден")
            return
            
        try:
            await self._purge_all_handlers()

            os.remove(module_path)
            pyc_path = os.path.join(user_modules_dir, f"{found_module}.pyc")
            if os.path.exists(pyc_path):
                os.remove(pyc_path)

            self.client.loaded_modules = load_all_modules(self.client, self.db_path)

            await event.respond(f"✅ Модуль '{module_data['name']}' (файл: {found_module}.py) полностью удален!")
            print(colored(f"Модуль {found_module} удалён, обработчики перезагружены", "green"))
            
        except Exception as e:
            await event.respond(f"⚠️ Ошибка при удалении: {str(e)}")
            print(colored(f"Ошибка удаления {found_module}: {str(e)}", "red"))

    async def _purge_all_handlers(self):

        handlers = self.client.list_event_handlers()
        
        for handler in handlers:
            if isinstance(handler, events.NewMessage):
                try:
                    self.client.remove_event_handler(handler.callback)
                except Exception as e:
                    print(colored(f"Ошибка удаления обработчика: {str(e)}", "yellow"))
        
        if hasattr(self.client, '_event_builders'):
            self.client._event_builders.clear()