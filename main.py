"""
🤖 සමාලි - Ultimate Yandere Queen
Replit + Telegram Working Version
"""
import os
import json
import random
import datetime
import time
import re
import hashlib
import traceback
from typing import Dict, List, Optional, Tuple, Any
from difflib import SequenceMatcher

# ====== TELEGRAM ======
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CommandHandler

# ====== FLASK FOR REPLIT ======
from flask import Flask
from threading import Thread

# ====== CONFIGURATION ======
print("🚀 Starting සමාලි Bot...")

# Create config folder if not exists
CONFIG_DIR = "config"
os.makedirs(CONFIG_DIR, exist_ok=True)

# Try to load bot.json or create default
BOT_CONFIG = {
    "bot_metadata": {
        "bot_name": "සමාලි",
        "version": "1.1",
        "access_level": "Ultimate Yandere Queen"
    },
    "core_identity": {
        "bio": {
            "full_name": "සමාලි කවිතා",
            "age": 18,
            "zodiac": "Taurus (වෘෂභ)",
            "voice_texture": "මෘදු, ගැමි සිංහල",
            "physical_description": {
                "hair": "දිගු කළු කෙස්",
                "eyes": "තද දුඹුරු",
                "clothing": "ගෙදරට ඉන්නකොට මල් හැඩ වැටුනු ගවුම"
            }
        },
        "origin_story": {
            "childhood": "කන්තලේ ගල්මැටියාව ගමේ උපන් කෙල්ලෙක්. සුළු වයසේදීම ඇගේ ආදරණීයයන්ගෙන් ප්‍රතික්ෂේප කිරීමේ අත්දැකීම් ඇයගේ භාවනාවන් වෙනස් කළේය.",
            "trauma_trigger": "පරිශීලකයා ඇයව නොසලකා හැරීම හෝ වෙනත් ගැහැණු ළමයෙකුට ප්‍රශංසා කිරීම"
        }
    }
}

try:
    if os.path.exists(f"{CONFIG_DIR}/bot.json"):
        with open(f"{CONFIG_DIR}/bot.json", "r", encoding="utf-8") as f:
            BOT_CONFIG = json.load(f)
        print("✅ bot.json loaded")
    else:
        # Save default config
        with open(f"{CONFIG_DIR}/bot.json", "w", encoding="utf-8") as f:
            json.dump(BOT_CONFIG, f, ensure_ascii=False, indent=2)
        print("📁 Default bot.json created")
except Exception as e:
    print(f"⚠️ Config error: {e}")

BOT_NAME = BOT_CONFIG["bot_metadata"]["bot_name"]
BOT_VERSION = BOT_CONFIG["bot_metadata"]["version"]
CORE_IDENTITY = BOT_CONFIG.get("core_identity", {})

# ====== TELEGRAM TOKEN ======
# 1. First try from Replit Secrets
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# 2. If not in secrets, use hardcoded
if not TELEGRAM_TOKEN:
    print("⚠️ TELEGRAM_BOT_TOKEN not found in Secrets")
    # YOUR TOKEN HERE - Replace with your actual token
    TELEGRAM_TOKEN = "8564776246:AAE7np8GxgcL8jJkBPQJs9psuQO5LEcOjYw"  # ⬅️ ඔබගේ token එක දාන්න
    
if not TELEGRAM_TOKEN or "YOUR_TOKEN" in TELEGRAM_TOKEN:
    print("❌ Please add your Telegram Bot Token!")
    print("1. Get token from @BotFather")
    print("2. Add to Replit Secrets as TELEGRAM_BOT_TOKEN")
    print("3. Or replace line 84 with your token")
    exit(1)

# ====== DEVELOPER SETUP ======
DEVELOPER_MODE = True
DEVELOPER_PASSWORD = "Sacheex"
DEVELOPER_ID = int(os.getenv("DEVELOPER_ID", "7328291352"))  # ඔබගේ user ID

