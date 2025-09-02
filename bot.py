import logging
import os
import random
import uuid
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, InputMediaVideo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

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
        self.user_sessions = {}  # Для хранения текущих мемов пользователя
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        chat_id = update.effective_chat.id
        
        self.db.add_user(user.id, user.username, user.first_name, user.last_name)
        
        keyboard = [
            [InlineKeyboardButton("🎮 Начать игру", callback_data="start_game")],
            [InlineKeyboardButton("📋 Правила", callback_data="show_rules")],
            [InlineKeyboardButton("📊 Статистика", callback_data="show_stats")],
            [InlineKeyboardButton("🏆 Лидерборд", callback_data="show_leaderboard")]
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
        
        callback_data = query.data
        
        if callback_data == "start_game":
            await self.start_game(query)
        elif callback_data == "show_rules":
            await self.show_rules(query)
        elif callback_data == "show_stats":
            await self.show_stats(query)
        elif callback_data == "show_leaderboard":
            await self.show_leaderboard(query)
        elif callback_data.startswith("situation_"):
            await self.choose_situation(query)
        elif callback_data.startswith("begin_"):
            await self.begin_game(query)
        elif callback_data.startswith("memechoice_"):
            await self.handle_meme_choice(query)
        elif callback_data.startswith("vote_"):
            await self.handle_vote(query)
        elif callback_data.startswith("nextround_"):
            await self.next_round(query)
        elif callback_data.startswith("endgame_"):
            await self.end_game(query)
    
    async def start_game(self, query):
        chat_id = query.message.chat_id
        user_id = query.from_user.id
        
        # Создаем новую игру
        self.active_games[chat_id] = {
            'players': [user_id],
            'player_names': {user_id: query.from_user.first_name},
            'status': 'waiting',
            'leader': user_id,
            'round_number': 0,
            'scores': {user_id: 0},
            'submitted_memes': {},
            'voting_options': {},
            'message_id': query.message.message_id
        }
        
        await query.edit_message_text(
            "🎮 Игра создана!\n"
            f"Игроков: 1/{Config.MAX_PLAYERS}\n\n"
            "Отправьте друзьям команду чтобы присоединиться:\n"
            f"/join_{chat_id}\n\n"
            "Когда все присоединятся, нажмите 'Начать игру'",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("▶️ Начать игру", callback_data=f"begin_{chat_id}")],
                [InlineKeyboardButton("❌ Отменить игру", callback_data=f"endgame_{chat_id}")]
            ])
        )
    
    async def join_game(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            if not context.args:
                await update.message.reply_text("❌ Используйте: /join_123456789")
                return
                
            chat_id = int(context.args[0])
            user = update.effective_user
            
            print(f"🔄 Игрок {user.first_name} пытается присоединиться к игре {chat_id}")
            
            if chat_id not in self.active_games:
                await update.message.reply_text("❌ Игра не найдена или уже завершена!")
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
            game['player_names'][user.id] = user.first_name
            game['scores'][user.id] = 0
            self.db.add_user(user.id, user.username, user.first_name, user.last_name)
            
            print(f"✅ Игрок {user.first_name} добавлен в игру {chat_id}")
            
            # Обновляем сообщение о создании игры
            try:
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=game.get('message_id'),
                    text=f"🎮 Игра создана!\nИгроков: {len(game['players'])}/{Config.MAX_PLAYERS}\n\n"
                         f"Отправьте друзьям команду: /join_{chat_id}\n\n"
                         "Когда все присоединятся, нажмите 'Начать игру'",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("▶️ Начать игру", callback_data=f"begin_{chat_id}")],
                        [InlineKeyboardButton("❌ Отменить игру", callback_data=f"endgame_{chat_id}")]
                    ])
                )
            except Exception as e:
                print(f"❌ Ошибка обновления сообщения: {e}")
            
            await update.message.reply_text(
                f"✅ {user.first_name} присоединился к игре!\n"
                f"Игроков: {len(game['players'])}/{Config.MAX_PLAYERS}"
            )
            
        except ValueError:
            await update.message.reply_text("❌ Используйте: /join_123456789")
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
        
        game['round_number'] = 1
        game['status'] = 'choosing_situation'
        
        # Получаем случайные ситуации
        situations = self.file_manager.get_random_situations(Config.SITUATIONS_TO_CHOOSE)
        game['situations'] = situations
        
        # Создаем клавиатуру с ситуациями
        keyboard = []
        for i, situation in enumerate(situations):
            keyboard.append([InlineKeyboardButton(
                situation[:40] + "..." if len(situation) > 40 else situation,
                callback_data=f"situation_{i}"
            )])
        
        leader_name = game['player_names'][game['leader']]
        
        await query.edit_message_text(
            f"📝 {leader_name}, выберите ситуацию для раунда {game['round_number']}:",
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
        game['submitted_memes'] = {}  # user_id -> meme_data
        
        # Отправляем ситуацию всем в чате
        await query.edit_message_text(
            f"🎲 РАУНД {game['round_number']} - СИТУАЦИЯ:\n\n{chosen_situation}\n\n"
            "Игроки выбирают мемы...",
            reply_markup=None
        )
        
        # Раздаем мемы каждому игроку в ЛС
        for player_id in game['players']:
            if player_id != game['leader']:  # Ведущий не выбирает мем
                await self.distribute_memes_to_player(chat_id, player_id, query.message.bot)
        
        print(f"✅ Выбрана ситуация: {chosen_situation}")
    
    async def distribute_memes_to_player(self, chat_id, player_id, bot):
        try:
            # Получаем случайные мемы для игрока
            memes = self.file_manager.get_random_memes(Config.MEMES_PER_PLAYER)
            
            if not memes:
                await bot.send_message(
                    player_id,
                    "❌ В базе закончились мемы! Добавьте новые мемы в папку data/memes/"
                )
                return
            
            # Сохраняем мемы для этого игрока
            if player_id not in self.user_sessions:
                self.user_sessions[player_id] = {}
            
            self.user_sessions[player_id][chat_id] = memes
            
            # Отправляем сообщение с кнопками для выбора мема
            keyboard = []
            for i, meme in enumerate(memes):
                keyboard.append([InlineKeyboardButton(
                    f"Мем {i+1}", 
                    callback_data=f"memechoice_{chat_id}_{i}"
                )])
            
            # Отправляем каждый мем как медиа
            media_group = []
            for i, meme in enumerate(memes):
                file_path = meme['path']
                if meme['filename'].lower().endswith(('.mp4', '.mov', '.avi')):
                    media = InputMediaVideo(media=open(file_path, 'rb'), caption=f"Мем {i+1}" if i == 0 else "")
                else:
                    media = InputMediaPhoto(media=open(file_path, 'rb'), caption=f"Мем {i+1}" if i == 0 else "")
                media_group.append(media)
            
            # Отправляем медиагруппу
            await bot.send_media_group(player_id, media=media_group)
            
            # Отправляем кнопки для выбора
            await bot.send_message(
                player_id,
                f"🎲 Выберите мем для ситуации:\n\n{self.active_games[chat_id]['current_situation']}",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
        except Exception as e:
            print(f"❌ Ошибка отправки мемов игроку {player_id}: {e}")
            await bot.send_message(
                player_id,
                "❌ Произошла ошибка при загрузке мемов. Попробуйте позже."
            )
    
    async def handle_meme_choice(self, query):
        try:
            data_parts = query.data.split('_')
            chat_id = int(data_parts[1])
            meme_index = int(data_parts[2])
            user_id = query.from_user.id
            
            game = self.active_games.get(chat_id)
            if not game or game['status'] != 'players_choosing':
                await query.answer("❌ Время выбора мемов истекло!")
                return
            
            if user_id in game['submitted_memes']:
                await query.answer("❌ Вы уже отправили мем!")
                return
            
            # Получаем выбранный мем
            user_memes = self.user_sessions.get(user_id, {}).get(chat_id, [])
            if not user_memes or meme_index >= len(user_memes):
                await query.answer("❌ Ошибка выбора мема!")
                return
            
            selected_meme = user_memes[meme_index]
            
            # Сохраняем выбор игрока
            game['submitted_memes'][user_id] = {
                'meme': selected_meme,
                'player_name': game['player_names'][user_id]
            }
            
            await query.answer(f"✅ Вы выбрали мем {meme_index + 1}!")
            await query.edit_message_text("✅ Ваш мем отправлен! Ждем других игроков...")
            
            # Проверяем, все ли игроки сделали выбор (кроме ведущего)
            expected_players = len(game['players']) - 1  # Все кроме ведущего
            if len(game['submitted_memes']) >= expected_players:
                await self.start_voting(chat_id, query.message.bot)
                
        except Exception as e:
            print(f"❌ Ошибка обработки выбора мема: {e}")
            await query.answer("❌ Ошибка выбора мема!")
    
    async def start_voting(self, chat_id, bot):
        game = self.active_games[chat_id]
        game['status'] = 'voting'
        
        # Отправляем все мемы ведущему для голосования
        leader_id = game['leader']
        
        if not game['submitted_memes']:
            await bot.send_message(chat_id, "❌ Никто не отправил мемы! Раунд пропущен.")
            await self.next_round_auto(chat_id, bot)
            return
        
        # Отправляем каждый мем ведущему
        voting_options = {}
        media_group = []
        
        for i, (user_id, meme_data) in enumerate(game['submitted_memes'].items()):
            meme = meme_data['meme']
            player_name = meme_data['player_name']
            option_id = str(uuid.uuid4())[:8]  # Уникальный ID для варианта голосования
            voting_options[option_id] = user_id
            
            caption = f"🎭 Вариант от {player_name}" if i == 0 else ""
            
            if meme['filename'].lower().endswith(('.mp4', '.mov', '.avi')):
                media = InputMediaVideo(media=open(meme['path'], 'rb'), caption=caption)
            else:
                media = InputMediaPhoto(media=open(meme['path'], 'rb'), caption=caption)
            
            media_group.append(media)
        
        game['voting_options'] = voting_options
        
        # Отправляем медиагруппу
        await bot.send_media_group(leader_id, media=media_group)
        
        # Создаем клавиатуру для голосования
        keyboard = []
        temp_row = []
        for i, option_id in enumerate(voting_options.keys()):
            temp_row.append(InlineKeyboardButton(f"🎯 {i+1}", callback_data=f"vote_{chat_id}_{option_id}"))
            if len(temp_row) >= 3:  # 3 кнопки в ряд
                keyboard.append(temp_row)
                temp_row = []
        if temp_row:
            keyboard.append(temp_row)
        
        await bot.send_message(
            leader_id,
            f"📊 {game['player_names'][leader_id]}, выберите самый смешной мем для ситуации:\n\n{game['current_situation']}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        # Уведомляем всех в основном чате
        await bot.send_message(
            chat_id,
            "📊 Все мемы отправлены! Ведущий выбирает победителя..."
        )
    
    async def handle_vote(self, query):
        try:
            data_parts = query.data.split('_')
            chat_id = int(data_parts[1])
            option_id = data_parts[2]
            voter_id = query.from_user.id
            
            game = self.active_games.get(chat_id)
            if not game or game['status'] != 'voting':
                await query.answer("❌ Голосование завершено!")
                return
            
            if voter_id != game['leader']:
                await query.answer("❌ Только ведущий может голосовать!")
                return
            
            if option_id not in game['voting_options']:
                await query.answer("❌ Неверный вариант!")
                return
            
            # Находим победителя
            winner_id = game['voting_options'][option_id]
            winner_name = game['player_names'][winner_id]
            
            # Обновляем счет
            game['scores'][winner_id] = game['scores'].get(winner_id, 0) + 1
            
            # Отправляем результаты в чат
            winner_meme = game['submitted_memes'][winner_id]['meme']
            
            if winner_meme['filename'].lower().endswith(('.mp4', '.mov', '.avi')):
                await query.message.bot.send_video(
                    chat_id,
                    video=open(winner_meme['path'], 'rb'),
                    caption=f"🏆 ПОБЕДИТЕЛЬ РАУНДА: {winner_name}!\n\n"
                           f"Ситуация: {game['current_situation']}\n\n"
                           f"💯 Текущие очки:\n" + 
                           "\n".join([f"{name}: {score}" for name, score in sorted(
                               [(game['player_names'][pid], score) for pid, score in game['scores'].items()],
                               key=lambda x: x[1], reverse=True
                           )])
                )
            else:
                await query.message.bot.send_photo(
                    chat_id,
                    photo=open(winner_meme['path'], 'rb'),
                    caption=f"🏆 ПОБЕДИТЕЛЬ РАУНДА: {winner_name}!\n\n"
                           f"Ситуация: {game['current_situation']}\n\n"
                           f"💯 Текущие очки:\n" + 
                           "\n".join([f"{name}: {score}" for name, score in sorted(
                               [(game['player_names'][pid], score) for pid, score in game['scores'].items()],
                               key=lambda x: x[1], reverse=True
                           )])
                )
            
            # Предлагаем начать следующий раунд
            game['status'] = 'round_complete'
            
            keyboard = [
                [InlineKeyboardButton("➡️ Следующий раунд", callback_data=f"nextround_{chat_id}")],
                [InlineKeyboardButton("🏁 Завершить игру", callback_data=f"endgame_{chat_id}")]
            ]
            
            await query.edit_message_text(
                "✅ Голосование завершено!",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
        except Exception as e:
            print(f"❌ Ошибка обработки голоса: {e}")
            await query.answer("❌ Ошибка голосования!")
    
    async def next_round(self, query):
        chat_id = int(query.data.split('_')[1])
        await self.next_round_auto(chat_id, query.message.bot)
        await query.answer("🔄 Подготовка следующего раунда...")
    
    async def next_round_auto(self, chat_id, bot):
        game = self.active_games.get(chat_id)
        if not game:
            return
        
        # Меняем ведущего по кругу
        current_leader_index = game['players'].index(game['leader'])
        next_leader_index = (current_leader_index + 1) % len(game['players'])
        game['leader'] = game['players'][next_leader_index]
        game['round_number'] += 1
        
        # Начинаем новый раунд
        game['status'] = 'choosing_situation'
        situations = self.file_manager.get_random_situations(Config.SITUATIONS_TO_CHOOSE)
        game['situations'] = situations
        
        # Создаем клавиатуру с ситуациями
        keyboard = []
        for i, situation in enumerate(situations):
            keyboard.append([InlineKeyboardButton(
                situation[:40] + "..." if len(situation) > 40 else situation,
                callback_data=f"situation_{i}"
            )])
        
        leader_name = game['player_names'][game['leader']]
        
        await bot.send_message(
            chat_id,
            f"🔄 РАУНД {game['round_number']}\n📝 {leader_name}, выберите ситуацию:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def end_game(self, query):
        chat_id = int(query.data.split('_')[1])
        game = self.active_games.get(chat_id)
        
        if not game:
            await query.answer("❌ Игра не найдена!")
            return
        
        # Определяем победителя
        if game['scores']:
            winner_id = max(game['scores'], key=game['scores'].get)
            winner_name = game['player_names'][winner_id]
            winner_score = game['scores'][winner_id]
            
            # Формируем таблицу результатов
            results = "🏆 ФИНАЛЬНЫЕ РЕЗУЛЬТАТЫ:\n\n"
            sorted_players = sorted(game['scores'].items(), key=lambda x: x[1], reverse=True)
            
            for i, (player_id, score) in enumerate(sorted_players, 1):
                player_name = game['player_names'][player_id]
                results += f"{i}. {player_name}: {score} очков\n"
            
            results += f"\n🎉 ПОБЕДИТЕЛЬ: {winner_name} с {winner_score} очками!"
            
            await query.edit_message_text(results)
        else:
            await query.edit_message_text("🎮 Игра завершена! Никто не набрал очков.")
        
        # Удаляем игру из активных
        if chat_id in self.active_games:
            del self.active_games[chat_id]
    
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

📝 КАК ИГРАТЬ:
1. Создайте игру командой /start
2. Пригласите друзей: /join_123456789
3. Ведущий выбирает ситуацию
4. Игроки выбирают мемы из ЛС
5. Ведущий голосует за лучший мем
6. Игра продолжается до завершения!
        """
        await query.edit_message_text(rules_text)
    
    async def show_stats(self, query):
        """Показать статистику пользователя"""
        user_id = query.from_user.id
        user_stats = self.db.get_user_stats(user_id)
        
        stats_text = f"""
📊 СТАТИСТИКА {query.from_user.first_name}:

🎮 Сыграно игр: {user_stats['games_played']}
🏆 Всего очков: {user_stats['total_score']}
📈 Средний результат: {user_stats['total_score'] / user_stats['games_played'] if user_stats['games_played'] > 0 else 0:.1f}
        """
        
        await query.edit_message_text(stats_text)
    
    async def show_leaderboard(self, query):
        """Показать таблицу лидеров"""
        leaderboard_data = self.db.get_leaderboard(10)
        
        if not leaderboard_data:
            await query.edit_message_text("📊 Пока никто не играл! Будьте первым!")
            return
        
        leaderboard_text = "🏆 ТОП-10 ИГРОКОВ:\n\n"
        for i, player in enumerate(leaderboard_data, 1):
            username = player['username'] or player['first_name']
            leaderboard_text += f"{i}. {username} - {player['total_score']} очков ({player['games_played']} игр)\n"
        
        await query.edit_message_text(leaderboard_text)
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда для показа статистики"""
        user_id = update.effective_user.id
        user_stats = self.db.get_user_stats(user_id)
        
        stats_text = f"""
📊 СТАТИСТИКА {update.effective_user.first_name}:

🎮 Сыграно игр: {user_stats['games_played']}
🏆 Всего очков: {user_stats['total_score']}
📈 Средний результат: {user_stats['total_score'] / user_stats['games_played'] if user_stats['games_played'] > 0 else 0:.1f}
        """
        
        await update.message.reply_text(stats_text)
    
    async def leaderboard_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда для показа лидерборда"""
        leaderboard_data = self.db.get_leaderboard(10)
        
        if not leaderboard_data:
            await update.message.reply_text("📊 Пока никто не играл! Будьте первым!")
            return
        
        leaderboard_text = "🏆 ТОП-10 ИГРОКОВ:\n\n"
        for i, player in enumerate(leaderboard_data, 1):
            username = player['username'] or player['first_name']
            leaderboard_text += f"{i}. {username} - {player['total_score']} очков ({player['games_played']} игр)\n"
        
        await update.message.reply_text(leaderboard_text)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда помощи"""
        help_text = """
🤖 КОМАНДЫ БОТА:

/start - Начать игру
/stats - Показать статистику
/leaderboard - Таблица лидеров
/help - Показать справку

🎮 КАК ИГРАТЬ:
1. Создайте игру через /start
2. Друзья присоединяются через /join_123456789
3. Ведущий выбирает ситуацию
4. Игроки выбирают мемы из ЛС
5. Ведущий голосует за лучший мем
6. Игра продолжается!

📁 Добавьте мемы в папку data/memes/
        """
        await update.message.reply_text(help_text)

def main():
    if not Config.BOT_TOKEN:
        logging.error("BOT_TOKEN не найден! Проверьте .env файл")
        return
    
    application = Application.builder().token(Config.BOT_TOKEN).build()
    bot = MemesGameBot()
    
    # Добавляем обработчики команд
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CommandHandler("join", bot.join_game))
    application.add_handler(CommandHandler("stats", bot.stats_command))
    application.add_handler(CommandHandler("leaderboard", bot.leaderboard_command))
    application.add_handler(CommandHandler("help", bot.help_command))
    
    # Добавляем обработчики callback-запросов
    application.add_handler(CallbackQueryHandler(bot.handle_callback))
    
    print("✅ Бот запускается...")
    application.run_polling()

if __name__ == "__main__":
    main()
