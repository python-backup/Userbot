from module.loader import User
from telethon import events
import json
import os

NAME = "Переводчик"
DESCRIPTION = "Перевод слов между русским и английским"
EMOJI = "🌍"
VERSION = "1.0"
AUTHOR = "system"

class TranslatorModule(User):
    
    
    # Путь к файлу словаря
    DICT_PATH = "bot_config/slovar.json"
    
    def __init__(self, client, db_path="bot_config/bot_data.db"):
        super().__init__(client, db_path)
        # Загружаем словарь при инициализации
        self.translations = self.load_dictionary()
        self.name = NAME
        self.description = DESCRIPTION
        self.emoji = EMOJI
        self.author = AUTHOR
        self.version = VERSION
 
    def load_dictionary(self):
        """Загружает словарь из файла или возвращает стандартный"""
        try:
            # Создаем папку, если ее нет
            os.makedirs(os.path.dirname(self.DICT_PATH), exist_ok=True)
            
            if os.path.exists(self.DICT_PATH):
                with open(self.DICT_PATH, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # Стандартный словарь
                default_dict = {
                    "ru_en": {
                        "привет": "hello", "мир": "world", "дом": "house", "вода": "water", "огонь": "fire", 
                        # ... (остальные стандартные слова)
                    },
                    "en_ru": {
                        "hello": "привет", "world": "мир", "house": "дом", "water": "вода", "fire": "огонь",
                        # ... (остальные стандартные слова)
                    }
                }
                # Сохраняем стандартный словарь
                self.save_dictionary(default_dict)
                return default_dict
        except Exception as e:
            print(f"Ошибка загрузки словаря: {e}")
            return {"ru_en": {}, "en_ru": {}}
    
    def save_dictionary(self, data=None):
        """Сохраняет словарь в файл"""
        try:
            with open(self.DICT_PATH, 'w', encoding='utf-8') as f:
                json.dump(data or self.translations, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения словаря: {e}")

    async def translate_cmd(self, event):
        """!translate - Перевод текста
        Использование: !translate <текст>
        #public"""
        text = event.pattern_match.string.split(' ', 1)[1] if ' ' in event.pattern_match.string else None
        
        if not text:
            await event.reply("❌ Укажите текст для перевода!\nПример: !translate Привет")
            return
            
        # Автоопределение языка
        if any(char in 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя' for char in text.lower()):
            direction = "ru_en"
            lang_name = "рус → англ"
        else:
            direction = "en_ru"
            lang_name = "англ → рус"
        
        # Поиск перевода
        result = self.translations[direction].get(
            text.lower(), 
            "❌ Перевод не найден"
        )
        
        await event.reply(f"{result}")

    async def addword_cmd(self, event):
        """!addword - Добавить слово в словарь
        Использование: !addword <слово> <перевод>"""
        if not await self.check_admin(event):
            return
            
        args = event.pattern_match.string.split(' ', 2)[1:] if ' ' in event.pattern_match.string else []
        
        if len(args) < 2:
            await event.reply("❌ Укажите слово и перевод!\nПример: !addword hello привет")
            return
            
        word, translation = args[0], args[1]
        
        # Определяем направление перевода
        if any(char in 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя' for char in word.lower()):
            self.translations["ru_en"][word.lower()] = translation.lower()
            reverse_dir = "en_ru"
        else:
            self.translations["en_ru"][word.lower()] = translation.lower()
            reverse_dir = "ru_en"
        
        # Добавляем обратный перевод
        self.translations[reverse_dir][translation.lower()] = word.lower()
        
        # Сохраняем обновленный словарь
        self.save_dictionary()
        
        await event.reply(f"✅ Добавлено: {word} ↔ {translation}")