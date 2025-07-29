import subprocess
from typing import List
from termcolor import colored

async def cleanup_processes(processes: list):
    for p in processes:
        try:
            if p and p.poll() is None:
                p.terminate()
                try:
                    p.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    p.kill()
        except Exception as e:
            print(colored(f"Ошибка при завершении процесса: {e}", "red"))