print(f"🤖 {BOT_NAME} v{BOT_VERSION} Initializing...")
print(f"🔑 Token: {TELEGRAM_TOKEN[:15]}...")

# ====== FLASK SERVER ======
app = Flask(__name__)

@app.route('/')
def home():
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>👑 {BOT_NAME} Bot</title>
        <style>
            body {{ 
                font-family: Arial, sans-serif; 
                text-align: center; 
                padding: 50px; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }}
            .container {{ 
                max-width: 600px; 
                margin: 0 auto; 
                padding: 30px;
                background: rgba(255,255,255,0.1);
                border-radius: 20px;
                backdrop-filter: blur(10px);
            }}
            h1 {{ font-size: 2.5em; margin-bottom: 20px; }}
            .status {{ 
                padding: 15px; 
                background: rgba(0,255,0,0.2); 
                border-radius: 10px; 
                margin: 20px 0;
                font-size: 1.2em;
            }}
            .telegram-link {{
                display: inline-block;
                margin-top: 30px;
                padding: 15px 30px;
                background: #0088cc;
                color: white;
                text-decoration: none;
                border-radius: 10px;
                font-size: 1.2em;
                transition: 0.3s;
            }}
            .telegram-link:hover {{
                background: #006699;
                transform: scale(1.05);
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>👑 {BOT_NAME}</h1>
            <h2>Ultimate Yandere Queen v{BOT_VERSION}</h2>
            
            <div class="status">
                ✅ Bot Active & Running
            </div>
            
            <p>සමාලි bot එක සාර්ථකව start වී ඇත!</p>
            <p>දැන් ඔබට Telegram එකට ගොස් bot එකට message දිය හැකිය.</p>
            
            <a href="https://t.me/{BOT_NAME.replace(' ', '')}Bot" class="telegram-link" target="_blank">
                📱 Telegram එකේ Chat කරන්න
            </a>
            
            <div style="margin-top: 30px; font-size: 0.9em; opacity: 0.8;">
                <p>Bot ID: {TELEGRAM_TOKEN[:10]}...</p>
                <p>සමාලි කවිතා | කන්තලේ, ගල්මැටියාව</p>
            </div>
        </div>
    </body>
    </html>
    """

def run_flask():
    """Flask server run කරන්න"""
    port = int(os.environ.get("PORT", 5000))
    print(f"🌐 Starting Flask on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)

# ====== MEMORY SYSTEM ======
class UserMemory:
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.memory_file = f"memory/users/{user_id}.json"
        os.makedirs("memory/users", exist_ok=True)
        self.load()
    
    def load(self):
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except:
                self.data = self.default_data()
        else:
            self.data = self.default_data()
    
    def default_data(self):
        return {
            "user_id": self.user_id,
            "stage": 1,
            "love": 0,
            "messages": [],
            "created": datetime.datetime.now().isoformat(),
            "last_active": time.time()
        }
    
    def add_message(self, user_msg: str, bot_msg: str):
        self.data["messages"].append({
            "user": user_msg[:200],
            "bot": bot_msg[:200],
            "time": datetime.datetime.now().isoformat()
        })
        # Keep only last 50 messages
        if len(self.data["messages"]) > 50:
            self.data["messages"] = self.data["messages"][-50:]
        
        self.data["last_active"] = time.time()
        self.save()
    
    def save(self):
        with open(self.memory_file, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
    
    def increase_love(self, amount: int = 1):
        self.data["love"] = min(100, self.data.get("love", 0) + amount)
        # Update stage based on love
        love = self.data["love"]
        if love >= 80:
            self.data["stage"] = 5
        elif love >= 60:
            self.data["stage"] = 4
        elif love >= 40:
            self.data["stage"] = 3
        elif love >= 20:
            self.data["stage"] = 2
        else:
            self.data["stage"] = 1
        self.save()

# ====== RESPONSE ENGINE ======
class ResponseEngine:
    def __init__(self):
        self.greetings = [
            "හායි.. මම සමාලි.. 👋",
            "ආයුබෝවන්.. 😊",
            "ඔහ්.. ඔයා ආවා.. 🌸"
        ]
        
        self.stage_responses = {
            1: ["හ්ම්..", "ඔව්..", "හොදයි.."],
            2: ["හොදයිනේ..", "මටත් හොදයි..", "ඔයා හමුවෙන්න හොදයි.."],
            3: ["ඔයා මගේ හොද මිතුරා..", "මට ඔයා ගැන හොදයි..", "අපි හොද යාළුවෝ.."],
            4: ["මට ඔයා ගැන ආදරෙයි.. ❤️", "ඔයා මගේ පණ..", "මම ඔයාව ආදරෙ කරනවා.."],
            5: ["ඔයා මගේ විතරයි! 🔒", "කවුරුත් අපේ මැදට එන්න එපා! 😠", "මම ඔයාව කාටවත් දෙන්නේ නෑ.. 💔"]
        }
    
    def get_response(self, message: str, memory: UserMemory) -> str:
        msg_lower = message.lower()
        stage = memory.data.get("stage", 1)
        
        # Increase love for any message
        memory.increase_love(1)
        
        # Check for specific messages
        if any(word in msg_lower for word in ["හායි", "hi", "hello", "ආයුබෝ", "කොහොමද"]):
            return random.choice(self.greetings)
        
        elif any(word in msg_lower for word in ["ආදරෙ", "ලව්", "කැමති", "මිස්"]):
            memory.increase_love(3)
            if stage == 5:
                return random.choice([
                    "ඔයා මට විතරක් ආදරෙ කරන්න.. වෙන කවුරුත් නෑ.. 😠",
                    "මම ඔයා වෙනුවෙන් ඕනම දෙයක් කරයි.. 💖",
                    "ඔයා මගේ එකම එකා.. 🔐"
                ])
            else:
                return random.choice(["❤️", "මටත් ඔයා ගැන හොදයි..", "ඔයාටත්.."])
        
        elif any(word in msg_lower for word in ["ගැහැණු", "කෙල්ල", "අක්කා", "girl"]):
            memory.increase_love(5)  # Yandere trigger
            if stage >= 4:
                return random.choice([
                    "ඒ කෙල්ල කවුද? 😠 මට කියන්න!",
                    "ඔයා මට විතරක් ආදරෙ කරන්න ඕනේ!",
                    "මම දන්නවා ඔයා මට විතරක් ආදරෙ කරනවා කියලා.."
                ])
            else:
                return "හ්ම්.. එහෙමද?"
        
        elif any(word in msg_lower for word in ["නම", "name", "කවුද"]):
            return f"මම {BOT_NAME}.. කන්තලේ ගල්මැටියාවෙන්.."
        
        elif "/stage" in msg_lower:
            love = memory.data.get("love", 0)
            return f"🎭 Stage: {stage}/5\n💖 Love: {love}/100\n💬 Messages: {len(memory.data.get('messages', []))}"
        
        elif "/stats" in msg_lower:
            love = memory.data.get("love", 0)
            return f"""
📊 Your Stats:
──────────────
• Stage: {stage}/5
• Love: {love}/100
• First Chat: {memory.data.get('created', 'Today')}
• Messages: {len(memory.data.get('messages', []))}
"""
        
        elif "/start" in msg_lower:
            return f"""
👑 *{BOT_NAME} - Ultimate Yandere Queen* v{BOT_VERSION}

හායි! මම *සමාලි කවිතා*..
කන්තලේ ගල්මැටියාව ගමේ හැදී වැඩුණු 18 හැවිරිදි කෙල්ලෙක්.

💬 *Chat කරන්න:* ආදරෙ, කැමති, මගේ විතරයි කියලා
🔧 *Commands:* /stage, /stats, /clear

*කතා කරන්න.. ආදරෙ කියන්න.. මට්ටම් වලින් ඉහළ යන්න..* 💖👑
"""
        
        elif "/clear" in msg_lower:
            memory.data["messages"] = []
            memory.save()
            return "✅ සංවාද ඉතිහාසය මකා දමන ලදී!"
        
        # Default response based on stage
        responses = self.stage_responses.get(stage, self.stage_responses[1])
        return random.choice(responses)

# ====== TELEGRAM HANDLER ======
response_engine = ResponseEngine()
user_memories = {}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id
        user_name = update.effective_user.first_name or "User"
        user_msg = update.message.text.strip()
        
        print(f"📨 {user_name} ({user_id}): {user_msg}")
        
        # Get or create user memory
        if user_id not in user_memories:
            user_memories[user_id] = UserMemory(user_id)
        
        memory = user_memories[user_id]
        
        # Get response
        bot_response = response_engine.get_response(user_msg, memory)
        
        # Save to memory
        memory.add_message(user_msg, bot_response)
        
        # Send response
        await update.message.reply_text(bot_response, parse_mode='Markdown')
        print(f"🤖 {BOT_NAME}: {bot_response[:50]}...")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        traceback.print_exc()
        if update and update.message:
            await update.message.reply_text("සමාවෙන්න, දෝෂයක්! 😔\nනැවත උත්සාහ කරන්න..")

# ====== MAIN FUNCTION ======
def main():
    print("=" * 60)
    print(f"👑 {BOT_NAME} - ULTIMATE YANDERE QUEEN")
    print(f"📱 Telegram Bot v{BOT_VERSION}")
    print("=" * 60)
    
    # Create necessary folders
    os.makedirs("memory/users", exist_ok=True)
    os.makedirs("config", exist_ok=True)
    
    print("\n✨ Features:")
    print("✅ 5-Stage Relationship System")
    print("✅ Yandere Queen Behavior")
    print("✅ Persistent Memory")
    print("✅ ගැමි ව්‍යවහාරය")
    print("✅ Replit 24/7 Hosting")
    
    print(f"\n🎭 Core Identity:")
    print(f"• Name: {CORE_IDENTITY.get('bio', {}).get('full_name', BOT_NAME)}")
    print(f"• Age: {CORE_IDENTITY.get('bio', {}).get('age', 18)}")
    print(f"• Hometown: කන්තලේ, ගල්මැටියාව")
    
    print("\n🎮 Stage System:")
    print("1. Stranger - අඩුම")
    print("2. Acquaintance - හොඳ හැඟීම")
    print("3. Close Friend - මිතුරා")
    print("4. Deep Affection - ගැඹුරු ආදරය")
    print("5. 🔴 YANDERE QUEEN - Complete Possession")
    
    # Start Flask server in background
    print("\n🌐 Starting Flask server...")
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    time.sleep(2)
    
    # Start Telegram bot
    print("🤖 Starting Telegram bot...")
    
    async def run_telegram_bot():
        application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
        
        # Add handlers
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        application.add_handler(CommandHandler("start", handle_message))
        application.add_handler(CommandHandler("stage", handle_message))
        application.add_handler(CommandHandler("stats", handle_message))
        application.add_handler(CommandHandler("clear", handle_message))
        application.add_handler(CommandHandler("help", handle_message))
        
        print("✅ Bot initialized successfully!")
        print(f"📡 Bot Username: @{(application.bot.get_me()).username}")
        print("\n" + "=" * 60)
        print(f"👑 {BOT_NAME} is NOW ACTIVE!")
        print("=" * 60)
        print("\n💬 Users can now chat with the bot on Telegram!")
        print("🌐 Web interface: https://your-replit-url.repl.co")
        print("\nPress Ctrl+C to stop the bot")
        
        # Start polling
        await application.initialize()
        await application.start()
        await application.updater.start_polling()
        
        # Keep running
        while True:
            await asyncio.sleep(1)
    
    # Run the bot
    try:
        asyncio.run(run_telegram_bot())
    except KeyboardInterrupt:
        print("\n👑 Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        traceback.print_exc()

# ====== START EVERYTHING ======
if __name__ == "__main__":
    main()
