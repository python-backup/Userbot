import os
import sys
import subprocess
import shutil
import requests
from termcolor import colored
from telethon.tl.types import Message
from module.loader import System
from git import Repo, GitCommandError
from git.exc import InvalidGitRepositoryError, NoSuchPathError

class Updater(System):
    NAME = "Updater"
    DESCRIPTION = "Система обновления юзер-бота"
    EMOJI = "🔄"
    AUTHOR = "System"
    VERSION="18"
    
    def __init__(self, client, db_path: str = 'bot_config/bot_data.db'):
        super().__init__(client, db_path)
        self.repo_url = "https://github.com/python-backup/Userbot.git"
        self.version_url = "https://raw.githubusercontent.com/python-backup/Userbot/main/Version.txt"
        self.changelog_url = "https://raw.githubusercontent.com/python-backup/Userbot/main/CHANGELOG.md"
        self.git_installed = self._check_gitpython()
        self._fix_git_safety()
        self.repo = self._get_repo()
        self.current_branch = self._get_current_branch()
        self.local_ver = self._get_local_version()

    def _check_gitpython(self) -> bool:
        try:
            import git
            return True
        except ImportError:
            print(colored("GitPython не найден, пытаюсь установить...", "yellow"))
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "gitpython"])
                import git
                print(colored("GitPython успешно установлен!", "green"))
                return True
            except Exception as e:
                print(colored(f"Ошибка установки GitPython: {e}", "red"))
                return False

    def _fix_git_safety(self):
        try:
            repo_path = os.getcwd()
            subprocess.run(
                ["git", "config", "--global", "--add", "safe.directory", repo_path],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            print(colored(f"Добавлен безопасный каталог: {repo_path}", "green"))
        except Exception as e:
            print(colored(f"Не удалось добавить безопасный каталог: {e}", "yellow"))

    def _get_repo(self):
        if not self.git_installed:
            return None
        
        try:
            repo = Repo(os.getcwd())
            repo.git.status()
            return repo
        except (InvalidGitRepositoryError, NoSuchPathError, GitCommandError) as e:
            print(colored(f"Ошибка доступа к репозиторию: {e}", "yellow"))
            return None

    def _get_local_version(self) -> str:
        version_file = os.path.join(os.getcwd(), "Version.txt")
        if os.path.exists(version_file):
            with open(version_file, "r") as f:
                return f.read().strip()
        return "unknown"

    def _get_current_branch(self) -> str:
        if not self.repo:
            return "unknown"
        
        try:
            if self.repo.head.is_detached:
                return "detached"
            return self.repo.active_branch.name
        except Exception:
            return "unknown"

    async def _get_remote_version(self) -> str:
        try:
            response = requests.get(self.version_url)
            response.raise_for_status()
            return response.text.strip()
        except Exception as e:
            print(colored(f"Ошибка получения удалённой версии: {e}", "red"))
            return "unknown"

    async def _check_update(self) -> tuple:
        try:
            remote_ver = await self._get_remote_version()
            if remote_ver == "unknown":
                return (False, "error", self.local_ver, "unknown")
                
            has_update = remote_ver != self.local_ver
            return (has_update, "version", self.local_ver, remote_ver)
        except Exception as e:
            print(colored(f"Ошибка проверки обновления: {e}", "red"))
            return (False, "error", self.local_ver, "unknown")

    async def _get_remote_commit_info(self) -> str:
        if not self.repo:
            return "unknown"
        
        try:
            remote_name = "origin"
            branch_name = self.current_branch if self.current_branch != "unknown" else "main"
            
            # Получаем информацию о удаленном репозитории
            remote = self.repo.remote(remote_name)
            remote.fetch()
            
            # Получаем ссылку на удаленную ветку
            remote_ref = f"{remote_name}/{branch_name}"
            if remote_ref not in self.repo.references:
                return "unknown"
                
            # Получаем последний коммит из удаленной ветки
            remote_commit = self.repo.commit(remote_ref)
            return remote_commit.message.split('\n')[0]
        except Exception as e:
            print(colored(f"Ошибка получения информации о коммите: {e}", "yellow"))
            return "unknown"

    async def update_cmd(self, event: Message):
        if not self.git_installed:
            await event.reply(
                "❌ <b>GitPython не установлен!</b>\n"
                "Установите вручную: <code>pip install gitpython</code>",
                parse_mode='html'
            )
            return

        msg = await event.reply("<i>⏳ Начинаю процесс обновления...</i>", parse_mode='html')

        try:
            temp_dir = "temp_repo_update"
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

            repo = Repo.clone_from(
                self.repo_url,
                temp_dir,
                branch="main",
                depth=1,
                single_branch=True
            )

            exclude = ["config_ex.py", "bot_config", "__pycache__"]
            for item in os.listdir(temp_dir):
                if item in exclude:
                    continue

                src = os.path.join(temp_dir, item)
                dst = os.path.join(os.getcwd(), item)

                if os.path.isdir(src):
                    if os.path.exists(dst):
                        shutil.rmtree(dst)
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)

            shutil.rmtree(temp_dir, ignore_errors=True)

            await msg.edit(
                "<b>✅ Обновление успешно завершено!</b>\n"
                "<i>Для применения изменений перезапустите бота</i>",
                parse_mode='html'
            )

        except GitCommandError as e:
            await msg.edit(
                f"<b>❌ Ошибка Git:</b>\n<code>{str(e)}</code>",
                parse_mode='html'
            )
            print(colored(f"Git Error: {str(e)}", "red"))
        except Exception as e:
            await msg.edit(
                f"<b>❌ Критическая ошибка:</b>\n<code>{str(e)}</code>",
                parse_mode='html'
            )
            print(colored(f"Update Error: {str(e)}", "red"))

    async def _get_update_info(self) -> str:
        try:
            response = requests.get(self.changelog_url)
            response.raise_for_status()
            text = response.text
            return text[:1000] + ("..." if len(text) > 1000 else "")
        except Exception as e:
            print(colored(f"Ошибка получения changelog: {e}", "yellow"))
            return "Информация об обновлении недоступна"