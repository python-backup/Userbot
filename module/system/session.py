# module/system/session.py
import os
from telethon import errors
from telethon.sync import TelegramClient
from main import SessionManager, generate_session_name
from module.loader import System

NAME = "Управление сессиями"
DESCRIPTION = "Добавление, удаление и просмотр сессий бота"
EMOJI = "🔄"
VERSION = "1.0"
AUTHOR = "system"

class Session(System):
    """Управление сессиями бота"""
    
    def __init__(self, client, db_path):
        super().__init__(client, db_path)
        self.name = NAME
        self.description = DESCRIPTION
        self.emoji = EMOJI
        self.author = AUTHOR
        self.version = VERSION
        self.manager = SessionManager(db_path)
        self.active_auth = {}  # {chat_id: {'state': str, 'client': TelegramClient, ...}}
        self.session_dir = "bot_config"  # Унифицированный путь
        
        os.makedirs(self.session_dir, exist_ok=True)

    async def _create_client(self, session_name, api_id, api_hash):
        """Создает клиента с отключенным интерактивным вводом"""
        session_file = os.path.join(self.session_dir, f"session_{session_name}")
        client = TelegramClient(
            session=session_file,
            api_id=api_id,
            api_hash=api_hash,
            device_model="UserBot (Non-Interactive)"
        )
        client.flood_sleep_threshold = 0
        client.parse_mode = 'html'
        return client

    async def session_add_cmd(self, event):
        """!sessionadd - Добавить новую сессию (ответьте на сообщение с данными)"""
        if not (reply_msg := await event.get_reply_message()):
            await event.respond("Ответьте на сообщение с данными в формате:\n"
                              "API_ID API_HASH НОМЕР_ТЕЛЕФОНА [ПАРОЛЬ_2FA]")
            return
        
        try:
            parts = reply_msg.text.split()
            if len(parts) < 3:
                raise ValueError("Неверный формат данных")
            
            api_id = int(parts[0])
            api_hash = parts[1]
            phone = parts[2]
            password = parts[3] if len(parts) > 3 else None
            
            session_name = generate_session_name()
            client = await self._create_client(session_name, api_id, api_hash)
            await client.connect()
            
            # Проверяем, не авторизован ли уже клиент
            if await client.is_user_authorized():
                await event.respond("ℹ️ Этот аккаунт уже авторизован! Завершаем процесс...")
                await self._finalize_session(event, {
                    'client': client,
                    'api_id': api_id,
                    'api_hash': api_hash,
                    'phone': phone,
                    'password': password,
                    'session_name': session_name
                })
                return
            
            self.active_auth[event.chat_id] = {
                'state': 'awaiting_code',
                'client': client,
                'api_id': api_id,
                'api_hash': api_hash,
                'phone': phone,
                'password': password,
                'session_name': session_name
            }
            
            sent_code = await client.send_code_request(phone)
            self.active_auth[event.chat_id]['phone_code_hash'] = sent_code.phone_code_hash
            
            await event.respond(
                "📲 Код подтверждения отправлен.\n"
                "Введите команду: `!code X-X-X-X-X`\n"
                "(где X-X-X-X-X - код из 5 цифр)"
            )

        except Exception as e:
            await event.respond(f"❌ Ошибка: {str(e)}")
            if event.chat_id in self.active_auth:
                await self._cleanup_auth(event.chat_id)

    async def code_cmd(self, event):
        """!code - Ввести код подтверждения для авторизации сессии"""
        if event.chat_id not in self.active_auth or self.active_auth[event.chat_id]['state'] != 'awaiting_code':
            await event.respond("❌ Нет активного процесса авторизации или неверный этап")
            return
        
        try:
            code = event.pattern_match.group(1).strip().replace('-', '')
            if not code.isdigit() or len(code) != 5:
                raise ValueError("Код должен состоять из 5 цифр (формат: X-X-X-X-X)")
            
            auth_data = self.active_auth[event.chat_id]
            client = auth_data['client']
            
            # Дополнительная проверка авторизации
            if await client.is_user_authorized():
                await event.respond("ℹ️ Бот уже авторизован! Завершаем процесс...")
                await self._finalize_session(event, auth_data)
                return
            
            try:
                await client.sign_in(
                    auth_data['phone'],
                    code=code,
                    phone_code_hash=auth_data['phone_code_hash']
                )
                await event.respond("✅ Код принят! Завершаем авторизацию...")
                
            except errors.SessionPasswordNeededError:
                if not auth_data.get('password'):
                    await event.respond(
                        "🔒 Требуется пароль двухфакторной аутентификации.\n"
                        "Введите команду: `!password ваш_пароль`"
                    )
                    self.active_auth[event.chat_id]['state'] = 'awaiting_password'
                    return
                
                await client.sign_in(password=auth_data['password'])
                await event.respond("✅ Пароль принят! Завершаем авторизацию...")
            
            await self._finalize_session(event, auth_data)
            
        except Exception as e:
            await event.respond(f"❌ Ошибка: {str(e)}")
            await self._cleanup_auth(event.chat_id)

    async def password_cmd(self, event):
        """!password - Ввести пароль 2FA для завершения авторизации"""
        if (event.chat_id not in self.active_auth or 
            self.active_auth[event.chat_id]['state'] != 'awaiting_password'):
            await event.respond("❌ Нет активного процесса авторизации, требующего пароль")
            return
        
        try:
            password = event.pattern_match.group(1).strip()
            if not password:
                raise ValueError("Пароль не может быть пустым")
            
            auth_data = self.active_auth[event.chat_id]
            client = auth_data['client']
            auth_data['password'] = password
            
            await client.sign_in(password=password)
            await event.respond("✅ Пароль принят! Завершаем авторизацию...")
            await self._finalize_session(event, auth_data)
            
        except Exception as e:
            await event.respond(f"❌ Ошибка: {str(e)}")
            await self._cleanup_auth(event.chat_id)

    async def _finalize_session(self, event, auth_data):
        """Завершает процесс авторизации и сохраняет сессию"""
        client = auth_data['client']
        session_file = os.path.join(self.session_dir, f"session_{auth_data['session_name']}")
        
        try:
            if not await client.is_user_authorized():
                raise Exception("Сессия не авторизована")
            
            me = await client.get_me()
            session_data = self.manager.add_session(
                api_id=auth_data['api_id'],
                api_hash=auth_data['api_hash'],
                phone=auth_data['phone'],
                session_name=auth_data['session_name'],
                password=auth_data.get('password')
            )
            
            await event.respond(
                f"✅ Авторизация успешно завершена!\n\n"
                f"🔹 <b>Имя сессии:</b> {session_data['session_name']}\n"
                f"🔹 <b>ID сессии:</b> {session_data['session_id']}\n"
                f"🔹 <b>Пользователь:</b> @{me.username}\n"
                f"🔹 <b>Номер телефона:</b> {session_data['phone']}\n\n"
                f"Бот готов к работе! 🚀"
            )
            
        except Exception as e:
            await event.respond(f"❌ Ошибка при завершении авторизации: {str(e)}")
            if os.path.exists(f"{session_file}.session"):
                os.remove(f"{session_file}.session")
        finally:
            if event.chat_id in self.active_auth:
                del self.active_auth[event.chat_id]
            if client.is_connected():
                await client.disconnect()

    async def _cleanup_auth(self, chat_id):
        """Очищает данные авторизации"""
        if chat_id in self.active_auth:
            auth_data = self.active_auth[chat_id]
            if 'client' in auth_data and auth_data['client'].is_connected():
                await auth_data['client'].disconnect()
            if 'session_name' in auth_data:
                session_file = os.path.join(self.session_dir, f"session_{auth_data['session_name']}")
                if os.path.exists(f"{session_file}.session"):
                    os.remove(f"{session_file}.session")
            del self.active_auth[chat_id]