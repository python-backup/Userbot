from telethon import events
import platform
import subprocess
import re
import asyncio
from termcolor import colored
from module.loader import System

NAME = "Ping"
DESCRIPTION = "Проверка соединения с серверами Telegram"
EMOJI = "🏓"
VERSION = "1.2"
AUTHOR = "система"

class Ping(System):
    

    def __init__(self, client, db_path="bot_config/bot_data.db"):
        super().__init__(client, db_path)
        self.status_icons = {
            'normal': "🟢",
            'warning': "🟡", 
            'critical': "🔴"
        }
        self.name = NAME
        self.description = DESCRIPTION
        self.emoji = EMOJI
        self.version = VERSION
        self.author = AUTHOR

    async def ping_host(self, host):
        param = '-n' if platform.system().lower() == 'windows' else '-c'
        command = ['ping', param, '1', host]
        try:
            process = subprocess.run(command, capture_output=True, text=True, timeout=5)
            output = process.stdout
            if platform.system().lower() == 'windows':
                match = re.search(r"(?:time|время)=(\d+)\s*ms", output)
            else:
                match = re.search(r"time=([\d.]+)\s*ms", output)
            return (True, float(match.group(1))) if match else (True, None)
        except Exception as e:
            print(colored(f"Ping error: {e}", "red"))
            return False, None

    async def ping_cmd(self, event):
        try:
            await event.delete()
            target_host = "api.telegram.org"
            success, delay = await self.ping_host(target_host)
            
            if not success or delay is None:
                msg = await event.respond(f"⚠️ Не удалось измерить пинг до {target_host}")
                await asyncio.sleep(5)
                await msg.delete()
                return

            status = (self.status_icons['critical'] if delay > 280 else
                     self.status_icons['warning'] if delay > 200 else
                     self.status_icons['normal'])

            response = (f"{EMOJI} Пинг до {target_host}\n"
                      f"⏱ Задержка: {delay:.2f} мс {status}\n"
                      f"🔄 Проверка соединения с сервером Telegram")
            await event.respond(response)
            
        except Exception as e:
            msg = await event.respond(f"⚠️ Ошибка: {str(e)}")
            await asyncio.sleep(5)
            await msg.delete()