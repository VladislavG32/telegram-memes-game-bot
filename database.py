import sqlite3
import os
from datetime import datetime
from config import Config

class Database:
    def __init__(self, db_path=None):
        self.db_path = db_path or Config.DATABASE_URL.replace('sqlite:///', '')
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Таблица пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                games_played INTEGER DEFAULT 0,
                total_score INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица игровых сессий
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS game_sessions (
                session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                status TEXT DEFAULT 'waiting',
                total_rounds INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица участия в играх
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS game_participation (
                participation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                user_id INTEGER,
                final_score INTEGER DEFAULT 0,
                is_winner INTEGER DEFAULT 0,
                FOREIGN KEY (session_id) REFERENCES game_sessions (session_id),
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # Таблица раундов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS game_rounds (
                round_id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                round_number INTEGER,
                situation TEXT,
                winner_id INTEGER,
                FOREIGN KEY (session_id) REFERENCES game_sessions (session_id),
                FOREIGN KEY (winner_id) REFERENCES users (user_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_user(self, user_id, username, first_name, last_name):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO users (user_id, username, first_name, last_name)
            VALUES (?, ?, ?, ?)
        ''', (user_id, username, first_name, last_name))
        conn.commit()
        conn.close()
    
    def update_user_stats(self, user_id, score_delta=0, games_delta=0):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users 
            SET games_played = games_played + ?, 
                total_score = total_score + ?
            WHERE user_id = ?
        ''', (games_delta, score_delta, user_id))
        conn.commit()
        conn.close()
    
    def create_game_session(self, chat_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO game_sessions (chat_id, status)
            VALUES (?, 'active')
        ''', (chat_id,))
        session_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return session_id
    
    def add_player_to_session(self, session_id, user_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO game_participation (session_id, user_id)
            VALUES (?, ?)
        ''', (session_id, user_id))
        conn.commit()
        conn.close()
    
    def record_round_result(self, session_id, round_number, situation, winner_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO game_rounds (session_id, round_number, situation, winner_id)
            VALUES (?, ?, ?, ?)
        ''', (session_id, round_number, situation, winner_id))
        conn.commit()
        conn.close()
    
    def complete_game_session(self, session_id, final_scores):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Находим победителя
        winner_id = max(final_scores, key=final_scores.get) if final_scores else None
        
        # Обновляем участие игроков
        for user_id, score in final_scores.items():
            is_winner = 1 if user_id == winner_id else 0
            cursor.execute('''
                UPDATE game_participation 
                SET final_score = ?, is_winner = ?
                WHERE session_id = ? AND user_id = ?
            ''', (score, is_winner, session_id, user_id))
            
            # Обновляем статистику пользователя
            self.update_user_stats(user_id, score_delta=score, games_delta=1)
        
        # Обновляем сессию
        cursor.execute('''
            UPDATE game_sessions 
            SET status = 'completed', total_rounds = (
                SELECT COUNT(*) FROM game_rounds WHERE session_id = ?
            )
            WHERE session_id = ?
        ''', (session_id, session_id))
        
        conn.commit()
        conn.close()
    
    def get_user_stats(self, user_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT games_played, total_score FROM users WHERE user_id = ?
        ''', (user_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {'games_played': result[0], 'total_score': result[1]}
        return {'games_played': 0, 'total_score': 0}
    
    def get_leaderboard(self, limit=10):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT user_id, username, first_name, total_score, games_played
            FROM users 
            WHERE games_played > 0
            ORDER BY total_score DESC 
            LIMIT ?
        ''', (limit,))
        
        leaderboard = []
        for row in cursor.fetchall():
            leaderboard.append({
                'user_id': row[0],
                'username': row[1],
                'first_name': row[2],
                'total_score': row[3],
                'games_played': row[4]
            })
        
        conn.close()
        return leaderboard
