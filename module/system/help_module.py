from telethon import events
import asyncio
import json
import os
import time
from pathlib import Path
from telethon.utils import get_display_name
from module.loader import System
from termcolor import colored

NAME = "Помощь"
DESCRIPTION = "Информация о всех командах"
EMOJI = "🛠️ "
VERSION = "2.2"
AUTHOR = "система"

class Help(System):
    
    def __init__(self, client, db_path="bot_config/bot_data.db"):
        super().__init__(client, db_path)
        self.name = NAME
        self.description = DESCRIPTION 
        self.emoji = EMOJI
        self.version = VERSION 
        self.author = AUTHOR
        self.theme_file = "bot_config/theme.json"
        self.themes_dir = "bot_config/themes"
        self.system_themes_dir = os.path.join(self.themes_dir, "system")
        self.user_themes_dir = os.path.join(self.themes_dir, "user")
        self._ensure_dirs_exist()
        self.current_theme = self._load_theme()
        self.current_theme_data = self._load_theme_data(self.current_theme)

    def _ensure_dirs_exist(self):
        Path("bot_config").mkdir(exist_ok=True)
        Path(self.themes_dir).mkdir(exist_ok=True)
        Path(self.system_themes_dir).mkdir(exist_ok=True)
        Path(self.user_themes_dir).mkdir(exist_ok=True)
        
        if not os.path.exists(self.theme_file):
            with open(self.theme_file, 'w') as f:
                json.dump({"theme": "default"}, f)
        
        default_themes = {
            "default": {
                "name": "Стандартная",
                "author": "система",
                "templates": {
                    "header": "🌸 *{title}* 🌸",
                    "separator": "══════════════════",
                    "module_item": "  {emoji} `{name}` {status}",
                    "command_item": "  ➣ `{command}`{admin_marker}",
                    "footer": "══════════════════\n🔙 Напишите `{prefix}help` чтобы вернуться"
                }
            },
            "cyber": {
                "name": "Киберпанк",
                "author": "система",
                "templates": {
                    "header": "┏━━━━━━━━━━━━━━━━━━┓\n┃   🚀 *{title}* 🚀   ┃",
                    "separator": "┣━━━━━━━━━━━━━━━━━━┫",
                    "module_item": "┃  {emoji} `{name}` {status} ┃",
                    "command_item": "┃  ➣ `{command}`{admin_marker} ┃",
                    "footer": "┗━━━━━━━━━━━━━━━━━━┛\n🔙 `{prefix}help` ДЛЯ ВОЗВРАТА"
                }
            },
            "code": {
                "name": "code",
                "author": "system",
                "templates": {
                    "header": "```\n# 📂 {title}\n",
                    "separator": "\n---\n",
                    "module_item": "- {emoji} {name}: {status}",
                    "command_item": "- {command}{admin_marker}",
                    "footer": "```"
                }
            }
        }
        
        for theme_name, data in default_themes.items():
            theme_path = os.path.join(self.system_themes_dir, f"{theme_name}.json")
            if not os.path.exists(theme_path):
                with open(theme_path, 'w') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

    def _load_theme(self):
        try:
            with open(self.theme_file, 'r') as f:
                data = json.load(f)
                return data.get("theme", "default")
        except:
            return "default"

    def _load_theme_data(self, theme_name):
        user_theme_path = os.path.join(self.user_themes_dir, f"{theme_name}.json")
        if os.path.exists(user_theme_path):
            try:
                with open(user_theme_path, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        system_theme_path = os.path.join(self.system_themes_dir, f"{theme_name}.json")
        if os.path.exists(system_theme_path):
            try:
                with open(system_theme_path, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        return {}

    def _save_theme(self, theme_name):
        with open(self.theme_file, 'w') as f:
            json.dump({"theme": theme_name}, f)
        self.current_theme = theme_name
        self.current_theme_data = self._load_theme_data(theme_name)

    async def _show_available_themes(self, event):
        themes = []
        
        for file in os.listdir(self.system_themes_dir):
            if file.endswith('.json'):
                theme_id = os.path.splitext(file)[0]
                try:
                    with open(os.path.join(self.system_themes_dir, file), 'r') as f:
                        theme_data = json.load(f)
                    themes.append({
                        'id': theme_id,
                        'name': theme_data.get('name', theme_id),
                        'author': theme_data.get('author', 'система'),
                        'is_current': theme_id == self.current_theme,
                        'type': 'system'
                    })
                except:
                    continue
        
        for file in os.listdir(self.user_themes_dir):
            if file.endswith('.json'):
                theme_id = os.path.splitext(file)[0]
                try:
                    with open(os.path.join(self.user_themes_dir, file), 'r') as f:
                        theme_data = json.load(f)
                    themes.append({
                        'id': theme_id,
                        'name': theme_data.get('name', theme_id),
                        'author': theme_data.get('author', 'Неизвестен'),
                        'is_current': theme_id == self.current_theme,
                        'type': 'user'
                    })
                except:
                    continue
        
        themes_sorted = sorted(themes, key=lambda x: (0 if x['type'] == 'system' else 1, x['name'].lower()))
        
        response = [
            self._format_template('header', title="ДОСТУПНЫЕ ТЕМЫ"),
            "",
            f"Текущая тема: **{self.current_theme}**",
            ""
        ]
        
        system_themes = [t for t in themes_sorted if t['type'] == 'system']
        if system_themes:
            response.append("🌟 *Стандартные темы*")
            for theme in system_themes:
                current_marker = " (текущая)" if theme['is_current'] else ""
                response.append(f"➣ `{theme['id']}` - {theme['name']}{current_marker}")
        
        user_themes = [t for t in themes_sorted if t['type'] == 'user']
        if user_themes:
            response.append("")
            response.append("✨ *Пользовательские темы*")
            for theme in user_themes:
                current_marker = " (текущая)" if theme['is_current'] else ""
                response.append(f"➣ `{theme['id']}` - {theme['name']} (автор: {theme['author']}){current_marker}")
        
        response.extend([
            "",
            f"Используйте: `{self.PREFIX}help theme [название_темы]` для изменения",
            f"Или отправьте JSON файл темы с reply на `{self.PREFIX}help theme import`",
            self._format_template('footer', theme=self.current_theme, prefix=self.PREFIX)
        ])
        
        await event.respond("\n".join(response), parse_mode='Markdown')

    async def _handle_theme_import(self, event):
        reply_msg = await event.get_reply_message()
        if not reply_msg or not reply_msg.file:
            error_msg = await event.respond("❌ Ответьте на сообщение с JSON файлом темы!")
            await asyncio.sleep(5)
            await error_msg.delete()
            return
        
        try:
            file_path = await reply_msg.download_media(file="temp_theme.json")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                theme_data = json.load(f)
            
            if not all(key in theme_data for key in ['name', 'templates']):
                error_msg = await event.respond("❌ Неверный формат темы! Обязательные поля: 'name', 'templates'")
                await asyncio.sleep(5)
                await error_msg.delete()
                os.remove(file_path)
                return
            
            theme_name = theme_data.get('id', os.path.splitext(reply_msg.file.name)[0].lower())
            theme_name = "".join(c for c in theme_name if c.isalnum() or c in ('_', '-')).strip('-_')
            
            if not theme_name:
                theme_name = f"custom_theme_{int(time.time())}"
            
            theme_path = os.path.join(self.user_themes_dir, f"{theme_name}.json")
            with open(theme_path, 'w', encoding='utf-8') as f:
                json.dump(theme_data, f, ensure_ascii=False, indent=2)
            
            os.remove(file_path)
            
            msg = await event.respond(
                f"✅ Тема '{theme_data['name']}' успешно импортирована!\n"
                f"Используйте: `{self.PREFIX}help theme {theme_name}`"
            )
            await asyncio.sleep(5)
            await msg.delete()
            
        except json.JSONDecodeError:
            error_msg = await event.respond("❌ Ошибка: файл не является валидным JSON!")
            await asyncio.sleep(5)
            await error_msg.delete()
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            error_msg = await event.respond(f"⚠️ Ошибка при импорте темы: {str(e)}")
            await asyncio.sleep(5)
            await error_msg.delete()
            if os.path.exists(file_path):
                os.remove(file_path)

    async def _handle_theme_change(self, event, theme_name):
        user_theme_path = os.path.join(self.user_themes_dir, f"{theme_name}.json")
        system_theme_path = os.path.join(self.system_themes_dir, f"{theme_name}.json")
        
        if os.path.exists(user_theme_path):
            theme_path = user_theme_path
        elif os.path.exists(system_theme_path):
            theme_path = system_theme_path
        else:
            error_msg = await event.respond(f"❌ Тема '{theme_name}' не найдена!")
            await asyncio.sleep(5)
            await error_msg.delete()
            return
        
        self._save_theme(theme_name)
        with open(theme_path, 'r') as f:
            theme_data = json.load(f)
        msg = await event.respond(f"✅ Тема изменена на: **{theme_data.get('name', theme_name)}**")
        await asyncio.sleep(3)
        await msg.delete()

    async def help_cmd(self, event):
        try:
            await event.delete()
            args = event.pattern_match.group(1)
            
            if args and args.startswith("theme"):
                theme_args = args.split()
                if len(theme_args) > 1:
                    if theme_args[1] == "import":
                        await self._handle_theme_import(event)
                    elif theme_args[1] == "create":
                        await self._handle_theme_create(event)
                    else:
                        await self._handle_theme_change(event, theme_args[1])
                else:
                    await self._show_available_themes(event)
                return
                
            requested_module = args.strip() if args else None
            
            if requested_module:
                await self._show_module_details(event, self.client.loaded_modules, requested_module.lower())
            else:
                await self._show_modules_list(event, self.client.loaded_modules)
                
        except Exception as e:
            error_msg = await event.respond(f"⚠️ Ошибка: {str(e)}")
            await asyncio.sleep(5)
            await error_msg.delete()

    def _format_template(self, template_name, **kwargs):
        templates = self.current_theme_data.get('templates', {})
        template = templates.get(template_name, "")
        
        if 'prefix' not in kwargs:
            kwargs['prefix'] = self.PREFIX
        
        try:
            return template.format(**kwargs)
        except:
            return template

    async def _show_modules_list(self, event, modules):
        response = [
            self._format_template('header', title="ДОСТУПНЫЕ МОДУЛИ"),
            "",
            f"Для подробностей: {self.PREFIX}help [модуль]",
            ""
        ]
        
        # Системные модули
        if modules.get("system"):
            response.append("⚙️ *Системные модули*")
            for module_name, data in modules["system"].items():
                if module_name.lower() != "help":
                    status = "🟢" if data.get('status') == '✅' else "🔴"
                    response.append(
                        self._format_template(
                            'module_item',
                            emoji=data.get('emoji', '🔹'),
                            name=data['name'],
                            status=status,
                            description=data.get('description', '')
                        )
                    )
            response.append("")

        if modules.get("user"):
            response.append("✨ *Пользовательские модули*")
            for module_name, data in modules["user"].items():
                status = "🟢" if data.get('status') == '✅' else "🔴"
                response.append(
                    self._format_template(
                        'module_item',
                        emoji=data.get('emoji', '🔸'),
                        name=data['name'],
                        status=status,
                        description=data.get('description', '')
                    )
                )
            response.append("")

        response.append(self._format_template('footer', theme=self.current_theme, prefix=self.PREFIX))
        await event.respond("\n".join(response), parse_mode='Markdown')

    async def _show_module_details(self, event, modules, module_name):
        if module_name == "help":
            response = [
                self._format_template('header', title=self.name.upper()),
                "",
                self._format_template('module_item', 
                    emoji=self.emoji,
                    name="Описание",
                    status=self.description,
                    description=""
                ),
                self._format_template('module_item',
                    emoji="📌",
                    name="Версия",
                    status=self.version,
                    description=""
                ),
                self._format_template('module_item',
                    emoji="👤",
                    name="Автор",
                    status=self.author,
                    description=""
                ),
                "",
                "🔹 *Команды:*"
            ]
            
            commands = [
                f"{self.PREFIX}help - Это сообщение",
                f"{self.PREFIX}help [модуль] - Справка по модулю",
                f"{self.PREFIX}help theme - Изменить тему справки"
            ]
            
            for cmd in commands:
                response.append(
                    self._format_template('command_item',
                        command=cmd,
                        admin_marker=""
                    )
                )
            
            response.append("")
            response.append(self._format_template('footer', theme=self.current_theme, prefix=self.PREFIX))
            
            await event.respond("\n".join(response), parse_mode='Markdown')
            return
        
        module_data = None
        module_type = None
        
        for mtype in ["system", "user"]:
            if modules.get(mtype):
                for name, data in modules[mtype].items():
                    if name.lower() == module_name or data['name'].lower() == module_name:
                        module_data = data
                        module_type = mtype
                        break
        
        if not module_data:
            error_msg = await event.respond("❌ Модуль не найден!")
            await asyncio.sleep(3)
            await error_msg.delete()
            return
        
        status_emoji = "🟢" if module_data.get('status') == '✅' else "🔴"
        
        has_commands = bool(module_data.get('commands'))
        has_inline = bool(module_data.get('inline_handlers'))
        
        module_kind = ""
        if has_commands and has_inline:
            module_kind = "Гибридный (команды + инлайн)"
        elif has_commands:
            module_kind = "Только команды"
        elif has_inline:
            module_kind = "Только инлайн"
        else:
            module_kind = "Без команд"
        
        response = [
            self._format_template('header', title=module_data['name'].upper()),
            "",
            self._format_template('module_item',
                emoji=module_data.get('emoji', '💠'),
                name="Описание",
                status=module_data.get('description', 'Нет описания'),
                description=""
            ),
            self._format_template('module_item',
                emoji="📌",
                name="Версия",
                status=module_data.get('version', '1.0'),
                description=""
            ),
            self._format_template('module_item',
                emoji="👤",
                name="Автор",
                status=module_data.get('author', 'Неизвестен'),
                description=""
            ),
            self._format_template('module_item',
                emoji="📦",
                name="Тип",
                status="Системный" if module_type == 'system' else "Пользовательский",
                description=""
            ),
            self._format_template('module_item',
                emoji="🔌",
                name="Режим",
                status=module_kind,
                description=""
            ),
            self._format_template('module_item',
                emoji=status_emoji,
                name="Статус",
                status="Работает" if module_data.get('status') == '✅' else "Ошибка",
                description=""
            ),
            ""
        ]

        if module_data.get('commands'):
            response.append("🔹 *Команды:*")
            for cmd in module_data['commands']:
                admin_marker = " (admin)" if "(admin)" in cmd else ""
                cmd_name = cmd.replace(" (admin)", "")
                response.append(
                    self._format_template('command_item',
                        command=cmd_name,
                        admin_marker=admin_marker
                    )
                )
        
        if module_data.get('inline_handlers'):
            response.append("")
            response.append("🔸 *Инлайн команды:*")
            for handler in module_data['inline_handlers']:
                admin_marker = " (admin)" if "(admin)" in handler else ""
                handler_name = handler.replace(" (admin)", "")
                response.append(
                    self._format_template('command_item',
                        command=handler_name,
                        admin_marker=admin_marker
                    )
                )
        
        response.append("")
        response.append(self._format_template('footer', theme=self.current_theme, prefix=self.PREFIX))
        
        await event.respond("\n".join(response), parse_mode='Markdown')