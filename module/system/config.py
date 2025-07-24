# system/config.py
from ..loader import System
from telethon import events
import json

NAME = "Конфигурация"
DESCRIPTION = "Основные настройки rux"
EMOJI = "⚙️"
AUTHOR = "system"
VERSION = "1.0"

class ModConfig(System):
    """Управление конфигурацией модулей"""
    def __init__(self, client, db_path="bot_config/bot_data.db"):
        super().__init__(client, db_path)
        self.name = NAME
        self.description = DESCRIPTION
        self.emoji = EMOJI
        self.author = AUTHOR

    async def config_cmd(self, event):
        """!config - Показать список модулей и их настройки"""
        if not await self.check_admin(event):
            return
        
        modules = self.client.loaded_modules
        text = "**⚙️ Доступные модули:**\n\n"
        
        for mtype in modules:
            for mod_name, mod_data in modules[mtype].items():
                status = "✅" if mod_data['status'] == '✅' else "❌"
                text += (
                    f"{mod_data['emoji']} **{mod_name}** ({mtype})\n"
                    f"Версия: {mod_data['version']}\n"
                    f"Статус: {status}\n"
                    f"Команды: `{'`, `'.join(mod_data['commands'])}`\n\n"
                )
        
        await event.respond(text)

    async def config_keys_cmd(self, event):
        """!config keys <модуль> - Показать все ключи настроек модуля"""
        if not await self.check_admin(event):
            return
        
        module_name = event.pattern_match.group(1).strip()
        
        # Проверяем существование модуля
        found_module = None
        for mtype in self.client.loaded_modules:
            if module_name in self.client.loaded_modules[mtype]:
                found_module = self.client.loaded_modules[mtype][module_name]
                break
        
        if not found_module:
            await event.respond(f"❌ Модуль `{module_name}` не найден!")
            return
        
        # Получаем текущие настройки модуля
        module_config = await self.module_config(module_name)
        
        if not module_config:
            await event.respond(f"ℹ️ Модуль `{module_name}` не имеет настроек")
            return
        
        text = f"**🔑 Доступные ключи настроек для {module_name}:**\n\n"
        
        for key, value in module_config.items():
            text += f"• **{key}** = `{value}`\n"
        
        text += "\nИспользуйте `!config set <модуль> <ключ> <значение>` для изменения"
        await event.respond(text)

    async def config_set_cmd(self, event):
        """!config set <модуль> <ключ> <значение> - Изменить настройку модуля"""
        if not await self.check_admin(event):
            return
        
        args = event.pattern_match.group(1).split()
        if len(args) < 3:
            await event.respond("**Использование:** `!config set <модуль> <ключ> <значение>`")
            return
        
        module_name, key, value = args[0], args[1], " ".join(args[2:])
        
        # Проверяем существование модуля
        found = False
        for mtype in self.client.loaded_modules:
            if module_name in self.client.loaded_modules[mtype]:
                found = True
                break
        
        if not found:
            await event.respond(f"❌ Модуль `{module_name}` не найден!")
            return
        
        # Меняем настройку
        await self.module_config(module_name, key, value)
        await event.respond(f"**⚙️ Настройка обновлена:**\n`{module_name}.{key} = {value}`")

    async def config_toggle_cmd(self, event):
        """!config toggle <модуль> - Включить/выключить модуль"""
        if not await self.check_admin(event):
            return
        
        module_name = event.pattern_match.group(1).strip()
        
        # Проверяем модуль
        found = False
        for mtype in self.client.loaded_modules:
            if module_name in self.client.loaded_modules[mtype]:
                found = True
                break
        
        if not found:
            await event.respond(f"❌ Модуль `{module_name}` не найден!")
            return
        
        # Меняем статус
        current = await self.module_config(module_name, "enabled")
        new_status = not bool(current) if current is not None else False
        await self.module_config(module_name, "enabled", new_status)
        
        await event.respond(
            f"**{'✅ Включен' if new_status else '❌ Выключен'} модуль:** `{module_name}`\n"
            f"Перезагрузите бота (`!restart`), чтобы изменения вступили в силу."
        )