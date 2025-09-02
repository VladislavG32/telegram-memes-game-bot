import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from database import Database
from file_manager import FileManager
from config import Config

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

class MemesGameBot:
    def __init__(self):
        self.db = Database()
        self.file_manager = FileManager()
        self.active_games = {}
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        chat_id = update.effective_chat.id
        
        self.db.add_user(user.id, user.username, user.first_name, user.last_name)
        
        keyboard = [
            [InlineKeyboardButton("🎮 Начать игру", callback_data="start_game")],
            [InlineKeyboardButton("📋 Правила", callback_data="show_rules")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"Привет, {user.first_name}! 👋\n"
            "Добро пожаловать в игру 'Мемы по ситуации'!\n\n"
            "Собери 2-8 друзей и начните веселье!",
            reply_markup=reply_markup
        )
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        
        if query.data == "start_game":
            await self.start_game(query)
        elif query.data == "show_rules":
            await self.show_rules(query)
        elif query.data.startswith("situation_"):
            await self.choose_situation(query)
    
    async def start_game(self, query):
        chat_id = query.message.chat_id
        user_id = query.from_user.id
        
        # Создаем новую игру
        self.active_games[chat_id] = {
            'players': [user_id],
            'status': 'waiting',
            'leader': user_id
        }
        
        await query.edit_message_text(
            "🎮 Игра создана!\n"
            f"Игроков: 1/{Config.MAX_PLAYERS}\n\n"
            "Отправьте друзьям команду чтобы присоединиться:\n"
            f"/join_{chat_id}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("▶️ Начать игру", callback_data=f"begin_{chat_id}")]
            ])
        )
    
    async def join_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            chat_id = int(context.args[0])
            user = update.effective_user
            
            if chat_id not in self.active_games:
                await update.message.reply_text("❌ Игра не найдена!")
                return
            
            game = self.active_games[chat_id]
            
            if user.id in game['players']:
                await update.message.reply_text("✅ Вы уже в игре!")
                return
            
            if len(game['players']) >= Config.MAX_PLAYERS:
                await update.message.reply_text("❌ Максимум игроков достигнут!")
                return
            
            game['players'].append(user.id)
            self.db.add_user(user.id, user.username, user.first_name, user.last_name)
            
            await update.message.reply_text(
                f"✅ {user.first_name} присоединился к игре!\n"
                f"Игроков: {len(game['players'])}/{Config.MAX_PLAYERS}"
            )
            
        except (IndexError, ValueError):
            await update.message.reply_text("❌ Используйте: /join_123456789")
    
    async def begin_game(self, query):
        chat_id = query.message.chat_id
        game = self.active_games.get(chat_id)
        
        if not game or len(game['players']) < Config.MIN_PLAYERS:
            await query.answer("❌ Нужно минимум 2 игрока!")
            return
        
        # Получаем случайные ситуации
        situations = self.file_manager.get_random_situations(Config.SITUATIONS_TO_CHOOSE)
        game['situations'] = situations
        game['status'] = 'choosing_situation'
        
        # Создаем клавиатуру с ситуациями
        keyboard = []
        for i, situation in enumerate(situations):
            keyboard.append([InlineKeyboardButton(
                situation[:40] + "..." if len(situation) > 40 else situation,
                callback_data=f"situation_{i}"
            )])
        
        await query.edit_message_text(
            "📝 Ведущий, выберите ситуацию для раунда:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def choose_situation(self, query):
        chat_id = query.message.chat_id
        game = self.active_games.get(chat_id)
        
        if not game or query.from_user.id != game['leader']:
            await query.answer("❌ Только ведущий может выбирать!")
            return
        
        situation_index = int(query.data.split('_')[1])
        chosen_situation = game['situations'][situation_index]
        game['current_situation'] = chosen_situation
        game['status'] = 'players_choosing'
        
        # Отправляем ситуацию всем
        await query.edit_message_text(
            f"🎲 СИТУАЦИЯ РАУНДА:\n\n{chosen_situation}\n\n"
            "Игроки выбирают мемы...",
            reply_markup=None
        )
        
        # TODO: Раздать мемы игрокам и обработать выбор
    
    async def show_rules(self, query):
        rules_text = """
📋 ПРАВИЛА ИГРЫ:

👥 Игроков: 2-8 человек
🃏 Каждый получает по 6 карточек с мемами
👑 Первый ведущий - создатель игры
📖 Ведущий выбирает и зачитывает ситуацию
😂 Игроки выбирают самый подходящий мем
🏆 Ведущий выбирает победителя раунда
🔄 Ведущий меняется каждый раунд
🎯 Побеждает набравший больше всего очков

🎥 Мемы могут быть как фото, так и видео!
        """
        await query.edit_message_text(rules_text)

def main():
    if not Config.BOT_TOKEN:
        logging.error("BOT_TOKEN не найден!")
        return
    
    application = Application.builder().token(Config.BOT_TOKEN).build()
    bot = MemesGameBot()
    
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CommandHandler("join", bot.join_game))
    application.add_handler(CallbackQueryHandler(bot.handle_callback))
    
    application.run_polling()

if __name__ == "__main__":
    main()