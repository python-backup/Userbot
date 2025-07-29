import asyncio
import os
import random
import json
from termcolor import colored
from pathlib import Path
from core.config import BOT_CONFIG_DIR, USER_MODULES_DIR
from core.database import ensure_db_exists, get_sessions
from core.userbot import setup_userbot_session, run_userbot_session
from core.utils import cleanup_processes
from core.inline_bot import run_inline_bot

def get_prefix() -> str:
    """Получаем префикс напрямую из конфиг-файла"""
    config_path = Path("bot_config/config.json")
    try:
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
                return config.get("prefix", "!")
        return "!"  # Дефолтный префикс
    except Exception as e:
        print(colored(f"⚠️ Ошибка чтения префикса: {e}", "yellow"))
        return "!"

async def spinning_rux():
    frames = [
        "🅡 🅤 🅧",
        "🆁 🆄 🆇", 
        "Ⓡ Ⓤ Ⓧ",
        "ℝ 𝕌 𝕏",
        "𝐑 𝐔 𝐗",
        "𝑅 𝑈 𝑋",
        "𝖱 𝖴 𝖷",
        "𝓡 𝓤 𝓧",
        "ℜ 𝔘 𝔛",
        "ℝ 𝕌 𝕏"
    ]
    for frame in frames:
        print(f"\r{frame}", end="", flush=True)
        await asyncio.sleep(0.1)

async def print_loading_animation():
    steps = [
        ("🧙‍♂️ Инициализация магии RUX...", 10),
        ("🌾 Проращиваем код...", 20),
        ("⚡ Заряжаем шутки...", 30), 
        ("🤖 Будим ботов...", 45),
        ("🧹 Убираем баги...", 55),
        ("☕ Завариваем кофе...", 65),
        ("🎵 Настраиваем звуки...", 75),
        ("📡 Подключаемся...", 85),
        ("🤹‍♂️ Разминаем сервера...", 90),
        ("🚀 Поехали!", 100)
    ]
    
    print(colored("\n[    ] Подготовка к запуску:", "magenta"))
    await spinning_rux()
    
    for text, progress in steps:
        color = random.choice(["yellow", "cyan", "magenta", "green"])
        bar_length = 30
        filled = int(bar_length * progress / 100)
        bar = "[" + "█" * filled + " " * (bar_length - filled) + "]"
        
        if progress == 100:
            bar = colored(bar, "green", attrs=["blink", "bold"])
            text = colored(text, "green", attrs=["bold"])
        elif progress > 85:
            bar = colored(bar, "cyan", attrs=["bold"])
        elif progress > 60:
            bar = colored(bar, "yellow")
        
        print(f"\r{bar} {progress}% {colored(text, color)}", end="", flush=True)
        delay = 0.2 + (progress / 100) * 0.5
        await asyncio.sleep(delay)
    
    print("\n")

async def main():
    os.makedirs(BOT_CONFIG_DIR, exist_ok=True)
    os.makedirs(USER_MODULES_DIR, exist_ok=True)
    ensure_db_exists()
    
    print(colored(r"""
          ____  _    ___  _
         /  __\/ \ /\\  \//
         |  \/|| | || \  / 
         |    /| \_/| /  \ 
         \_/\_\\____//__/\\
                  
    """, "blue"))
    print(colored("=== 🤖 RUX UserBot System ===", "blue", attrs=["bold"]))
    print(colored("⚡ Версия 17.1 | Квантовый запуск", "magenta"))
    
    await print_loading_animation()

    sessions = get_sessions()
    if not sessions:
        print(colored("\n🤷 Сессии не найдены. Начинаем настройку...", "yellow"))
        if not await setup_userbot_session():
            print(colored("❌ Настройка прервана", "red"))
            return
        sessions = get_sessions()

    # Получаем префикс ДО запуска процессов
    current_prefix = get_prefix()
    inline_process = await run_inline_bot()
    
    try:
        userbot_tasks = [
            asyncio.create_task(run_userbot_session(session))
            for session in sessions
        ]
        
        print(colored(r"""
         _____   _   _   _____ 
        |  ___| | | | | |  _  |
        | |__   | | | | | | | |
        |  __|  | | | | | | | |
        | |___  | |_| | | |_| |
        \____/   \___/  \_____/
        """, "green"))
        print(colored("🎉 RUX успешно запущен!", "green", attrs=["bold"]))
        print(colored(f"👉 Введите {current_prefix}help для списка модулей", "cyan"))
        print(colored("💡 Совет дня: Не верьте тестерам на 1м курсе", "yellow"))
        
        await asyncio.gather(*userbot_tasks)
        
    except KeyboardInterrupt:
        print(colored("\n🛑 Получен сигнал остановки", "yellow"))
    except Exception as e:
        print(colored(f"❌ Ошибка: {e}", "red"))
    finally:
        if inline_process:
            await cleanup_processes([inline_process])
        print(colored("\n🔴 Система остановлена", "red"))
        print(colored("😴 RUX переходит в спящий режим...", "blue"))

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(colored("\n🛑 Работа завершена", "yellow"))
    except Exception as e:
        print(colored(f"❌ Критическая ошибка: {e}", "red"))