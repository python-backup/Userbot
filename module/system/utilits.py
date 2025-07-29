from module.loader import User
import requests
from forex_python.converter import CurrencyRates
import math
import re
import random
import asyncio
from googletrans import Translator
from bs4 import BeautifulSoup
import feedparser
from datetime import datetime

class UtilityTools(User):
    
    NAME = "utility_tools"
    DESCRIPTION = "Модуль с полезными утилитами: конвертер валют, калькулятор, таймер, случайный выбор, переводчик, факты, новости и погода"
    EMOJI = "🛠️"
    VERSION = "2.2"
    AUTHOR = "DigitalEternities"
    
    def __init__(self, client, db_path="bot_config/bot_data.db"):
        super().__init__(client, db_path)
        self.c = CurrencyRates(force_decimal=True)
        self.translator = Translator(service_urls=[
            'translate.google.com',
            'translate.google.ru'
        ])
        
        self.facts = [
            "🧠 Человеческий мозг генерирует за день больше электрических импульсов, чем все телефоны мира вместе взятые.",
            "🌌 В космосе есть алмазная планета (BPM 37093), размером с Юпитер.",
            "🦇 Летучие мыши — единственные млекопитающие, способные к настоящему полёту (а не планированию).",
            "📅 В 1903 году братья Райт совершили первый полёт на самолёте, который длился всего 12 секунд.",
            "🐜 Муравьи никогда не спят — у них нет век, но они отдыхают короткими периодами.",
            "🔥 Огонь не имеет тени — даже в самых ярких условиях.",
            "🍌 Бананы — это ягоды, а клубника — нет (с точки зрения ботаники).",
            "🧊 Лёд горячее, чем вы думаете: при -40°C он всё ещё «горячее» жидкого азота (-196°C).",
            "🦎 Хамелеоны меняют цвет не для маскировки, а для общения и регуляции температуры.",
            "🚀 Запуск ракеты SpaceX Falcon Heavy в 2018 году сопровождался Tesla Roadster с манекеном водителя.",
            "🧬 У человека и шимпанзе 98.7% общих генов.",
            "🌕 На Луне есть мусор: более 180 тонн обломков космических аппаратов и оборудования.",
            "🐙 У осьминога три сердца и голубая кровь (из-за гемоцианина вместо гемоглобина).",
            "💡 Эйнштейн так и не научился водить машину.",
            "🕰️ Самые точные часы в мире — атомные, они ошибаются на 1 секунду за 15 миллиардов лет.",
            "🌍 Земля замедляется: каждые 100 лет сутки становятся длиннее на 1.7 миллисекунды.",
            "🍯 Чтобы сделать 1 кг мёда, пчела должна облететь 4 млн цветков.",
            "🚗 Первый автомобильный штраф выписали в 1896 году за скорость 13 км/ч.",
            "🦉 Совы могут поворачивать голову на 270 градусов благодаря особому строению шеи.",
            "🧂 Поваренная соль (NaCl) — единственный минерал, который человек ест в чистом виде.",
            "📱 Первый SMS-сообщение было отправлено в 1992 году и содержало текст: «Счастливого Рождества!».",
            "🦴 Кости человека прочнее стали, если сравнивать их по соотношению веса и прочности.",
            "🌡️ Самая высокая температура, зарегистрированная на Земле: +56.7°C (Долина Смерти, США).",
            "❄️ Самая низкая температура: -89.2°C (антарктическая станция «Восток»).",
            "🐋 Сердце синего кита бьётся 5–10 раз в минуту и размером с автомобиль.",
            "💻 Первый компьютерный вирус (1982) заражал дискеты и назывался «Elk Cloner».",
            "🪐 Юпитер защищает Землю от астероидов, «притягивая» их своей гравитацией.",
            "🍎 Яблоки тонут в воде, потому что они на 25% состоят из воздуха (в отличие от арбузов).",
            "🦴 Новорождённый ребёнок имеет 270 костей, а взрослый — всего 206.",
            "🚿 Вода — единственное вещество, которое в природе встречается в трёх состояниях: твёрдом, жидком и газообразном.",
            "🪙 Монетка, брошенная с Эмпайр-стейт-билдинг, не убьёт человека — она достигнет скорости всего 80 км/ч.",
            "🌿 Растения «слышат» звуки: например, реагируют на жужжание пчёл, увеличивая содержание сахара в нектаре.",
            "🦴 Правши живут в среднем на 9 лет дольше левшей (статистика).",
            "🧲 Магнитное поле Земли смещается: за последние 200 лет оно «сдвинулось» на 225 км.",
            "🪐 Плутон меньше России по площади (17.7 млн км² против 17.1 млн км²).",
            "🐍 Змеи могут «видеть» с закрытыми глазами — у них есть инфракрасные рецепторы.",
            "📚 Самая длинная книга в мире — «В поисках утраченного времени» Марселя Пруста (1.2 млн слов).",
            "🦠 Вирусы могут заражать другие вирусы (например, вирофаг Sputnik).",
            "🧵 Паутина паука-кругопряда прочнее стали той же толщины.",
            "🌊 Вода покрывает 71% поверхности Земли, но только 1% её пригоден для питья.",
            "🦕 Куры — ближайшие живые родственники тираннозавра.",
            "🧪 Золото растворяется в ртути, как сахар в воде.",
            "🛌 Человек проводит треть жизни во сне (около 25 лет, если доживёт до 75).",
            "🪐 У Сатурна есть шестиугольный шторм на северном полюсе (диаметр — 25 000 км).",
            "🐝 Пчелы распознают человеческие лица, но только как «узоры».",
            "🧴 Молния нагревает воздух вокруг себя до 30 000°C — это в 5 раз горячее поверхности Солнца.",
            "🦴 Волосы человека могут выдержать вес до 100 граммов (а вся шевелюра — до 12 тонн).",
            "🌡️ Температура ядра Земли (6000°C) равна температуре поверхности Солнца.",
            "🦜 Вороны настолько умны, что могут планировать месть обидчикам.",
            "🧲 Если уменьшить Землю до размеров бильярдного шара, она будет идеально гладкой (перепады высот < 0.1 мм)."
        ]

    # ========== КОНВЕРТЕР ВАЛЮТ (ИСПРАВЛЕННЫЙ) ==========
    async def convert_cmd(self, event):
        """!convert <amount> <from_currency> to <to_currency> - Конвертирует валюту"""
        await event.delete()
        args = event.pattern_match.group(1)
        
        if not args:
            await event.respond("❌ Укажите параметры конвертации!\nПример: !convert 100 USD to RUB")
            return
            
        try:
            match = re.match(r'(\d+\.?\d*)\s+([A-Za-z]{3})\s+to\s+([A-Za-z]{3})', args.strip())
            if not match:
                raise ValueError("Неверный формат команды")
                
            amount, from_curr, to_curr = match.groups()
            amount = float(amount)
            from_curr = from_curr.upper()
            to_curr = to_curr.upper()
            
            try:
                result = self.c.convert(from_curr, to_curr, amount)
                await event.respond(f"💱 {amount:.2f} {from_curr} = {result:.2f} {to_curr}")
            except Exception as api_error:
                await self.fallback_convert(event, amount, from_curr, to_curr)
                
        except Exception as e:
            await event.respond(f"❌ Ошибка конвертации: {str(e)}\nПример: !convert 100 USD to RUB")

    async def fallback_convert(self, event, amount, from_curr, to_curr):
        """Альтернативный метод конвертации"""
        try:
            # Добавлены дополнительные валюты и обновлены курсы
            rates = {
                "USD": {"RUB": 90.0, "EUR": 0.92, "GBP": 0.79, "JPY": 151.5, "CNY": 7.23},
                "EUR": {"RUB": 98.0, "USD": 1.08, "GBP": 0.86, "JPY": 164.5, "CNY": 7.86},
                "RUB": {"USD": 0.011, "EUR": 0.010, "GBP": 0.0086, "JPY": 1.68, "CNY": 0.080},
                "GBP": {"USD": 1.27, "EUR": 1.16, "RUB": 116.5, "JPY": 191.5, "CNY": 9.15},
                "JPY": {"USD": 0.0066, "EUR": 0.0061, "RUB": 0.60, "GBP": 0.0052, "CNY": 0.048},
                "CNY": {"USD": 0.14, "EUR": 0.13, "RUB": 12.5, "GBP": 0.11, "JPY": 20.8}
            }
            
            if from_curr in rates and to_curr in rates[from_curr]:
                result = amount * rates[from_curr][to_curr]
                await event.respond(f"💱 (Фиксированный курс) {amount:.2f} {from_curr} ≈ {result:.2f} {to_curr}")
            else:
                raise ValueError("Валюта не поддерживается")
        except Exception as e:
            await event.respond("❌ Не удалось выполнить конвертацию. Попробуйте позже.")

    # ========== КАЛЬКУЛЯТОР (ИСПРАВЛЕННЫЙ) ==========
    async def calc_cmd(self, event):
        """!calc <expression> - Расширенный калькулятор"""
        await event.delete()
        args = event.pattern_match.group(1)
        
        if not args:
            help_text = (
                "🧮 Расширенный калькулятор. Поддерживает:\n"
                "• Базовые операции: + - * / \n"
                "• Степени: 2^3 или 2**3\n"
                "• Корни: sqrt(9)\n"
                "• Тригонометрию: sin(30), cos(45), tan(60)\n"
                "• Константы: pi, e\n"
                "• Факториалы: 5!\n\n"
                "Примеры:\n!calc 2*(3+4)^2\n!calc sin(30) + cos(45)"
            )
            await event.respond(help_text)
            return
            
        try:
            expr = args.replace(" ", "").replace("^", "**")
            
            # Улучшенное регулярное выражение для безопасности
            if not re.match(r'^[\d+\-*/().!^√πesincostanlog\s]+$', expr):
                raise ValueError("Недопустимые символы в выражении")
                
            expr = expr.replace("√", "sqrt")
            
            safe_dict = {
                'sqrt': math.sqrt,
                'sin': math.sin,
                'cos': math.cos,
                'tan': math.tan,
                'log': math.log,
                'pi': math.pi,
                'e': math.e,
                '__builtins__': None
            }
            
            def factorial(n):
                if n > 100:
                    raise ValueError("Факториал слишком большого числа")
                return math.factorial(int(n))
                
            safe_dict['factorial'] = factorial
            
            result = eval(expr, {"__builtins__": None}, safe_dict)
            await event.respond(f"🧮 {args} = {result}")
            
        except Exception as e:
            await event.respond(f"❌ Ошибка: {str(e)}\nИспользуйте !calc для справки")

    # ========== ТАЙМЕР (ИСПРАВЛЕННЫЙ) ==========
    async def timer_cmd(self, event):
        """!timer <seconds> [message] - Установить таймер"""
        await event.delete()
        args = event.pattern_match.group(1)
        
        if not args:
            await event.respond("❌ Укажите время в секундах!\nПример: !timer 60 Напоминание")
            return
            
        try:
            parts = args.split(maxsplit=1)
            seconds = float(parts[0])  # Разрешены дробные секунды
            if seconds <= 0:
                raise ValueError("Время должно быть больше 0")
            seconds = min(seconds, 86400)  # Ограничение 24 часа
            message = parts[1] if len(parts) > 1 else "Время вышло!"
            
            await event.respond(f"⏳ Таймер на {seconds} секунд установлен. Сообщение: '{message}'")
            
            async def timer_callback():
                await asyncio.sleep(seconds)
                await event.respond(f"🔔 {message} (таймер {seconds} сек.)")
                
            asyncio.create_task(timer_callback())
            
        except ValueError as e:
            await event.respond(f"❌ Неверный формат времени: {str(e)}\nПример: !timer 60 Напоминание")
        except Exception as e:
            await event.respond(f"❌ Ошибка при установке таймера: {str(e)}")

    # ========== СЛУЧАЙНЫЙ ВЫБОР (ИСПРАВЛЕННЫЙ) ==========
    async def choose_cmd(self, event):
        """!choose <option1> ; <option2> ... - Выбрать случайный вариант"""
        await event.delete()
        args = event.pattern_match.group(1)
        
        if not args:
            await event.respond("❌ Укажите варианты через ';'!\nПример: !choose Пицца ; Суши ; Бургер")
            return
            
        options = [x.strip() for x in re.split(r';\s*', args) if x.strip()]
        
        if len(options) < 2:
            await event.respond("❌ Нужно указать хотя бы 2 варианта!")
            return
            
        choice = random.choice(options)
        options_text = "\n".join(f"• {opt}" for opt in options)
        await event.respond(f"🎲 Я выбираю: {choice}!\n\nВарианты:\n{options_text}")

    # ========== ПЕРЕВОДЧИК (ИСПРАВЛЕННЫЙ) ==========
    async def translate_cmd(self, event):
        """!translate [текст] - Перевод между английским и русским"""
        await event.delete()
        text = event.pattern_match.group(1)
        
        if not text:
            await event.respond(f"❌ Укажите текст для перевода!\nПример: {self.PREFIX}translate Привет, мир!")
            return
            
        try:
            for attempt in range(3):
                try:
                    detected = self.translator.detect(text)
                    dest = 'en' if detected.lang == 'ru' else 'ru'
                    translation = self.translator.translate(text, dest=dest)
                    response = (
                        f"🔤 Исходный текст ({detected.lang}):\n{text}\n\n"
                        f"🌍 Перевод ({dest}):\n{translation.text}"
                    )
                    await event.respond(response)
                    return
                except Exception as e:
                    if attempt == 2:
                        raise
                    await asyncio.sleep(1)
                    
        except Exception:
            try:
                translated = await self.fallback_translate(text)
                await event.respond(f"🌍 (Альтернативный перевод):\n{translated}")
            except Exception as e:
                await event.respond(f"❌ Ошибка перевода: {str(e)}\nПопробуйте позже")

    async def fallback_translate(self, text):
        """Альтернативные методы перевода без API ключа"""
        try:
            is_russian = bool(re.search('[а-яА-Я]', text))
            lang_pair = 'ru-en' if is_russian else 'en-ru'
            
            url = "https://api.mymemory.translated.net/get"
            params = {'q': text, 'langpair': lang_pair}
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if data.get('responseData', {}).get('translatedText'):
                return data['responseData']['translatedText']
                
            return await self.web_translate(text, is_russian)
        except Exception:
            raise Exception("Все сервисы перевода недоступны")

    async def web_translate(self, text, is_russian):
        """Перевод через веб-скрапинг"""
        try:
            to_lang = 'en' if is_russian else 'ru'
            url = f"https://www.bing.com/translator?text={requests.utils.quote(text)}&to={to_lang}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            translation = soup.find('textarea', {'id': 'tta_output_ta'})
            if translation:
                return translation.text.strip()
                
            raise Exception("Перевод не найден")
        except Exception as e:
            raise Exception(f"Ошибка веб-перевода: {str(e)}")

    # ========== РАНДОМНЫЙ ФАКТ (БЕЗ ИЗМЕНЕНИЙ) ==========
    async def fact_cmd(self, event):
        """!fact - Показать случайный интересный факт"""
        await event.delete()
        fact = random.choice(self.facts)
        await event.respond(f"📚 **Случайный факт:**\n\n{fact}")

    # ========== УДАЛЕНИЕ СООБЩЕНИЙ (ИСПРАВЛЕННЫЙ) ==========
    async def delm_cmd(self, event):
        """!delm [число] - Удалить указанное количество сообщений пользователя"""
        await event.delete()
        args = event.pattern_match.group(1)
    
        if not args or not args.isdigit():
            await event.respond(f"❌ Укажите количество сообщений для удаления!\nПример: {self.PREFIX}delm 3")
            return
        
        count = int(args)
        if count <= 0 or count > 100:
            await event.respond("❌ Число должно быть от 1 до 100!")
            return
        
        try:
            messages = []
            async for message in self.client.iter_messages(
                await event.get_chat(),
                from_user="me" if event.is_private else event.sender_id,
                limit=count
            ):
                messages.append(message)
            
            if messages:
                await self.client.delete_messages(await event.get_chat(), messages)
            else:
                await event.respond("❌ Не найдено сообщений для удаления!", delete_after=5)
        except Exception as e:
            # Логируем ошибку, но не показываем пользователю
            print(f"Ошибка при удалении сообщений: {e}")