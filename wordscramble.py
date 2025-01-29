import os
import json
import random
import asyncio
import sys
import google.generativeai as genai
from telegram import Update, Bot
from pathlib import Path
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from datetime import datetime, timedelta

# Get the directory containing the script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Construct path to .env file
ENV_PATH = os.path.join(BASE_DIR, '.env')

# Check if .env file exists
if not os.path.exists(ENV_PATH):
    print(f"Error: .env file not found at {ENV_PATH}")
    print("Creating example .env file...")
    
    # Create example .env file
    with open(ENV_PATH, 'w') as f:
        f.write("GEMINI_API_KEY=your_gemini_api_key_here\n")
        f.write("TELEGRAM_BOT_TOKEN=your_telegram_token_here\n")
    
    print("Please edit the .env file and add your actual API keys")
    sys.exit(1)

# Load environment variables from .env file
print(f"Loading environment variables from {ENV_PATH}")
load_dotenv(ENV_PATH)

# Initialize Gemini with better error handling
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
    print("Error: GEMINI_API_KEY not properly set in .env file")
    print("Please edit the .env file and add your actual Gemini API key")
    sys.exit(1)

try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")
except Exception as e:
    print(f"Error configuring Gemini AI: {str(e)}")
    sys.exit(1)

# Initialize bot with your token
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TOKEN or TOKEN == "your_telegram_token_here":
    print("Error: TELEGRAM_BOT_TOKEN not properly set in .env file")
    print("Please edit the .env file and add your actual Telegram bot token")
    sys.exit(1)

# Define the base and data directories with better path handling
BASE_DIR = os.getcwd() 
DATA_DIR = os.path.join(BASE_DIR, "PyData")

