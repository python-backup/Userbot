from module.loader import User
import random
import asyncio
from telethon import types

NAME = "Memes & Trolls"
DESCRIPTION = "Самые кринжовые и смешные функции"
EMOJI = "🤡"
AUTHOR = "system"

class FunModule(User):
    """Модуль для приколов и троллинга"""
    def __init__(self, client, db_path="bot_config/bot_data.db"):
        super().__init__(client, db_path)
        self.name = NAME
        self.description = DESCRIPTION
        self.emoji = EMOJI
        self.author = AUTHOR

    async def _execute_command(self, event, response_text):
        """Удаляет команду и отправляет ответ"""
        try:
            await event.delete()  # Удаляем команду
        except:
            pass  # Если нет прав на удаление, пропускаем
        await event.respond(response_text)  # Отправляем ответ

    async def cringe_cmd(self, event):
        '''!cringe - Рандомный кринж'''
        cringe_list = [
            "Я в 5 лет думал, что если нажать Alt+F4, стану богатым...",
            "Когда мама спрашивает, кто разбил вазу, а ты говоришь, что это кот... но у вас нет кота.",
            "Ты: *пишешь сообщение* \nТоже ты: *удаляешь* \nЧат: '...'",
        ]
        await self._execute_command(event, f"🤡 {random.choice(cringe_list)}")

    async def fake_ban_cmd(self, event):
        '''!fakeban - Фейковый бан рандомного юзера'''
        chat = await event.get_chat()
        users = [p.id for p in await self.client.get_participants(chat) if not p.bot]
        if not users:
            await self._execute_command(event, "🚨 Некого банить, тут одни боты...")
            return
        victim = random.choice(users)
        await self._execute_command(event, f"🚨 **BANNED** <@{victim}> за **нарушение правил чата** (шутка)")

    async def npc_cmd(self, event):
        '''!npc - Что бы сказал NPC?'''
        npc_phrases = [
            "Мне нужно квест выполнить...",
            "Не трогай меня, у меня лагает путь!",
            "Эй, слушай!..",
            "Ты видел моего кота?",
        ]
        await self._execute_command(event, f"🗣️ NPC говорит: *{random.choice(npc_phrases)}*")

    async def conspiracy_cmd(self, event):
        '''!conspiracy - Случайная теория заговора'''
        theories = [
            "А что если облака – это дроны?",
            "Windows 10 на самом деле шпионит за твоим холодильником.",
            "Коты – это инопланетяне, но они просто притворяются милыми.",
        ]
        await self._execute_command(event, f"🔍 **Теория заговора:** {random.choice(theories)}")

    async def bsod_cmd(self, event):
        '''!bsod - Фейковый синий экран'''
        bsod_text = (
            "💻 **CRITICAL ERROR**\n\n"
            "SYSTEM32 DELETED ITSELF\n"
            "PLEASE RESTART YOUR LIFE\n\n"
            "0x0000001A (MEMORY_CORRUPTED_BY_CRINGE)"
        )
        await self._execute_command(event, bsod_text)

    async def anime_char_cmd(self, event):
        '''!animechar - Рандомный аниме-персонаж'''
        traits = ["цудере", "яндере", "кудэре", "хиккикомори"]
        powers = ["огонь", "тьма", "копирование способностей", "бесполезность"]
        response = (
            f"🎌 **Твой аниме-персонаж:**\n"
            f"- Тип: **{random.choice(traits)}**\n"
            f"- Сила: **{random.choice(powers)}**\n"
            f"- Фраза: *'NANI?!'*"
        )
        await self._execute_command(event, response)

    async def troll_cmd(self, event):
        '''!troll - Случайный троллинг'''
        actions = [
            "Я знаю, что ты это читаешь...",
            "*тихо удаляет сообщение*",
            "...",
        ]
        await self._execute_command(event, random.choice(actions))

    async def memename_cmd(self, event):
        '''!memename - Генератор кринжовых ников'''
        parts = ["xXx_", "_", "Pro", "Noob", "Killer", "2007", "Gamer"]
        new_name = f"{random.choice(parts)}{random.choice(parts)}{random.choice(parts)}"
        await self._execute_command(event, f"🔥 Твой новый ник: **{new_name}**")

    async def roulette_cmd(self, event):
        '''!roulette - Русская рулетка (6 вариантов, 1 проигрышный)'''
        if random.randint(1, 6) == 1:
            await self._execute_command(event, "💀 Бах! Ты проиграл.")
        else:
            await self._execute_command(event, "🎉 Ты выжил! Попробуешь еще раз?")

    async def fake_typing_cmd(self, event):
        '''!typing - Фейковая печать (бот делает вид, что печатает)'''
        async with self.client.action(event.chat_id, 'typing'):
            await asyncio.sleep(3)
        await self._execute_command(event, "Я долго думал... но так и не придумал ничего умного.")