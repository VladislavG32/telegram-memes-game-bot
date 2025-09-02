import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    MAX_PLAYERS = 8
    MIN_PLAYERS = 2
    MEMES_PER_PLAYER = 6
    SITUATIONS_TO_CHOOSE = 10
    ROUND_DURATION = 120
    MEMES_DIR = os.path.join('data', 'memes')
    SITUATIONS_FILE = os.path.join('data', 'situations.txt')
    USED_MEMES_FILE = os.path.join('data', 'used_memes.json')
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///game.db')