# Create directories if they don't exist
os.makedirs(BASE_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# Define file paths
WORDLIST_PATH = os.path.join(DATA_DIR, "wordlist.json")
USERS_PATH = os.path.join(DATA_DIR, "users.json")
POINTS_PATH = os.path.join(DATA_DIR, "userpoints.json")

print("Environment setup completed successfully!")
print(f"Using directories:")
print(f"  Base dir: {BASE_DIR}")
print(f"  Data dir: {DATA_DIR}")


class ScrambleGame:
    def __init__(self):
        # Basic game attributes
        self.current_word = ""
        self.scrambled_word = ""
        self.game_active = False
        self.hints_used = {}
        self.next_game_time = None
        self.pinned_message_id = None
        self.words = self.load_words()
        self.used_words = set()
        self.word_reset_message = False
        self.revealed_positions = {}
        # Block system attributes
        self.blocks_available = set()  # Initialize empty set for blocks
        self.blocked_players = set()   # Players blocked for current word
        self.block_used = set()        # Players who have used their block this round
    
    async def get_word_definition(self, word):
        """Get word definition using Gemini AI"""
        try:
          #  prompt = f'Give a short brief, tagalog definition with taglish funny hugot 1 qoute word "{word}".'
            prompt = f'very short answer anung ibig sabihin ng "{word}" and taglish funny hugot bad jokes 1 qoute word "{word}".'
            response = model.generate_content(prompt)
            if response and response.text:
                # Clean up the response to just get the definition
                definition = response.text.strip()
                if definition.startswith("Definition: "):
                    definition = definition[11:]  # Remove "Definition: " prefix
                return f"📚 {definition}"
            return None
        except Exception as e:
            print(f"Error getting definition: {str(e)}")
            return None
        
    async def initialize_blocks(self, chat_id):
        """Initialize blocks for new game"""
        try:
            users = load_users()
            self.blocks_available = set(users.keys())
            self.blocked_players.clear()
            self.block_used.clear()
        except Exception as e:
            print(f"Error initializing blocks: {str(e)}")

    def load_words(self):
        """Load words from wordlist.json"""
        try:
            with open(WORDLIST_PATH, 'r') as f:
                data = json.load(f)
                # Filter words to ensure they match length criteria
                return [word for word in data.get('words', []) if 4 <= len(word) <= 15]
        except FileNotFoundError:
            # Don't create default words, just return empty list
            return []

    def reset_game_blocks(self):
        """Reset block system"""
        self.blocks_available = set()  # Clear available blocks
        self.blocked_players.clear()   # Clear blocked players
        try:
            users = load_users()
            self.blocks_available.update(users.keys())  # Add all current players
        except Exception as e:
            print(f"Error resetting blocks: {str(e)}")

    def scramble_word(self):

        """Reset only blocked_players for new word, keep block availability"""
        self.blocked_players.clear()
        # Rest of scramble_word code stays the same...
        """Select and scramble a word that hasn't been used"""
        if not self.words:
            raise ValueError("No words available")
                
        # If all words have been used or available_words would be empty, reset
        if len(self.used_words) >= len(self.words):
            self.used_words.clear()
            self.word_reset_message = True
                
        # Get available words (words that haven't been used)
        available_words = [word for word in self.words if word not in self.used_words]
        
        if not available_words:  # Double check after filtering
            self.used_words.clear()
            available_words = self.words.copy()  # Use all words after reset
                
        # Select a random word from available words
        word = random.choice(available_words)
        self.used_words.add(word)  # Mark word as used
            
        # Scramble the word
        scrambled = list(word)
        while ''.join(scrambled) == word:
            random.shuffle(scrambled)
                
        self.current_word = word
        self.scrambled_word = ''.join(scrambled)
        self.hints_used = {}
        if hasattr(self, 'revealed_positions'):
            self.revealed_positions = {}  # Reset revealed positions for hints
        return self.scrambled_word
    
        
    

    def reload_words(self):
        """Reload words from wordlist.json"""
        self.words = self.load_words()
        self.used_words.clear()  # Clear used words when reloading
        return len(self.words)

# Initialize game state
game = ScrambleGame()

def load_users():
    if os.path.exists(USERS_PATH):
        with open(USERS_PATH, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_PATH, 'w') as f:
        json.dump(users, f)

def load_points():
    try:
        if os.path.exists(POINTS_PATH):
            with open(POINTS_PATH, 'r') as f:
                return json.load(f)
        else:
            # If file doesn't exist, create it with empty dictionary
            default_points = {}
            with open(POINTS_PATH, 'w') as f:
                json.dump(default_points, f)
            return default_points
    except json.JSONDecodeError:
        # If file is corrupted or empty, create new with empty dictionary
        default_points = {}
        with open(POINTS_PATH, 'w') as f:
            json.dump(default_points, f)
        return default_points

def save_points(points):
    try:
        with open(POINTS_PATH, 'w') as f:
            json.dump(points, f, indent=2)
    except Exception as e:
        print(f"Error saving points: {str(e)}")

async def game_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
        game_info = """
    🎮 WORD SCRAMBLE BATTLE 🎮

    📜 Description:
    A fun word guessing game where players compete to unscramble words while using strategy with hints and attacks! Battle your way to the top of the leaderboard!

    🎯 Game Features:
    • Random scrambled words (4-15 letters)
    • Automatic new words every 60 seconds
    • Points system with leaderboard
    • Hint system with strategy
    • Attack power to block opponents
    • Tagalog definition and hugot quotes
    • Continuous gameplay until stopped

    📋 Basic Rules:
    1. Join game: /joinscramble
    2. Guess the scrambled word by typing it
    3. First correct answer gets points (1-3 points)
    4. New word appears every 60 seconds
    5. Check rankings: /leaderboard

    💡 Hint System:
    • Use /hint to reveal letters
    • Max hints depends on word length
    • Each hint costs 1 point
    • Progressive reveals (more letters shown with each hint)
    • Players with 0 points limited to 3 hints
    • Points deducted increase with each hint used

    ⚔️ Attack Power:
    • Use /attack username to block opponent
    • Costs 3 points to use attack
    • Can only use once per game session
    • Blocked player gets no points for correct answer
    • Attack power resets when new game starts

    🎁 Scoring System:
    • Correct answer: +1 to 3 points
    • Using hint: -1 point (increases with each hint)
    • Using attack: -3 points
    • Getting blocked: 0 points for correct answer

    👑 Admin Commands:
    • /start_game - Start new game
    • /stop_game - End game and show winners
    • /resetpoints - Reset all scores
    • /reload_words - Reload word list

    💭 Winner Rewards:
    • Top players shown on leaderboard
    • Special medals for top 3 players (🥇🥈🥉)
    • Bragging rights until next game!

    Type /startscramblewords to begin! Good luck! 🎯
    """
        await update.message.reply_text(game_info)

async def reload_words(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to reload words from wordlist.json"""
    if not await is_admin(update, context):
        await update.message.reply_text("Only admins can reload the word list!")
        return
        
    try:
        word_count = game.reload_words()
        await update.message.reply_text(f"Word list reloaded successfully! {word_count} words loaded.")
    except Exception as e:
        await update.message.reply_text(f"Error reloading word list: {str(e)}")

async def reset_points(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to reset all points"""
    if not await is_admin(update, context):
        await update.message.reply_text("❌ Only admins can reset points!")
        return
        
    try:
        # Reset points to empty dictionary
        with open(POINTS_PATH, 'w') as f:
            json.dump({}, f)
        
        await update.message.reply_text(
            "🔄 Points Reset Successfully!\n"
            "📊 All player scores have been reset to 0\n"
            "💫 New game, fresh start!"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error resetting points: {str(e)}")


async def show_final_leaderboard(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    """Show final leaderboard and thank you message"""
    points = load_points()
    if not points:
        await context.bot.send_message(
            chat_id=chat_id,
            text="🎮 Game Over!\n\nNo scores recorded in this session. Thanks for playing! 🎉"
        )
        return
        
    sorted_points = sorted(points.items(), key=lambda x: x[1], reverse=True)
    users = load_users()
    
    # Create winners message
    winners_msg = "🎮 Game Over! Final Results 🏁\n\n"
    winners_msg += "🏆 Top Players 🏆\n\n"
    
    for i, (user_id, score) in enumerate(sorted_points[:10], 1):
        username = users.get(user_id, {}).get('username', 'Anonymous')
        
        # Add medal emoji for top 3
        if i == 1:
            medal = "🥇"
        elif i == 2:
            medal = "🥈"
        elif i == 3:
            medal = "🥉"
        else:
            medal = "👏"
            
        winners_msg += f"{medal} {i}. {username}: {score} points\n"
    
    winners_msg += "\n🌟 Thanks for playing! 🌟\n"
    winners_msg += "See you in the next game! 👋"
    
    await context.bot.send_message(chat_id=chat_id, text=winners_msg)

# Modify the start_scramble function to include the new command
async def start_scramble(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text("Only admins can start the game!")
        return

    rules = """
🎮 Welcome to Scramble Words! 🎮

Rules:
1. Words are 4-15 letters long
2. Type /joinscramble to register
3. Use /hint for help (max 3 hints, -1 point penalty)
4. Check scores with /leaderboard
5. Game continues automatically every 60 seconds

Admin Commands:
• /start_game - Start new game
• /stop_game - Stop game
• /resetpoints - Reset all points
• /reload_words - Reload word list

Good luck! 🎯
    """
    await update.message.reply_text(rules)

async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await context.bot.get_chat_member(update.effective_chat.id, update.effective_user.id)
    return user.status in ['creator', 'administrator']

async def join_scramble(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
        
    users = load_users()
    user_id = str(update.effective_user.id)
    
    if user_id not in users:
        users[user_id] = {
            'username': update.effective_user.username or "Anonymous",
            'join_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        save_users(users)
        # Add new player to blocks_available if game is active
        if game.game_active:
            game.blocks_available.add(user_id)
        try:
            await update.message.reply_text(
                "Welcome to Scramble Words! 🎮\n"
                "You can use /attack username to block a player from earning points! ⚡"
            )
        except Exception as e:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Welcome to Scramble Words! 🎮\n"
                "You can use /attack username to block a player from earning points! ⚡"
            )
    else:
        can_block = user_id in game.blocks_available
        try:
            await update.message.reply_text(
                "You're already registered! 📝\n" +
                ("You can still use /attack! ⚡" if can_block else 
                 "You've already used your attack power! ❌")
            )
        except Exception as e:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="You're already registered! 📝\n" +
                ("You can still use /attack! ⚡" if can_block else 
                 "You've already used your attack power! ❌")
            )

async def start_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text("Only admins can start the game!")
        return
    
    game.game_active = True
    
    # Reset and initialize blocks
    game.reset_game_blocks()  # Reset blocks first
    await game.initialize_blocks(update.effective_chat.id)  # Then initialize for new game
    
    await new_round(context, update.effective_chat.id)

async def new_round(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    if not game.game_active:
        return
        
    try:
        # Check if we need to show the reset message
        if game.word_reset_message:
            await context.bot.send_message(
                chat_id=chat_id, 
                text="🔄 All words have been used! Starting over with the full word list."
            )
            game.word_reset_message = False
        
        try:
            scrambled = game.scramble_word()
        except ValueError:
            # Show final leaderboard and thank you message
            await context.bot.send_message(
                chat_id=chat_id,
                text="🎯 Game Over: Word list is empty!"
            )
            await show_final_leaderboard(context, chat_id)
            game.game_active = False
            return
            
        message = f"🎯 Unscramble this word: {scrambled.upper()} \n\n Use /hint and it will be penalty for all \n\n Join now click /joinscramble"
        
        # Unpin previous message if exists
        if game.pinned_message_id:
            try:
                await context.bot.unpin_chat_message(chat_id=chat_id, message_id=game.pinned_message_id)
            except Exception:
                pass
        
        # Send and pin new message
        sent_message = await context.bot.send_message(chat_id=chat_id, text=message)
        try:
            await context.bot.pin_chat_message(chat_id=chat_id, message_id=sent_message.message_id)
            game.pinned_message_id = sent_message.message_id
        except Exception:
            pass
        
        # Schedule next round
        game.next_game_time = datetime.now() + timedelta(seconds=60)
    except Exception as e:
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"⚠️ Error in game: {str(e)}"
        )
        await show_final_leaderboard(context, chat_id)
        game.game_active = False

async def stop_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command to stop the game and show winners"""
    if not await is_admin(update, context):
        await update.message.reply_text("❌ Only admins can stop the game!")
        return
    
    try:
        if not game.game_active:
            await update.message.reply_text("No active game to stop!")
            return
            
        game.game_active = False
        
        # Unpin the last scrambled word if exists
        if game.pinned_message_id:
            try:
                await context.bot.unpin_chat_message(
                    chat_id=update.effective_chat.id,
                    message_id=game.pinned_message_id
                )
            except:
                pass
        
        # Get and display winners
        points = load_points()
        if not points:
            await update.message.reply_text(
                "🎮 Game Over!\n\n"
                "No scores recorded in this session."
            )
            return
            
        sorted_points = sorted(points.items(), key=lambda x: x[1], reverse=True)
        users = load_users()
        
        # Create winners message
        winners_msg = "🎮 Game Over! Final Results 🏁\n\n"
        winners_msg += "🏆 Top Players 🏆\n\n"
        
        for i, (user_id, score) in enumerate(sorted_points[:10], 1):
            username = users.get(user_id, {}).get('username', 'Anonymous')
            
            # Add medal emoji for top 3
            if i == 1:
                medal = "🥇"
            elif i == 2:
                medal = "🥈"
            elif i == 3:
                medal = "🥉"
            else:
                medal = "👏"
                
            winners_msg += f"{medal} {i}. {username}: {score} points\n"
        
        winners_msg += "\nThanks for playing! 🎉"
        
        await update.message.reply_text(winners_msg)
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error stopping game: {str(e)}")


async def hint(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not game.game_active:
        await update.message.reply_text("No active game! Wait for admin to start.")
        return
        
    user_id = str(update.effective_user.id)
    users = load_users()
    if user_id not in users:
        await update.message.reply_text("Please /joinscramble first!")
        return
    
    username = users[user_id]['username']
    points = load_points()
    current_points = points.get(user_id, 0)
        
    if user_id not in game.hints_used:
        game.hints_used[user_id] = 0
    
    word = game.current_word
    if not word:
        await update.message.reply_text("No active word to hint!")
        return
    
    # Calculate max hints based on word length
    max_hints = min(len(word) - 2, 5)  # At least 2 letters hidden, max 5 hints
    
    # If player has 0 points, limit to 3 hints
    if current_points <= 0:
        max_hints = min(max_hints, 3)
        
    # Check if anyone has used max hints
    max_hints_used = any(hints >= max_hints for hints in game.hints_used.values())
    
    if max_hints_used:
        await update.message.reply_text(
            "❌ Maximum hints have been used for this round!\n"
            "All players are now penalized! Wait for the next word."
        )
        return
        
    if game.hints_used[user_id] >= max_hints:
        # Apply penalty to all players when someone reaches max hints
        penalty_message = f"⚠️ {username} has used maximum hints!\n📉 All players will be penalized!\n\n"
        penalty_updates = []
        
        for player_id in users.keys():
            if player_id in points and points[player_id] > 0:
                original_points = points[player_id]
                points[player_id] = max(0, points[player_id] - 2)  # -2 points penalty
                penalty_updates.append(f"@{users[player_id]['username']}: {original_points} → {points[player_id]}")
        
        save_points(points)
        
        if penalty_updates:
            penalty_message += "Point Deductions:\n" + "\n".join(penalty_updates)
        else:
            penalty_message += "No players with points to deduct."
            
        await update.message.reply_text(penalty_message)
        return
        
    hint_count = game.hints_used[user_id] + 1
    
    # Initialize revealed positions
    if not hasattr(game, 'revealed_positions'):
        game.revealed_positions = {}
    if user_id not in game.revealed_positions:
        game.revealed_positions[user_id] = set()
    
    # Calculate progressive point deduction
    point_deduction = hint_count  # More points lost for each subsequent hint
    
    # Apply point penalty
    if user_id in points and points[user_id] > 0:
        points[user_id] = max(0, points[user_id] - point_deduction)
        save_points(points)
        point_message = f"📉 -{point_deduction} points (now at {points[user_id]} points)"
    else:
        point_message = "💫 No points deducted (already at 0 points)"
    
    # Calculate letters to reveal
    total_letters = len(word)
    remaining_hidden = total_letters - len(game.revealed_positions[user_id])
    letters_to_reveal = max(1, remaining_hidden // (max_hints - game.hints_used[user_id]))
    
    # Get positions not yet revealed
    available_positions = [i for i in range(total_letters) 
                         if i not in game.revealed_positions[user_id]]
    
    # Randomly select new positions to reveal
    new_positions = random.sample(available_positions, min(letters_to_reveal, len(available_positions)))
    game.revealed_positions[user_id].update(new_positions)
    
    # Create the hint string
    hint_chars = ['?' for _ in range(total_letters)]
    for pos in game.revealed_positions[user_id]:
        if 0 <= pos < total_letters:
            hint_chars[pos] = word[pos]
    hint = ''.join(hint_chars)
    
    game.hints_used[user_id] += 1
    
    # Create announcement message
    revealed_count = len(game.revealed_positions[user_id])
    announcement = (
        f"👤 {username} used hint {game.hints_used[user_id]}/{max_hints}\n"
        f"📝 Hint: {hint}\n"
        f"📊 Progress: {revealed_count}/{total_letters} letters revealed\n"
        f"{point_message}\n"
        f"⚠️ Warning: If max hints are used, all players will be penalized!"
    )
    
    await update.message.reply_text(announcement)
    
    # Reset revealed positions when max hints are used
    if game.hints_used[user_id] >= max_hints:
        game.revealed_positions[user_id] = set()


async def status_scramble(update: Update, context: ContextTypes.DEFAULT_TYPE):
    points = load_points()
    if not points:
        await update.message.reply_text("No scores yet!")
        return
        
    sorted_points = sorted(points.items(), key=lambda x: x[1], reverse=True)
    users = load_users()
    
    leaderboard = "🏆 Leaderboard 🏆\n\n"
    for i, (user_id, score) in enumerate(sorted_points[:10], 1):
        username = users.get(user_id, {}).get('username', 'Anonymous')
        leaderboard += f"{i}. {username}: {score} points\n"
    
    await update.message.reply_text(leaderboard)

async def block_player(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not game.game_active:
        await update.message.reply_text("No active game! Wait for admin to start.")
        return
        
    user_id = str(update.effective_user.id)
    users = load_users()
    points = load_points()
    
    if user_id not in users:
        await update.message.reply_text("Please /joinscramble first!")
        return
    
    # Check if player has enough points
    current_points = points.get(user_id, 0)
    if current_points < 3:
        await update.message.reply_text(
            f"❌ You need 3 points to use attack power!\n"
            f"Your current points: {current_points}"
        )
        return
    
    if user_id not in game.blocks_available:
        await update.message.reply_text(
            "❌ You've already used your attack power in this game!\n"
            "Attack power resets when admin starts a new game with /start_game"
        )
        return
    
    if not context.args:
        await update.message.reply_text("Please specify a player to attack!\nExample: /attack username")
        return
    
    target_username = context.args[0].replace("@", "")
    
    target_id = None
    for uid, data in users.items():
        if data['username'].lower() == target_username.lower():
            target_id = uid
            break
    
    if not target_id:
        await update.message.reply_text(f"Player @{target_username} not found!")
        return
    
    if target_id == user_id:
        await update.message.reply_text("❌ You cannot attack yourself!")
        return
    
    # Deduct points and apply attack
    points[user_id] = current_points - 3
    save_points(points)
    game.blocked_players.add(target_id)
    game.blocks_available.remove(user_id)
    
    blocker_name = users[user_id]['username']
    target_name = users[target_id]['username']
    
    announcement = (
        f"⚡ POWER ATTACK ACTIVATED! ⚡\n"
        f"🗡️ {blocker_name} attacked {target_name}\n"
        f"❌ {target_name} cannot earn points this round!\n"
        f"💰 Cost: -3 points ({points[user_id]} points remaining)\n"
        f"📢 {blocker_name} has used their attack power!"
    )
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=announcement
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not game.game_active or not game.current_word:
        return
        
    user_id = str(update.effective_user.id)
    users = load_users()
    if user_id not in users:
        return
        
    if not update.message.text:
        return
        
    guess = update.message.text.lower().strip()
    if guess == game.current_word:
        points = load_points()
        if user_id not in points:
            points[user_id] = 0
            
        # Check if player is blocked
        if user_id in game.blocked_players:
            await update.message.reply_text(
                f"🎯 Correct! But you were blocked this round!\n"
                f"The word was: {game.current_word.upper()}\n"
                f"❌ No points earned due to power block!"
            )
        else:
            # Normal point calculation
            hint_penalty = game.hints_used.get(user_id, 0)
            earned_points = max(1, 3 - hint_penalty)
            points[user_id] += earned_points
            save_points(points)
            
            # Get word definition
            definition = await game.get_word_definition(game.current_word)
            definition_text = f"\n{definition}" if definition else ""
            
            await update.message.reply_text(
                f"🎉 Correct! {users[user_id]['username']} earned {earned_points} points!\n"
                f"The word was: {game.current_word.upper()}"
                f"{definition_text}"
                f"\n\nJoin now click /joinscramble\n"
                f"Next word in 40 seconds..."
            )
        
        # Schedule next round
        await asyncio.sleep(60)
        await new_round(context, update.effective_chat.id)

def main():
    application = Application.builder().token(TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("startscramblewords", start_scramble))
    application.add_handler(CommandHandler("start_game", start_game))
    application.add_handler(CommandHandler("stop_game", stop_game))  # New stop game handler
    application.add_handler(CommandHandler("joinscramble", join_scramble))
    application.add_handler(CommandHandler("hint", hint))
    application.add_handler(CommandHandler("leaderboard", status_scramble))
    application.add_handler(CommandHandler("reload_words", reload_words))
    application.add_handler(CommandHandler("resetpoints", reset_points))
    application.add_handler(CommandHandler("attack", block_player))
    application.add_handler(CommandHandler("wordscramble", game_info))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Start the bot
    application.run_polling()

if __name__ == "__main__":
    main()