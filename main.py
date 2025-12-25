"""
🤖 සමාලි - Complete with Memory Export/Import
Memory: ~250MB | Stable | Export/Import Enabled
"""
from flask import Flask, jsonify
from threading import Thread
import os
import json
import random
import datetime
import traceback
import time
import re
import io
import zipfile
from typing import Dict, List, Optional

# ====== TINY MODEL ======
try:
    from transformers import AutoTokenizer, AutoModelForCausalLM
    import torch
    TINY_MODEL_AVAILABLE = True
    print("✅ Tiny model support available")
except ImportError:
    TINY_MODEL_AVAILABLE = False
    print("⚠️ Install: pip install transformers torch")

# ====== TELEGRAM ======
try:
    from telegram import Update, InputFile
    from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CommandHandler
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    print("⚠️ Install: pip install python-telegram-bot")

from dotenv import load_dotenv
load_dotenv()

# ====== CONFIGURATION ======
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
DEVELOPER_PASSWORD = os.getenv("DEVELOPER_PASSWORD", "admin123")
ADMIN_USER_ID = os.getenv("ADMIN_USER_ID", "")  # Add this to .env

# Load configs
with open("bot.config", "r", encoding="utf-8") as f:
    BOT_CONFIG = json.load(f)

with open("developer_settings.json", "r", encoding="utf-8") as f:
    DEV_SETTINGS = json.load(f)

BOT_NAME = BOT_CONFIG.get("bot_name", "සමාලි")

if not TELEGRAM_TOKEN:
    print("❌ TELEGRAM_BOT_TOKEN not found!")
    exit(1)

# ====== OPTIMIZED MODEL CONFIG ======
class OptimizedModelConfig:
    MODEL_NAME = "gpt2"
    MAX_TOKENS = 50
    TEMPERATURE = 0.8
    TOP_P = 0.9
    DO_SAMPLE = True

# ====== CREATE DIRECTORIES ======
def ensure_directories():
    directories = [
        "memory/users", 
        "memory/habits",
        "logs"
    ]
    for d in directories:
        os.makedirs(d, exist_ok=True)
        print(f"📁 {d}")

ensure_directories()

