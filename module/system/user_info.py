from module.loader import User
from telethon import events
import telethon.types
from datetime import datetime

NAME = "Профиль"
DESCRIPTION = "Информация о людей"
EMOJI = "👤"
VERSION = "1.0"
AUTHOR = "System"

class UserInfoModule(User):
    
    def __init__(self, client, db_path="bot_config/bot_data.db"):
        super().__init__(client, db_path)
        self.name = NAME
        self.description = DESCRIPTION 
        self.emoji = EMOJI
        self.version = VERSION 
        self.author = AUTHOR

    async def user_cmd(self, event):
        try:
            if event.is_reply:
                reply = await event.get_reply_message()
                user = await self.client.get_entity(reply.sender_id)
            elif event.pattern_match.group(1):
                user_arg = event.pattern_match.group(1).strip()
                user = await self.client.get_entity(user_arg)
            else:
                user = await event.get_sender()
            
            user_info = f"ℹ️ **Информация о пользователе**\n\n"
            
            user_info += f"👤 **Имя:** {user.first_name or 'Не указано'}\n"
            if user.last_name:
                user_info += f"👥 **Фамилия:** {user.last_name}\n"
            if user.username:
                user_info += f"🔹 **Юзернейм:** @{user.username}\n"
            user_info += f"🆔 **ID:** `{user.id}`\n"
            
            if hasattr(user, 'status'):
                if user.status and hasattr(user.status, 'was_online'):
                    last_seen = user.status.was_online
                    user_info += f"⏱ **Был в сети:** {last_seen.strftime('%d.%m.%Y %H:%M')}\n"
            
            if hasattr(user, 'about') and user.about:
                user_info += f"📝 **Описание:** {user.about}\n"
            
            if hasattr(user, 'phone') and user.phone:
                user_info += f"📱 **Телефон:** `{user.phone}`\n"
            else:
                user_info += "📱 **Телефон:** `Скрыт/недоступен`\n"
            
            if user.bot:
                user_info += "🤖 **Это бот:** Да\n"
            
            if hasattr(user, 'status'):
                if user.status and hasattr(user.status, 'created_at'):
                    created_at = user.status.created_at
                    user_info += f"📅 **Дата регистрации:** {created_at.strftime('%d.%m.%Y')}\n"
            
            await event.delete()
            await event.respond(user_info)
            
        except Exception as e:
            await event.delete()
            await event.respond(f"⚠️ Ошибка: {str(e)}")