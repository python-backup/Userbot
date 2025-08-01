import asyncio
from termcolor import colored
from core.run import main

if __name__ == "__main__":
    try:
        print(colored("=== Запуск RUX UserBot ===", "blue"))
        os.system('termux-toast "RUX запускается..."')
        asyncio.run(main())
    except KeyboardInterrupt:
        print(colored("\nrux завершил работу", "yellow"))
    except Exception as e:
        print(colored(f"Критическая ошибка: {e}", "red"))