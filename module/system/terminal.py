import os
import sys
import traceback
import subprocess
from pathlib import Path
from typing import Optional

from telethon import events
from telethon.tl.types import Message

from module.loader import ModuleBase

NAME = "Terminal"
DESCRIPTION = "Выполнение команд в терминале"
EMOJI = "💻"
VERSION = "1.2"
AUTHOR = "system"

class Terminal(ModuleBase):

    def __init__(self, client, db_path="bot_config/bot_data.db"):
        super().__init__(client, db_path)
        self.current_dir = str(Path.home())
        self.name = NAME
        self.description = DESCRIPTION
        self.emoji = EMOJI
        self.author = AUTHOR
        self.version = VERSION
        self.MAX_MESSAGE_LENGTH = 400

    async def _send_long_message(self, event: Message, text: str):
        while text:
            chunk = text[:self.MAX_MESSAGE_LENGTH]
            text = text[self.MAX_MESSAGE_LENGTH:]
            await event.respond(chunk, parse_mode="markdown")

    async def term_cmd(self, event: Message):
        if not (await self.check_admin(event)):
            return
        
        command = event.pattern_match.group(1)
        if not command:
            await event.respond("❌ Укажите команду для выполнения")
            return
        
        try:
            if command.startswith("cd "):
                await self._handle_cd(event, command[3:])
                return
            elif command == "cd":
                await self._handle_cd(event, str(Path.home()))
                return
            elif command == "pwd":
                await event.respond(f"Текущая директория: `{self.current_dir}`")
                return
            elif command.startswith("ls"):
                await self._handle_ls(event, command[2:].strip())
                return
            
            process = subprocess.Popen(
                command,
                shell=True,
                cwd=self.current_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate()
            
            result = ""
            if stdout:
                result += f"Вывод:\n{stdout}\n"
            if stderr:
                result += f"Ошибки:\n{stderr}\n"
            if not result:
                result = "Команда выполнена, но вывод пуст"
            
            header = (
                f"📟 **Terminal**\n"
                f"**Директория:** `{self.current_dir}`\n"
                f"**Команда:** `{command}`\n\n"
                f"**Результат:**\n```"
            )
            footer = "```"
            
            max_result_length = self.MAX_MESSAGE_LENGTH - len(header) - len(footer)
            if len(result) > max_result_length:
                await event.respond(header + "Результат слишком длинный, отправляю частями..." + footer)
                await self._send_long_message(event, result)
            else:
                await event.respond(header + result + footer, parse_mode="markdown")
            
        except Exception as e:
            error_msg = f"❌ Ошибка выполнения команды:\n```{str(e)}\n{traceback.format_exc()}```"
            await self._send_long_message(event, error_msg)

    async def _handle_cd(self, event: Message, directory: str):
        try:
            new_dir = str(Path(self.current_dir).joinpath(directory).resolve())
            if not Path(new_dir).is_dir():
                await event.respond(f"❌ Директория не существует: `{new_dir}`")
                return
            
            self.current_dir = new_dir
            await event.respond(f"✅ Текущая директория изменена на: `{self.current_dir}`")
        except Exception as e:
            await event.respond(f"❌ Ошибка при смене директории:\n```{str(e)}```")

    async def _handle_ls(self, event: Message, directory: str):
        try:
            target_dir = self.current_dir if not directory else str(Path(self.current_dir).joinpath(directory).resolve())
            if not Path(target_dir).is_dir():
                await event.respond(f"❌ Директория не существует: `{target_dir}`")
                return
            
            items = os.listdir(target_dir)
            if not items:
                result = "Директория пуста"
            else:
                result = "Содержимое директории:\n" + "\n".join(items)
            
            await event.respond(
                f"📂 **Содержимое:** `{target_dir}`\n\n"
                f"```{result}```",
                parse_mode="markdown"
            )
        except Exception as e:
            await event.respond(f"❌ Ошибка при просмотре директории:\n```{str(e)}```")