import sqlite3
import os
from config import Config

class Database:
    def __init__(self, db_path=None):
        self.db_path = db_path or Config.DATABASE_URL.replace('sqlite:///', '')
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT, last_name TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)')
        cursor.execute('CREATE TABLE IF NOT EXISTS game_sessions (session_id INTEGER PRIMARY KEY AUTOINCREMENT, chat_id INTEGER, status TEXT DEFAULT "waiting", current_round INTEGER DEFAULT 0, current_situation TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)')
        cursor.execute('CREATE TABLE IF NOT EXISTS game_players (player_id INTEGER PRIMARY KEY AUTOINCREMENT, session_id INTEGER, user_id INTEGER, score INTEGER DEFAULT 0, is_leader INTEGER DEFAULT 0, FOREIGN KEY (session_id) REFERENCES game_sessions (session_id))')
        cursor.execute('CREATE TABLE IF NOT EXISTS player_memes (meme_id INTEGER PRIMARY KEY AUTOINCREMENT, player_id INTEGER, meme_path TEXT, is_used INTEGER DEFAULT 0, FOREIGN KEY (player_id) REFERENCES game_players (player_id))')
        conn.commit()
        conn.close()
    
    def add_user(self, user_id, username, first_name, last_name):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO users (user_id, username, first_name, last_name) VALUES (?, ?, ?, ?)', (user_id, username, first_name, last_name))
        conn.commit()
        conn.close()
    
    def create_game_session(self, chat_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO game_sessions (chat_id, status) VALUES (?, "waiting")', (chat_id,))
        session_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return session_id