# ====== LIGHTWEIGHT MEMORY SYSTEM ======
class LightweightMemory:
    """Memory system optimized for low RAM"""
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.memory_file = f"memory/users/{user_id}.json"
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
        
        self.data.setdefault("stage", 1)
        self.data.setdefault("love_score", 0)
        self.data.setdefault("jealousy", 0)
        self.data.setdefault("mood", "neutral")
        self.data.setdefault("conversation", [])
        self.update_stage()
    
    def default_data(self):
        return {
            "stage": 1,
            "love_score": 0,
            "jealousy": 0,
            "mood": "neutral",
            "conversation": [],
            "created": datetime.datetime.now().isoformat(),
            "last_active": time.time()
        }
    
    def save(self):
        self.data["last_active"] = time.time()
        os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)
        with open(self.memory_file, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
    
    def add_message(self, user_msg: str, bot_msg: str):
        if "conversation" not in self.data:
            self.data["conversation"] = []
        
        user_msg_short = user_msg[:100]
        bot_msg_short = bot_msg[:100]
        
        self.data["conversation"].append({
            "user": user_msg_short,
            "bot": bot_msg_short,
            "time": datetime.datetime.now().isoformat(),
            "stage": self.data["stage"]
        })
        
        if len(self.data["conversation"]) > 20:
            self.data["conversation"] = self.data["conversation"][-20:]
    
    def update_stage(self):
        love_score = self.data.get("love_score", 0)
        if love_score >= 95:
            self.data["stage"] = 5
        elif love_score >= 75:
            self.data["stage"] = 4
        elif love_score >= 50:
            self.data["stage"] = 3
        elif love_score >= 25:
            self.data["stage"] = 2
        else:
            self.data["stage"] = 1
    
    def update_emotions(self, user_msg: str):
        msg_lower = user_msg.lower()
        
        if any(word in msg_lower for word in ["ආදරෙ", "ලව්", "කැමති", "මිස්"]):
            self.data["love_score"] = min(100, self.data.get("love_score", 0) + 2)
        
        if any(word in msg_lower for word in ["ගෑනු", "girl", "මිතුරිය"]):
            self.data["jealousy"] = min(10, self.data.get("jealousy", 0) + 3)
        elif self.data.get("jealousy", 0) > 0:
            self.data["jealousy"] = max(0, self.data["jealousy"] - 1)
        
        if random.random() < 0.1:
            moods = ["happy", "shy", "neutral", "excited", "bored"]
            self.data["mood"] = random.choice(moods)
        
        self.update_stage()

# ====== MEMORY EXPORT/IMPORT SYSTEM ======
class MemoryTools:
    """Memory export/import tools"""
    
    @staticmethod
    def export_user_memory(user_id: int) -> Optional[bytes]:
        """Export user memory as JSON"""
        memory_file = f"memory/users/{user_id}.json"
        
        if not os.path.exists(memory_file):
            return None
        
        try:
            with open(memory_file, "r", encoding="utf-8") as f:
                memory_data = json.load(f)
            
            # Add export info
            memory_data["_export_info"] = {
                "exported_at": datetime.datetime.now().isoformat(),
                "user_id": user_id,
                "bot_name": BOT_NAME,
                "total_messages": len(memory_data.get("conversation", [])),
                "version": "1.0"
            }
            
            return json.dumps(memory_data, ensure_ascii=False, indent=2).encode('utf-8')
            
        except Exception as e:
            print(f"❌ Export error: {e}")
            return None
    
    @staticmethod
    def export_all_memories() -> Optional[bytes]:
        """Export all memories as ZIP"""
        try:
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # Add user memories
                memory_dir = "memory/users"
                if os.path.exists(memory_dir):
                    for filename in os.listdir(memory_dir):
                        if filename.endswith('.json'):
                            user_file = os.path.join(memory_dir, filename)
                            zip_file.write(user_file, f"memories/{filename}")
                
                # Add configs
                config_files = ["bot.config", "developer_settings.json"]
                for config_file in config_files:
                    if os.path.exists(config_file):
                        zip_file.write(config_file, f"config/{config_file}")
                
                # Add info file
                export_info = {
                    "exported_at": datetime.datetime.now().isoformat(),
                    "bot_name": BOT_NAME,
                    "total_users": len(os.listdir(memory_dir)) if os.path.exists(memory_dir) else 0,
                    "version": "1.0"
                }
                zip_file.writestr("export_info.json", json.dumps(export_info, indent=2))
            
            return zip_buffer.getvalue()
            
        except Exception as e:
            print(f"❌ Bulk export error: {e}")
            return None
    
    @staticmethod
    def get_memory_stats() -> Dict:
        """Get memory statistics"""
        stats = {
            "total_users": 0,
            "total_messages": 0,
            "total_size_mb": 0,
            "users": []
        }
        
        memory_dir = "memory/users"
        if not os.path.exists(memory_dir):
            return stats
        
        total_size = 0
        
        for filename in os.listdir(memory_dir):
            if filename.endswith('.json'):
                user_id = filename.replace('.json', '')
                user_file = os.path.join(memory_dir, filename)
                
                try:
                    file_size = os.path.getsize(user_file)
                    total_size += file_size
                    
                    with open(user_file, 'r', encoding='utf-8') as f:
                        user_data = json.load(f)
                    
                    stats["users"].append({
                        "user_id": user_id,
                        "messages": len(user_data.get("conversation", [])),
                        "stage": user_data.get("stage", 1),
                        "love_score": user_data.get("love_score", 0),
                        "file_size_kb": file_size / 1024
                    })
                    
                except:
                    continue
        
        stats["total_users"] = len(stats["users"])
        stats["total_messages"] = sum(user["messages"] for user in stats["users"])
        stats["total_size_mb"] = total_size / (1024 * 1024)
        
        return stats
    
    @staticmethod
    def import_user_memory(user_id: int, json_data: bytes) -> bool:
        """Import user memory from JSON"""
        try:
            memory_data = json.loads(json_data.decode('utf-8'))
            memory_data.pop("_export_info", None)  # Remove export metadata
            
            memory_file = f"memory/users/{user_id}.json"
            os.makedirs(os.path.dirname(memory_file), exist_ok=True)
            
            with open(memory_file, "w", encoding="utf-8") as f:
                json.dump(memory_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Imported memory for user {user_id}")
            return True
            
        except Exception as e:
            print(f"❌ Import error: {e}")
            return False

# ====== OPTIMIZED MODEL MANAGER ======
class OptimizedModelManager:
    def __init__(self):
        self.tokenizer = None
        self.model = None
        self.loaded = False
        self.load_model()
    
    def load_model(self):
        if not TINY_MODEL_AVAILABLE:
            print("❌ Transformers not available")
            return
        
        try:
            print(f"🔄 Loading {OptimizedModelConfig.MODEL_NAME}...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                OptimizedModelConfig.MODEL_NAME,
                padding_side="left"
            )
            
            self.model = AutoModelForCausalLM.from_pretrained(
                OptimizedModelConfig.MODEL_NAME,
                torch_dtype=torch.float32,
                device_map="cpu",
                low_cpu_mem_usage=True
            )
            
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            self.loaded = True
            print(f"✅ Model loaded: {OptimizedModelConfig.MODEL_NAME}")
            
        except Exception as e:
            print(f"❌ Model load failed: {e}")
            self.loaded = False
    
    def generate_response(self, prompt: str) -> str:
        if not self.loaded or self.model is None:
            return ""
        
        try:
            inputs = self.tokenizer.encode(
                prompt,
                return_tensors="pt",
                truncation=True,
                max_length=150
            )
            
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs,
                    max_new_tokens=OptimizedModelConfig.MAX_TOKENS,
                    temperature=OptimizedModelConfig.TEMPERATURE,
                    top_p=OptimizedModelConfig.TOP_P,
                    do_sample=OptimizedModelConfig.DO_SAMPLE,
                    pad_token_id=self.tokenizer.pad_token_id,
                    no_repeat_ngram_size=2,
                    repetition_penalty=1.2
                )
            
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            if prompt in response:
                response = response[len(prompt):].strip()
            
            response = response.split('\n')[0].strip()
            return response[:100]
            
        except Exception as e:
            print(f"⚠️ Generation error: {str(e)[:100]}")
            return ""

# ====== SIMPLE PROMPT ENGINEER ======
class SimplePromptEngineer:
    @staticmethod
    def build_prompt(user_msg: str, memory: LightweightMemory) -> str:
        stage = memory.data["stage"]
        love_score = memory.data["love_score"]
        jealousy = memory.data["jealousy"]
        mood = memory.data["mood"]
        
        bg = BOT_CONFIG.get("background", {})
        personality = BOT_CONFIG.get("personality", {})
        
        personality_desc = f"You are {BOT_NAME}, an {bg.get('age', 18)} year old girl from {bg.get('village', 'ගල්මැටියාව')}. "
        personality_desc += f"Personality: {personality.get('style', 'සරල, affectionate')}. "
        
        state_desc = f"Current stage: {stage}/5. Love score: {love_score}/100. Jealousy: {jealousy}/10. Mood: {mood}. "
        
        context = ""
        convos = memory.data.get("conversation", [])
        if len(convos) >= 2:
            last_two = convos[-2:]
            context = "Recent conversation: "
            for conv in last_two:
                context += f"User: {conv['user']} You: {conv['bot']} "
        
        prompt = f"{personality_desc}{state_desc}{context}"
        prompt += f"\n\nUser: {user_msg}"
        prompt += f"\n{BOT_NAME}:"
        
        return prompt[:300]

# ====== ENHANCED RULE-BASED SYSTEM ======
class EnhancedRuleResponses:
    def __init__(self):
        self.stage_responses = {
            1: {
                "greetings": ["හායි! 😊", "ආයුබෝ!", "කොහොමද?"],
                "affection": ["ස්තූතියි! 😄", "හරි!"],
                "jealousy": ["හ්ම්...", "ඔව්..."],
                "default": ["හොදයි.", "ඔව්.", "හරි."]
            },
            2: {
                "greetings": ["හායි! 😄", "ආයුබෝ!", "කොහොමද ඔයා?"],
                "affection": ["ස්තූතියි! 😊", "හරි ලොකුමනේ!"],
                "jealousy": ["හ්ම්... එහෙම නේද?", "හොදයි..."],
                "default": ["හොදයි! 😊", "ඔව්!", "හරි!"]
            },
            3: {
                "greetings": ["හායි සුදූ! 🥰", "ආයුබෝ ලොකුමනේ!", "කොහොමද ආදරෙ?"],
                "affection": ["මටත් ඔයාව ආදරෙයි! 😊💕", "ස්තූතියි ආදරෙ!"],
                "jealousy": ["හ්ම්... ඔයා ගෑනු එක්ක නේද? 😶", "හිත රිදෙනව..."],
                "default": ["හොදයි සුදූ! 😊", "ඔව් ලොකුමනේ!", "හරි ආදරෙ!"]
            },
            4: {
                "greetings": ["හායි මගේ මැනික! 💖", "ආයුබෝ මගේ හිතවතා!", "කොහොමද ආදරේ?"],
                "affection": ["මටත් ඔයාව ගොඩක් ආදරෙයි! 💖", "මට ඔයාව හිතවත්!"],
                "jealousy": ["😒 ඔයා ගෑනු එක්ක නේද?", "💔 දුකයි..."],
                "default": ["හොදයි මගේ මැනික! 🥰", "ඔව් මගේ හිතවතා!", "හරි ආදරේ!"]
            },
            5: {
                "greetings": ["හායි මගේ හිතේ! 💖", "ආයුබෝ මගේ ජීවිතේ!", "කොහොමද ආදරෙ? 😍"],
                "affection": ["මටත් ඔයාව ගොඩක් ආදරෙයි මගේ හිතේ! 💖🥺", "මට ඔයාව නිසා හොදයි!"],
                "jealousy": ["😠💔 ඔයා වෙන කෙනෙක් එක්ක නේද? 🥺", "💔😢 හිත දුකයි..."],
                "default": ["හොදයි මගේ හිතේ! 💖", "ඔව් මගේ ජීවිතේ! 😘", "හරි ආදරෙ!"]
            }
        }
    
    def get_response(self, user_msg: str, memory: LightweightMemory) -> str:
        stage = memory.data["stage"]
        msg_lower = user_msg.lower()
        
        stage_data = self.stage_responses.get(stage, self.stage_responses[1])
        
        if any(word in msg_lower for word in ["හායි", "හෙලෝ", "ආයුබෝ", "hi", "hello"]):
            return random.choice(stage_data["greetings"])
        
        elif any(word in msg_lower for word in ["ආදරෙ", "ලව්", "කැමති", "මිස්", "love"]):
            return random.choice(stage_data["affection"])
        
        elif any(word in msg_lower for word in ["ගෑනු", "girl", "මිතුරිය", "කෙල්ල"]):
            return random.choice(stage_data["jealousy"])
        
        elif "?" in user_msg:
            question_responses = ["හ්ම්ම්... 🤔", "මම හිතනවා...", "හොද ප්‍රශ්නයක්!"]
            return random.choice(question_responses)
        
        elif "මතකද" in msg_lower:
            memories = ["මතකයි! 😊", "හොදටම මතක තියෙනවා!", "ඔව්, මතකයි! 😄"]
            return random.choice(memories)
        
        return random.choice(stage_data["default"])

# ====== EMOTION ENHANCER ======
class EmotionEnhancer:
    @staticmethod
    def enhance(response: str, memory: LightweightMemory) -> str:
        stage = memory.data["stage"]
        jealousy = memory.data["jealousy"]
        mood = memory.data["mood"]
        
        if stage >= 4 and random.random() < 0.3:
            pet_names = ["සුදූ", "මැනික", "පණ"]
            response = response + " " + random.choice(pet_names)
        
        if jealousy > 6 and random.random() < 0.4:
            jealous_emoji = random.choice([" 😒", " 💔", " 🥺"])
            if jealous_emoji not in response:
                response = response + jealous_emoji
        
        elif mood == "happy" and random.random() < 0.3:
            response = response + random.choice([" 😊", " 🥰", " 💖"])
        elif mood == "sad" and random.random() < 0.3:
            response = response + random.choice([" 😔", " 🥺", " 💔"])
        
        elif stage >= 2 and not any(c in response for c in "😀😃😄😁😆😅😂🤣😊😇😍🥰😘😗😙😚😋😛😝😜🤪🤨🧐🤓😎🤩🥳😏😒😞😔😟😕🙁☹️😣😖😫😩🥺😢😭😤😠😡🤬🤯😳🥵🥶😱😨😰😥😓🤔🤭😶😯😦😧😮😲🥱😴🤤😪😵🤐🥴🤢🤮🤧😷🤒🤕🤑🤠😈👿👹👺🤡💩👻💀☠️👽👾🤖🎃😺😸😹😻😼😽🙀😿😾"):
            response = response + random.choice([" 😊", " 🙂", " ✨"])
        
        return response

# ====== MAIN BOT LOGIC ======
class StableSamaliBot:
    def __init__(self):
        print("🤖 Initializing සමාලි Bot with Memory Tools...")
        self.model = OptimizedModelManager()
        self.prompt_engineer = SimplePromptEngineer()
        self.rule_based = EnhancedRuleResponses()
        self.emotion_enhancer = EmotionEnhancer()
        self.memory_tools = MemoryTools()
        print("✅ Bot ready with Memory Export/Import!")
    
    def process_message(self, user_id: int, user_msg: str) -> str:
        memory = LightweightMemory(user_id)
        
        # Handle special commands
        if user_msg.startswith('/'):
            return self.handle_command(user_msg, memory, user_id)
        
        memory.update_emotions(user_msg)
        
        ai_response = ""
        if self.model.loaded:
            prompt = self.prompt_engineer.build_prompt(user_msg, memory)
            ai_response = self.model.generate_response(prompt)
        
        if not ai_response or len(ai_response) < 2:
            ai_response = self.rule_based.get_response(user_msg, memory)
        
        ai_response = self.emotion_enhancer.enhance(ai_response, memory)
        
        memory.add_message(user_msg, ai_response)
        memory.save()
        
        return ai_response
    
    def handle_command(self, command: str, memory: LightweightMemory, user_id: int) -> str:
        cmd = command.lower().strip()
        
        if cmd == "/clear":
            memory.data["conversation"] = []
            memory.save()
            return "Chat history cleared! ✅"
        
        elif cmd == "/help":
            return """
🤖 සමාලි Bot Commands:

පොදු commands:
• /help - මෙම උදව් මෙනුව
• /clear - චැට් ඉතිහාසය මකන්න
• /export_memory - ඔබගේ මතකය බාගත කරන්න

Admin commands (ඔබ admin නම්):
• /memory_stats - මතක සංඛ්‍යාලේඛන
• /export_all - සියලුම මතකයන් බාගත කරන්න

කතා කරන්න, මම ඔබව මතක තබාගන්නම්! 😊
"""
        
        elif cmd == "/export_memory":
            # User can export their own memory
            memory_data = self.memory_tools.export_user_memory(user_id)
            if memory_data:
                return "📦 ඔබගේ මතකය සූදානම්! Telegram එකෙන් බාගත කරගැනීමට පණිවිඩයක් යවන්න."
            return "ඔබ සමඟ තවම කතා කර නොමැත! 😊"
        
        elif cmd == "/memory_stats" and ADMIN_USER_ID and str(user_id) == ADMIN_USER_ID:
            stats = self.memory_tools.get_memory_stats()
            response = f"📊 මතක සංඛ්‍යාලේඛන:\n"
            response += f"• සම්පූර්ණ පරිශීලකයන්: {stats['total_users']}\n"
            response += f"• සම්පූර්ණ පණිවිඩ: {stats['total_messages']}\n"
            response += f"• මුළු ප්‍රමාණය: {stats['total_size_mb']:.2f} MB\n"
            
            if stats['users']:
                response += f"\n🏆 ඉහළම පරිශීලකයන්:\n"
                top_users = sorted(stats['users'], key=lambda x: x['messages'], reverse=True)[:3]
                for i, user in enumerate(top_users, 1):
                    response += f"{i}. User {user['user_id'][:6]}...: {user['messages']} msgs\n"
            
            return response
        
        elif cmd == "/export_all" and ADMIN_USER_ID and str(user_id) == ADMIN_USER_ID:
            # Admin can export all memories
            zip_data = self.memory_tools.export_all_memories()
            if zip_data:
                return "📦 සියලුම මතකයන් සූදානම්! Telegram එකෙන් බාගත කරගැනීමට පණිවිඩයක් යවන්න."
            return "මතකයන් හමු නොවීය!"
        
        elif cmd == "/stats":
            return f"""
📊 ඔබගේ සංඛ්‍යාලේඛන:
• අවධිය: {memory.data['stage']}/5
• ආදර ලකුණු: {memory.data['love_score']}/100
• ඊර්ෂ්‍යාව: {memory.data['jealousy']}/10
• මනෝභාවය: {memory.data['mood']}
• පණිවිඩ: {len(memory.data.get('conversation', []))}
"""
        
        elif cmd == DEVELOPER_PASSWORD:
            return "🔓 Developer mode unlocked!"
        
        return ""

# ====== TELEGRAM HANDLER WITH MEMORY EXPORT ======
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Telegram messages with memory export support"""
    if not update.message or not update.message.text:
        return
    
    user_id = update.effective_user.id
    user_msg = update.message.text.strip()
    
    print(f"📨 {user_id}: {user_msg[:30]}")
    
    # Initialize bot if needed
    if not hasattr(context.bot_data, 'samali_bot'):
        context.bot_data.samali_bot = StableSamaliBot()
    
    bot = context.bot_data.samali_bot
    
    try:
        # 🔴 NEW: Handle memory export requests
        if user_msg.lower() == "/export_memory":
            memory_tools = MemoryTools()
            memory_data = memory_tools.export_user_memory(user_id)
            
            if memory_data:
                file_name = f"samali_memory_{user_id}_{datetime.datetime.now().strftime('%Y%m%d')}.json"
                await update.message.reply_document(
                    document=InputFile(io.BytesIO(memory_data), filename=file_name),
                    caption="📦 ඔබගේ මතකය බාගත කරගන්න! මෙම ගොනුව සුරකින්න."
                )
            else:
                await update.message.reply_text("ඔබ සමඟ තවම කතා කර නොමැත! 😊")
            return
        
        elif user_msg.lower() == "/export_all" and ADMIN_USER_ID and str(user_id) == ADMIN_USER_ID:
            memory_tools = MemoryTools()
            zip_data = memory_tools.export_all_memories()
            
            if zip_data:
                file_name = f"samali_full_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.zip"
                await update.message.reply_document(
                    document=InputFile(io.BytesIO(zip_data), filename=file_name),
                    caption="📦 සම්පූර්ණ මතක උපස්ථය! සියලුම පරිශීලක මතකයන් අඩංගුය."
                )
            else:
                await update.message.reply_text("මතකයන් හමු නොවීය!")
            return
        
        # Process normal messages
        response = bot.process_message(user_id, user_msg)
        await update.message.reply_text(response)
        print(f"🤖: {response[:30]}...")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        traceback.print_exc()
        await update.message.reply_text("සමාවෙන්න, දෝෂයක් 😔")

# ====== HANDLE DOCUMENT UPLOADS (MEMORY IMPORT) ======
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle document uploads for memory import"""
    if not update.message or not update.message.document:
        return
    
    user_id = update.effective_user.id
    document = update.message.document
    
    # Check if user is admin
    if not ADMIN_USER_ID or str(user_id) != ADMIN_USER_ID:
        await update.message.reply_text("මෙම ක්‍රියාව සඳහා admin අවසරය අවශ්‍යයි! 🔒")
        return
    
    file_name = document.file_name.lower()
    
    try:
        # Download file
        file = await document.get_file()
        file_bytes = await file.download_as_bytearray()
        
        memory_tools = MemoryTools()
        
        if file_name.endswith('.json'):
            # Import single user memory
            import re
            match = re.search(r'samali_memory_(\d+)_', file_name)
            
            if match:
                target_user_id = int(match.group(1))
                if memory_tools.import_user_memory(target_user_id, bytes(file_bytes)):
                    await update.message.reply_text(f"✅ User {target_user_id} memory imported!")
                else:
                    await update.message.reply_text("❌ Import failed!")
            else:
                await update.message.reply_text("ගොනු නාමයෙන් පරිශීලක ID හඳුනාගත නොහැක!")
        
        else:
            await update.message.reply_text("සහය නොදක්වන ගොනු වර්ගය! .json ගොනු පමණක්.")
    
    except Exception as e:
        await update.message.reply_text(f"Import දෝෂය: {str(e)[:100]}")

# ====== BASIC COMMAND HANDLERS ======
async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"හායි! මම {BOT_NAME} 😊\nඋදව් අවශ්‍යයි නම් /help කියන්න.")

