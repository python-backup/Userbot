from telethon import events
import sqlite3
from termcolor import colored
from module.loader import System
import asyncio

NAME = "*Администрирование"
DESCRIPTION = "Управление правами пользователей️"
EMOJI = "🔐"
VERSION = "1.0"
AUTHOR = "система"
    
class AdminGrant(System):
    def __init__(self, client, db_path="bot_config/bot_data.db"):
        super().__init__(client, db_path)
        self.name = NAME
        self.description = DESCRIPTION 
        self.emoji = EMOJI
        self.version = VERSION 
        self.author = AUTHOR

    async def setadmin_cmd(self, event):
        await event.delete()
        
        target = await self._get_target_user(event)
        if not target:
            msg = await event.respond("❌ Укажите пользователя (ответом или username/id)")
            await asyncio.sleep(5)
            await msg.delete()
            return

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO admins (user_id, username) VALUES (?, ?)",
                (target.id, target.username or target.first_name)
            )
            conn.commit()

        await event.respond(
            f"✅ Пользователь {target.first_name} "
            f"(ID: {target.id}) теперь администратор"
        )

    async def deladmin_cmd(self, event):
        await event.delete()
        
        target = await self._get_target_user(event)
        if not target:
            msg = await event.respond("❌ Укажите пользователя (ответом или username/id)")
            await asyncio.sleep(5)
            await msg.delete()
            return

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM admins WHERE user_id=?", (target.id,))
            conn.commit()

            if cursor.rowcount > 0:
                await event.respond(f"✅ Пользователь {target.first_name} больше не администратор")
            else:
                await event.respond("ℹ️ Этот пользователь не был администратором")

    async def isadmin_cmd(self, event):
        is_admin = await self.check_admin(event)
        await event.respond("✅ Вы администратор" if is_admin else "⛔ Вы не администратор")

    async def _get_target_user(self, event):
        args = event.pattern_match.group(1)
        
        if event.is_reply:
            replied = await event.get_reply_message()
            return replied.sender
        
        if args:
            try:
                return await self.client.get_entity(args.strip())
            except ValueError:
                return None
        return None