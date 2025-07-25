# RUX-USERBOT

## 📌 О проекте

RUX UserBot - это мощный модульный юзер бот с открытым исходным кодом, написанный на Python с использованием Telethon и aiogram. Бот предоставляет широкий набор функций для управления чатами, автоматизации задач и развлечения.

## 🌟 Особенности

- **Модульная архитектура** - Легко добавлять и удалять функционал
- **Двойной режим работы** - Поддержка как UserBot, так и обычного бота через inline-режим
- **Безопасность** - Встроенная система проверки целостности файлов

## 🛠 Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/python-backup/Userbot
cd rux-userbot
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Настройте конфигурацию:
- Укажите свои API ID и API Hash от Telegram

4. Запустите бота:
```bash
python main.py
```

## 📂 Структура проекта

```
rux-userbot/
├── core/               # Основные компоненты ядра
├── module/             # Модули бота
│   ├── system/         # Системные модули
│   └── user/           # Пользовательские модули
├── bot_config/         # Конфигурационные файлы и базы данных
├── main.py             # Точка входа
└── inline.py           # Inline-режим бота
```

## 🔧 Доступные модули

### Системные модули (system)
- **AdminGrant** - Управление правами администраторов
- **Backup** - Создание резервных копий файлов и модулей
- **Config** - Управление настройками бота
- **Help** - Система помощи и документации
- **Info** - Информация о системе
- **Installer** - Установка новых модулей
- **Ping** - Проверка соединения
- **Prefix** - Управление префиксом команд
- **Restart** - Перезагрузка бота
- **Session** - Управление сессиями
- **Terminal** - Выполнение команд терминала
- **Uninstaller** - Удаление модулей
- **Updater** - Система обновлений

## 🚀 Использование

Основные команды:
- `!help` - Получить список всех команд
- `!help <модуль>` - Получить справку по конкретному модулю
- `!update` - Проверить и установить обновления

Пример работы с модулями:
```
!install - Установить новый модуль (ответом на файл .py)
!uninstall <название> - Удалить модуль
!backup <файл> - Создать резервную копию файла
!setadmin @username - Назначить администратора
```

## ⚠️ Безопасность

Бот включает несколько уровней защиты:
1. Проверка целостности системных файлов
2. Защита от несанкционированного изменения кода
3. Ограничение доступа к критическим командам
4. Журналирование всех действий�андам
4. Журналирование всех действий�рование всех действий
