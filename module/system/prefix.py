from module.loader import System
from telethon import events
import asyncio
import sys
import os

NAME = "смена префикса"
DESCRIPTION = "Изменение символа"
EMOJI = "⚙️"
AUTHOR = "system"

class setprefix(System):
    def __init__(self, client, db_path="bot_config/bot_data.db"):
        super().__init__(client, db_path)
        self.name = NAME
        self.description = DESCRIPTION
        self.emoji = EMOJI
        self.author = AUTHOR
    
    async def setpref_cmd(self, event):
        if not await self.check_admin(event):
            msg = await event.respond("⛔ Недостаточно прав")
            await asyncio.sleep(3)
            await msg.delete()
            return

        args = event.pattern_match.group(1)
        
        if args is None:
            await event.respond(f"ℹ️ Текущий префикс: `{self.PREFIX}`\n"
                              f"Пример: `{self.PREFIX}setpref .`")
            return
        
        new_prefix = args.strip()
        
        if not new_prefix:
            await event.respond("❌ Не указан новый префикс")
            return
        
        if len(new_prefix) > 3:
            await event.respond("❌ Префикс не может быть длиннее 3 символов")
            return
        
        if ' ' in new_prefix:
            await event.respond("❌ Префикс не может содержать пробелы")
            return
        
        success = await self.set_prefix(new_prefix)
        if not success:
            await event.respond("❌ Ошибка сохранения префикса")
            return
        
        await event.respond(f"✅ Префикс изменен на `{new_prefix}`\n"
                          "🔄 Перезагружаю бота...")
        
        python = sys.executable
        os.execl(python, python, *sys.argv)