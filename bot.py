import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

print("=== Начало загрузки бота ===")

try:
    from database import Database
    print("✅ Database импортирован успешно")
except Exception as e:
    print(f"❌ Ошибка импорта Database: {e}")
    raise

try:
    from config import Config
    print("✅ Config импортирован успешно")
except Exception as e:
    print(f"❌ Ошибка импорта Config: {e}")
    raise

try:
    from file_manager import FileManager
    print("✅ FileManager импортирован успешно")
except Exception as e:
    print(f"❌ Ошибка импорта FileManager: {e}")
    raise

print("=== Все импорты успешны ===")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

class MemesGameBot:
    def __init__(self):
        self.db = Database()
        self.file_manager = FileManager()
        self.active_games = {}
        self.game_messages = {}  # Для хранения ID сообщений игр
    
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
        elif query.data.startswith("begin_"):
            await self.begin_game(query)
    
    async def start_game(self, query):
        chat_id = query.message.chat_id
        user_id = query.from_user.id
        
        # Создаем новую игру
        self.active_games[chat_id] = {
            'players': [user_id],
            'status': 'waiting',
            'leader': user_id,
            'message_id': query.message.message_id
        }
        
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("▶️ Начать игру", callback_data=f"begin_{chat_id}")],
            [InlineKeyboardButton("📋 Правила", callback_data="show_rules")]
        ])
        
        await query.edit_message_text(
            "🎮 Игра создана!\n"
            f"Игроков: 1/{Config.MAX_PLAYERS}\n\n"
            "Отправьте друзьям команду чтобы присоединиться:\n"
            f"/join {chat_id}",
            reply_markup=reply_markup
        )
    
    async def join_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            print(f"🔄 Команда join получена: args={context.args}")
            
            if not context.args:
                await update.message.reply_text("❌ Используйте: /join 123456789")
                return
                
            chat_id = int(context.args[0])
            user = update.effective_user
            
            print(f"🔄 Игрок {user.first_name} пытается присоединиться к игре {chat_id}")
            print(f"🔄 Активные игры: {list(self.active_games.keys())}")
            
            if chat_id not in self.active_games:
                await update.message.reply_text("❌ Игра не найдена! Создайте новую игру через /start")
                return
            
            game = self.active_games[chat_id]
            
            if user.id in game['players']:
                await update.message.reply_text("✅ Вы уже в игре!")
                return
            
            if len(game['players']) >= Config.MAX_PLAYERS:
                await update.message.reply_text("❌ Максимум 8 игроков достигнут!")
                return
            
            # Добавляем игрока
            game['players'].append(user.id)
            self.db.add_user(user.id, user.username, user.first_name, user.last_name)
            
            print(f"✅ Игрок {user.first_name} добавлен в игру {chat_id}")
            print(f"✅ Теперь игроков: {len(game['players'])}")
            
            # Отправляем сообщение игроку
            await update.message.reply_text(
                f"✅ Вы присоединились к игре!\n"
                f"Игроков: {len(game['players'])}/{Config.MAX_PLAYERS}"
            )
            
            # Отправляем сообщение в основной чат игры
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"✅ {user.first_name} присоединился к игре!\n"
                     f"Игроков: {len(game['players'])}/{Config.MAX_PLAYERS}"
            )
            
            # Обновляем сообщение с игрой
            reply_markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("▶️ Начать игру", callback_data=f"begin_{chat_id}")],
                [InlineKeyboardButton("📋 Правила", callback_data="show_rules")]
            ])
            
            try:
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=game['message_id'],
                    text=f"🎮 Игра создана!\nИгроков: {len(game['players'])}/{Config.MAX_PLAYERS}\n\nОтправьте друзьям команду чтобы присоединиться:\n/join {chat_id}",
                    reply_markup=reply_markup
                )
            except Exception as e:
                print(f"⚠️ Не удалось обновить сообщение: {e}")
            
        except ValueError:
            await update.message.reply_text("❌ Используйте: /join 123456789")
        except Exception as e:
            print(f"❌ Ошибка присоединения: {e}")
            await update.message.reply_text("❌ Ошибка присоединения к игре")
    
    async def begin_game(self, query):
        chat_id = int(query.data.split('_')[1])
        game = self.active_games.get(chat_id)
        
        if not game:
            await query.answer("❌ Игра не найдена!")
            return
            
        if len(game['players']) < Config.MIN_PLAYERS:
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
        
        print(f"✅ Выбрана ситуация: {chosen_situation}")
    
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
        logging.error("BOT_TOKEN не найден! Проверьте .env файл")
        return
    
    application = Application.builder().token(Config.BOT_TOKEN).build()
    bot = MemesGameBot()
    
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CommandHandler("join", bot.join_game))
    application.add_handler(CallbackQueryHandler(bot.handle_callback))
    
    print("✅ Бот запускается...")
    application.run_polling()

if __name__ == "__main__":
    main()