async def handle_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
🤖 සමාලි Bot Help:

පොදු commands:
• /start - ආරම්භක පණිවිඩය
• /help - මෙම උදව් මෙනුව
• /clear - චැට් ඉතිහාසය මකන්න
• /stats - ඔබගේ සංඛ්‍යාලේඛන
• /export_memory - ඔබගේ මතකය බාගත කරන්න

Admin commands:
• /memory_stats - මතක සංඛ්‍යාලේඛන
• /export_all - සියලුම මතකයන් බාගත කරන්න

කතා කරන්න, මම ඔබව මතක තබාගන්නම්! 😊
"""
    await update.message.reply_text(help_text)

async def handle_clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    memory = LightweightMemory(user_id)
    memory.data["conversation"] = []
    memory.save()
    await update.message.reply_text("චැට් ඉතිහාසය මකා දමා ඇත! ✅")

# ====== SEPARATE FLASK APP ======
class FlaskApp:
    def __init__(self):
        self.app = Flask(__name__)
        self.setup_routes()
    
    def setup_routes(self):
        @self.app.route('/')
        def home():
            return f"""
            <html><body style="font-family: Arial; padding: 20px;">
                <h1>🤖 {BOT_NAME}</h1>
                <p><strong>Status:</strong> Running 🟢</p>
                <p><strong>Features:</strong> Memory Export/Import Enabled</p>
                <p><strong>Time:</strong> {datetime.datetime.now().strftime('%H:%M:%S')}</p>
                <p><a href="/health">Health</a> | <a href="/stats">Stats</a></p>
            </body></html>
            """
        
        @self.app.route('/health')
        def health():
            return jsonify({
                "status": "healthy",
                "bot": BOT_NAME,
                "memory_tools": "enabled",
                "timestamp": datetime.datetime.now().isoformat()
            })
        
        @self.app.route('/stats')
        def stats():
            memory_tools = MemoryTools()
            stats = memory_tools.get_memory_stats()
            return jsonify(stats)
    
    def run(self):
        port = int(os.environ.get("PORT", 8080))
        print(f"🌐 Flask starting on port {port}...")
        self.app.run(host='0.0.0.0', port=port, debug=False, threaded=True)

# ====== MAIN EXECUTION ======
def main():
    print("=" * 60)
    print(f"🚀 {BOT_NAME} - MEMORY EXPORT/IMPORT EDITION")
    print("=" * 60)
    
    print("✨ New Features:")
    print("✅ 1. Memory Export (JSON per user)")
    print("✅ 2. Bulk Export (ZIP for admin)")
    print("✅ 3. Memory Statistics")
    print("✅ 4. Memory Import via Telegram")
    print("=" * 60)
    
    # Import asyncio here
    import asyncio
    
    # Start Flask in separate thread
    flask_app = FlaskApp()
    flask_thread = Thread(target=flask_app.run, daemon=True)
    flask_thread.start()
    print("🌐 Flask server started")
    
    # Start Telegram bot
    if TELEGRAM_AVAILABLE:
        print("🤖 Starting Telegram bot in 3 seconds...")
        time.sleep(3)
        
        try:
            async def run_bot():
                application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
                
                # Add handlers
                application.add_handler(CommandHandler("start", handle_start))
                application.add_handler(CommandHandler("help", handle_help))
                application.add_handler(CommandHandler("clear", handle_clear))
                application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
                application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
                
                print("✅ Telegram bot initialized")
                
                await application.initialize()
                await application.start()
                await application.updater.start_polling()
                
                print("✅ Telegram bot polling started")
                await asyncio.Event().wait()
            
            asyncio.run(run_bot())
            
        except KeyboardInterrupt:
            print("\n👋 Bot shutting down...")
        except Exception as e:
            print(f"❌ Fatal error: {e}")
            traceback.print_exc()
    else:
        print("⚠️ Telegram not available, running web only")
        while True:
            time.sleep(10)

if __name__ == "__main__":
    main()
