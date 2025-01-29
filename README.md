# 🎮 Word Scramble Game Telegram Bot

A fun and interactive Telegram bot that hosts word scramble games with unique features like hints, power attacks, and Taglish definitions! Perfect for group chats and Filipino language enthusiasts.

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/downloads/)
[![python-telegram-bot](https://img.shields.io/badge/python--telegram--bot-20.7-green)](https://github.com/python-telegram-bot/python-telegram-bot)
[![Google Gemini AI](https://img.shields.io/badge/Google%20Gemini%20AI-1.5-orange)](https://ai.google.dev/)

## ✨ Features

- 🎯 Random word scrambling with Filipino/Taglish words
- 🔄 Automatic new words every 60 seconds
- 💡 Progressive hint system with strategic point costs
- ⚔️ Power attack system to block other players
- 📚 Automatic Taglish definitions and hugot quotes using Google Gemini AI
- 🏆 Leaderboard system with points tracking
- 🎨 Rich formatting and emoji feedback
- 🔒 Admin controls for game management

## 📋 Prerequisites

- Python 3.8 or higher
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- Google Gemini API Key

## 🔧 Core Dependencies

```plaintext
python-telegram-bot==20.7
google-generativeai==0.8.3
python-dotenv==0.18.0
APScheduler==3.6.3
```

## 🚀 Quick Start

1. Clone the repository:
```bash
git clone https://github.com/ryuchi311/Word-Scramble-Game-Telegram-Bot.git
cd Word-Scramble-Game-Telegram-Bot
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

3. Set up your environment variables:
   - Create a `.env` file in the root directory
   - Add your API keys:
```plaintext
GEMINI_API_KEY=your_gemini_api_key_here
TELEGRAM_BOT_TOKEN=your_telegram_token_here
```

4. Run the bot:
```bash
python wordscramble.py
```

## 🎮 Game Commands

### Player Commands
- `/wordscramble` - Show game info and rules
- `/joinscramble` - Join the game
- `/hint` - Get a hint (costs points)
- `/leaderboard` - View top players
- `/attack username` - Block a player from earning points

### Admin Commands
- `/start_game` - Start a new game session
- `/stop_game` - End current game and show winners
- `/resetpoints` - Reset all player points
- `/reload_words` - Reload word list

## 🎯 Game Rules

1. Words are 4-15 letters long
2. Players must register using `/joinscramble`
3. First correct answer gets points (1-3 points)
4. New word appears every 60 seconds
5. Hints cost points (progressive penalty)
6. Players can block others using attack power (costs 3 points)
7. Blocked players get no points for correct answers

## 📝 Scoring System

- Correct answer: +1 to 3 points
- Using hint: -1 point (increases with each hint)
- Using attack: -3 points
- Getting blocked: 0 points for correct answer

## 🎨 Features in Detail

### Hint System
- Progressive letter reveal
- Max hints based on word length
- Increasing point penalties
- Group penalty when max hints used

### Attack Power
- Block other players from scoring
- One-time use per game session
- Strategic timing element
- Costs 3 points to use

### Word Generation
- Custom word list in Filipino/Taglish
- Random scrambling algorithm
- No repeated words until list exhausted
- Automatic word cycling

## 🤝 Contributing

Feel free to fork the repository and submit pull requests. For major changes, please open an issue first to discuss what you would like to change.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Thanks to [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) for the amazing framework
- Google Gemini AI for providing word definitions
- All contributors and players who make this game fun!

## 📞 Contact

For support or queries, create an issue in the repository or contact [@ryuchi311](https://github.com/ryuchi311) on GitHub.

---

Made with ❤️ by Ryuchi | [GitHub](https://github.com/ryuchi311)
