import sqlite3
from typing import Dict, List, Optional, Tuple
from core.config import DATABASE_FILE

def ensure_db_exists():
    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS telegram_config (
                session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                api_id INTEGER NOT NULL,
                api_hash TEXT NOT NULL,
                phone_number TEXT NOT NULL,
                session_name TEXT UNIQUE NOT NULL,
                password TEXT,
                is_active INTEGER DEFAULT 1
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admins (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                session_id INTEGER,
                FOREIGN KEY(session_id) REFERENCES telegram_config(session_id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inline_bots (
                bot_id INTEGER PRIMARY KEY AUTOINCREMENT,
                bot_token TEXT UNIQUE NOT NULL,
                bot_username TEXT UNIQUE,
                is_active INTEGER DEFAULT 1
            )
        ''')
        conn.commit()

def migrate_db():
    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(admins)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'session_id' not in columns:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS admins_new (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    session_id INTEGER,
                    FOREIGN KEY(session_id) REFERENCES telegram_config(session_id)
                )
            ''')
            cursor.execute('''
                INSERT INTO admins_new (user_id, username)
                SELECT user_id, username FROM admins
            ''')
            cursor.execute('DROP TABLE admins')
            cursor.execute('ALTER TABLE admins_new RENAME TO admins')
            conn.commit()

def get_sessions() -> List[Dict]:
    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT session_id, api_id, api_hash, phone_number, session_name, password "
            "FROM telegram_config WHERE is_active = 1"
        )
        return [
            {
                'session_id': row[0],
                'api_id': row[1],
                'api_hash': row[2],
                'phone': row[3],
                'session_name': row[4],
                'password': row[5]
            } for row in cursor.fetchall()
        ]

def get_inline_bot_token() -> Optional[str]:
    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT bot_token FROM inline_bots WHERE is_active = 1 LIMIT 1"
        )
        result = cursor.fetchone()
        return result[0] if result else None

def get_inline_bot_username() -> Optional[str]:
    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT bot_username FROM inline_bots WHERE is_active = 1 LIMIT 1"
        )
        result = cursor.fetchone()
        return result[0] if result else None

def add_inline_bot(token: str, username: Optional[str] = None) -> bool:
    try:
        with sqlite3.connect(DATABASE_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO inline_bots (bot_token, bot_username) VALUES (?, ?)",
                (token, username)
            )
            conn.commit()
            return True
    except sqlite3.IntegrityError:
        return False
    except sqlite3.Error:
        return False

def update_inline_bot_username(username: str) -> bool:
    try:
        with sqlite3.connect(DATABASE_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE inline_bots SET bot_username = ? WHERE is_active = 1",
                (username,)
            )
            conn.commit()
            return cursor.rowcount > 0
    except sqlite3.Error:
        return False

def deactivate_all_inline_bots():
    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE inline_bots SET is_active = 0"
        )
        conn.commit()

def get_active_inline_bot() -> Optional[Dict]:
    with sqlite3.connect(DATABASE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT bot_token, bot_username FROM inline_bots WHERE is_active = 1 LIMIT 1"
        )
        result = cursor.fetchone()
        if result:
            return {
                'token': result[0],
                'username': result[1]
            }
        return None