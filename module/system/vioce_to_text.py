from module.loader import System
from telethon import events
import asyncio
import os
import tempfile
import speech_recognition as sr

NAME = "Голос в текст"
DESCRIPTION = "Транскрибация аудиосообщений"
EMOJI = "🎤"
AUTHOR = "system"
VERSION = "1.0"

class VoiceToText(System):
    def __init__(self, client, db_path="bot_config/bot_data.db"):
        super().__init__(client, db_path)
        self.name = NAME
        self.description = DESCRIPTION
        self.emoji = EMOJI
        self.author = AUTHOR
        self.version = VERSION
        self.recognizer = sr.Recognizer()
    
    async def v2t_cmd(self, event):
        if not event.is_reply:
            await event.respond("ℹ️ Ответьте на эту команду голосовым сообщением")
            return

        reply = await event.get_reply_message()
        
        if not reply.voice:
            await event.respond("❌ В ответе нет голосового сообщения")
            return

        try:
            voice = await reply.download_media(file=bytes)
            
            with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as tmp:
                tmp.write(voice)
                ogg_path = tmp.name
            
            wav_path = await self._convert_to_wav(ogg_path)
            
            text = await self._recognize_speech(wav_path)
            
            os.unlink(ogg_path)
            os.unlink(wav_path)
            
            await event.respond(f"🔹 Распознанный текст:\n```\n{text}\n```")
            
        except Exception as e:
            await event.respond(f"❌ Ошибка распознавания: {str(e)}")
            if hasattr(self, 'client') and self.client.debug_mode:
                traceback.print_exc()

    async def _convert_to_wav(self, ogg_path):
        wav_path = ogg_path.replace('.ogg', '.wav')
        proc = await asyncio.create_subprocess_shell(
            f'ffmpeg -y -i {ogg_path} -ar 16000 -ac 1 {wav_path}',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await proc.wait()
        return wav_path

    async def _recognize_speech(self, wav_path):
        with sr.AudioFile(wav_path) as source:
            audio = self.recognizer.record(source)
        
        try:
            text = self.recognizer.recognize_google(audio, language='ru-RU')
            return text
        except sr.UnknownValueError:
            return "Не удалось распознать речь"
        except sr.RequestError as e:
            return f"Ошибка сервиса распознавания: {str(e)}"