import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from database import Database
from config import Config

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

class MemesGameBot:
    def __init__(self):
        self.db = Database()
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        self.db.add_user(user.id, user.username, user.first_name, user.last_name)
        keyboard = [[InlineKeyboardButton("Start game", callback_data="start_game")]]
        await update.message.reply_text(f"Hello {user.first_name}!", reply_markup=InlineKeyboardMarkup(keyboard))
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        await query.edit_message_text("Game started!")

def main():
    if not Config.BOT_TOKEN:
        logging.error("No BOT_TOKEN!")
        return
    application = Application.builder().token(Config.BOT_TOKEN).build()
    bot = MemesGameBot()
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CallbackQueryHandler(bot.handle_callback))
    application.run_polling()

if __name__ == "__main__":
    main()