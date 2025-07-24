# module/system/restart.py
from telethon import events
import os
import asyncio
import sys
import datetime
import json
from module.loader import System
from termcolor import colored


NAME = "Перезагрузка"
DESCRIPTION = "Перезапуск систем rux"
EMOJI = "♻"
AUTHOR = "система"
RESTART_DATA_FILE = "restart_data.json"


class Restart(System):
    def __init__(self, client, db_path="bot_config/bot_data.db"):
        super().__init__(client, db_path)
        self.name = NAME
        self.description = DESCRIPTION
        self.emoji = EMOJI
        self.author = AUTHOR
        
        if os.path.exists(RESTART_DATA_FILE):
            asyncio.create_task(self.on_restart_complete())

    async def restart_cmd(self, event):
        try:
            await event.delete()
            start_time = datetime.datetime.now()
            restart_msg = await event.respond("🔄 Перезапуск системы...")
            
            restart_data = {
                "start_time": start_time.isoformat(),
                "chat_id": event.chat_id,
                "msg_id": restart_msg.id
            }
            
            with open(RESTART_DATA_FILE, "w") as f:
                json.dump(restart_data, f)
            
            await asyncio.sleep(1)
            os.execl(sys.executable, sys.executable, *sys.argv)
            
        except Exception as e:
            await event.respond(f"⚠️ Ошибка при перезагрузке: {str(e)}")

    def format_duration(self, duration):
        total_seconds = duration.total_seconds()
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = int(total_seconds % 60)
        
        parts = []
        if hours > 0:
            parts.append(f"{hours} час" + ("ов" if hours > 1 else ""))
        if minutes > 0:
            parts.append(f"{minutes} минут" + ("у" if minutes == 1 else "ы" if 1 < minutes < 5 else ""))
        if seconds > 0 or not parts:
            parts.append(f"{seconds} секунд" + ("у" if seconds == 1 else "ы" if 1 < seconds < 5 else ""))
        
        return ' '.join(parts)

    async def on_restart_complete(self):
        try:
            with open(RESTART_DATA_FILE, "r") as f:
                restart_data = json.load(f)
            os.remove(RESTART_DATA_FILE)
            
            start_time = datetime.datetime.fromisoformat(restart_data["start_time"])
            chat_id = restart_data["chat_id"]
            end_time = datetime.datetime.now()
            reboot_duration = end_time - start_time
            
            uptime_str = self.format_duration(reboot_duration)
            
            try:
                await self.client.send_message(
                    chat_id,
                    f"👍 Юзербот полностью загружен! \nᵔᴥᵔ\n"
                    f"Полная перезагрузка заняла: {uptime_str}\n"
                )
                
                try:
                    await self.client.delete_messages(chat_id, restart_data["msg_id"])
                except:
                    pass
                    
            except Exception as e:
                dialogs = await self.client.get_dialogs(limit=1)
                if dialogs:
                    await self.client.send_message(
                        dialogs[0].entity,
                        f"👍 Юзербот полностью загружен! \nᵔᴥᵔ\n"
                        f"Полная перезагрузка заняла: {uptime_str}\n"
                    )
                
        except Exception as e:
            print(colored(f"Restart notification error: {e}", "red"))