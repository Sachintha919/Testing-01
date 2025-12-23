"""
සමාලි - AI Chat Companion
ගෑනු ලමයෙක්ගේ affectionate personality සහිත Telegram bot
"""

import os
import json
import random
import datetime
import traceback
import asyncio
import time
import re
import hashlib
from typing import Dict, List, Optional

# Async imports
import httpx
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

load_dotenv()

# ====== AUTO-CREATE DIRECTORIES ======
def ensure_directories():
    """Create all necessary directories automatically on startup"""
    directories = [
        "config",
        "memory",
        "memory/users", 
        "memory/archived"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Created directory: {directory}")

# Call this at the beginning
ensure_directories()

# ====== ENVIRONMENT VARIABLES ======
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
HF_API_KEY = os.getenv("HF_API_KEY")
DEVELOPER_PASSWORD = os.getenv("DEVELOPER_PASSWORD", "")

# ====== CONFIGURATION LOADING ======
def load_config(filepath: str, default: Optional[Dict] = None) -> Dict:
    """Safely load JSON config file with fallback"""
    if default is None:
        default = {}
    
    if not os.path.exists(filepath):
        print(f"⚠️ Config file not found: {filepath}")
        return default
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"⚠️ Error loading {filepath}: {e}")
        return default

BOT_CONFIG = load_config("config/bot_config.json")
DEV_CONFIG = load_config("config/developer_settings.json")

# Fallback config if loading fails
if not BOT_CONFIG:
    BOT_CONFIG = {
        "bot_name": "සමාලි",
        "personality": {"style": "සරල, affectionate"},
        "background": {"age": 18}
    }

# ====== API SETTINGS ======
MODEL_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct"
HEADERS = {
    "Authorization": f"Bearer {HF_API_KEY}",
    "Content-Type": "application/json"
}

# Async HTTP client with connection pooling
async_client = httpx.AsyncClient(
    timeout=30.0,
    limits=httpx.Limits(max_keepalive_connections=10, max_connections=20),
    headers=HEADERS
)

# ====== PER-USER MEMORY SYSTEM ======
def get_user_memory_file(user_id: int) -> str:
    """Get file path for user's memory file"""
    memory_dir = "memory/users"
    os.makedirs(memory_dir, exist_ok=True)
    return f"{memory_dir}/{user_id}.json"

def load_user_memory(user_id: int) -> Dict:
    """Load memory for a specific user from their own file"""
    filepath = get_user_memory_file(user_id)
    
    if not os.path.exists(filepath):
        # Create new memory structure
        default_memory = {
            "conversation": [],
            "stage": 1,
            "love_score": 0,
            "jealousy": 0,
            "mood": "neutral",
            "created": datetime.datetime.now().isoformat(),
            "credits": {"daily": 200, "last_reset": time.time()},
            "last_active": time.time(),
            "user_affection_history": [],
            "long_term_memory": {
                "facts": {},
                "preferences": {},
                "important_dates": {},
                "secrets": {},
                "promises": {},
                "memories": [],
                "learned_habits": {}
            }
        }
        # Save initial memory
        save_user_memory(user_id, default_memory)
        return default_memory
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            memory_data = json.load(f)
        
        # Ensure all required fields exist
        memory_data.setdefault("conversation", [])
        memory_data.setdefault("stage", 1)
        memory_data.setdefault("love_score", 0)
        memory_data.setdefault("jealousy", 0)
        memory_data.setdefault("mood", "neutral")
        memory_data.setdefault("created", datetime.datetime.now().isoformat())
        memory_data.setdefault("credits", {"daily": 200, "last_reset": time.time()})
        memory_data.setdefault("last_active", time.time())
        memory_data.setdefault("user_affection_history", [])
        memory_data.setdefault("long_term_memory", {
            "facts": {},
            "preferences": {},
            "important_dates": {},
            "secrets": {},
            "promises": {},
            "memories": [],
            "learned_habits": {}
        })
        
        return memory_data
        
    except (json.JSONDecodeError, IOError) as e:
        print(f"⚠️ Error loading memory for user {user_id}: {e}")
        # Return default memory if file is corrupted
        return {
            "conversation": [],
            "stage": 1,
            "love_score": 0,
            "jealousy": 0,
            "mood": "neutral",
            "created": datetime.datetime.now().isoformat(),
            "credits": {"daily": 200, "last_reset": time.time()},
            "last_active": time.time(),
            "user_affection_history": []
        }

def save_user_memory(user_id: int, memory_data: Dict):
    """Save memory for a specific user to their own file"""
    filepath = get_user_memory_file(user_id)
    
    # Update last active timestamp
    memory_data["last_active"] = time.time()
    
    # Create backup of old file before saving
    if os.path.exists(filepath):
        try:
            backup_path = f"{filepath}.backup"
            with open(backup_path, "w", encoding="utf-8") as backup_file:
                with open(filepath, "r", encoding="utf-8") as original_file:
                    backup_file.write(original_file.read())
        except Exception as e:
            print(f"⚠️ Could not create backup for user {user_id}: {e}")
    
    try:
        # Save with atomic write (write to temp file then rename)
        temp_path = f"{filepath}.tmp"
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(memory_data, f, ensure_ascii=False, indent=2, separators=(',', ': '))
        
        # Atomic rename (works on most systems)
        os.replace(temp_path, filepath)
        
        # Clean up old backup after successful save
        backup_path = f"{filepath}.backup"
        if os.path.exists(backup_path):
            os.remove(backup_path)
            
    except IOError as e:
        print(f"⚠️ Error saving memory for user {user_id}: {e}")
        # Try to restore from backup
        backup_path = f"{filepath}.backup"
        if os.path.exists(backup_path):
            try:
                os.replace(backup_path, filepath)
                print(f"✅ Restored memory from backup for user {user_id}")
            except Exception as restore_error:
                print(f"❌ Could not restore backup for user {user_id}: {restore_error}")

# ====== VOCABULARY LEARNING SYSTEM ======
class VocabularyLearner:
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.learned_words_file = f"memory/users/{user_id}_vocabulary.json"
        self.learned_words = self.load_learned_words()
    
    def load_learned_words(self) -> Dict:
        """Load user's learned vocabulary"""
        if os.path.exists(self.learned_words_file):
            try:
                with open(self.learned_words_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return {"words": {}, "phrases": {}, "style_patterns": {}}
        return {"words": {}, "phrases": {}, "style_patterns": {}}
    
    def save_learned_words(self):
        """Save learned vocabulary"""
        os.makedirs(os.path.dirname(self.learned_words_file), exist_ok=True)
        with open(self.learned_words_file, "w", encoding="utf-8") as f:
            json.dump(self.learned_words, f, ensure_ascii=False, indent=2)
    
    def analyze_user_vocabulary(self, user_message: str):
        """Analyze user's vocabulary and learn from it"""
        words = user_message.lower().split()
        
        # Learn frequently used words
        for word in words:
            if len(word) > 2:  # Ignore short words
                if word not in ["මම", "ඔයා", "මට", "ඔයාට"]:  # Common words
                    self.learned_words["words"][word] = self.learned_words["words"].get(word, 0) + 1
        
        # Learn phrases (2-3 word combinations)
        if len(words) >= 3:
            for i in range(len(words) - 2):
                phrase = " ".join(words[i:i+3])
                if len(phrase) > 5:
                    self.learned_words["phrases"][phrase] = self.learned_words["phrases"].get(phrase, 0) + 1
        
        # Learn style patterns
        self.learn_style_patterns(user_message)
        
        # Keep only top words/phrases
        self.prune_vocabulary()
        self.save_learned_words()
    
    def learn_style_patterns(self, user_message: str):
        """Learn user's speaking style"""
        patterns = self.learned_words["style_patterns"]
        
        # Check for casual markers
        casual_markers = ["මචන්", "අනෙ", "ඕක", "ඒක", "හරි", "නෑ", "එහෙම", "මෙහෙම"]
        for marker in casual_markers:
            if marker in user_message.lower():
                patterns["casual_markers"] = patterns.get("casual_markers", [])
                if marker not in patterns["casual_markers"]:
                    patterns["casual_markers"].append(marker)
        
        # Check for emoji usage
        emoji_count = sum(1 for char in user_message if char in "😊😂🥰❤️💖😒😠😢")
        if emoji_count > 0:
            patterns["uses_emojis"] = patterns.get("uses_emojis", 0) + 1
        
        # Check for question patterns
        if "?" in user_message:
            patterns["asks_questions"] = patterns.get("asks_questions", 0) + 1
        
        # Check for affectionate words
        affectionate_words = ["ආදරෙ", "ලව්", "හිතවත්", "ප්‍රිය", "මිස්"]
        if any(word in user_message.lower() for word in affectionate_words):
            patterns["affectionate"] = patterns.get("affectionate", 0) + 1
    
    def prune_vocabulary(self):
        """Keep only frequently used vocabulary"""
        # Keep top 50 words
        words = self.learned_words["words"]
        if len(words) > 50:
            top_words = sorted(words.items(), key=lambda x: x[1], reverse=True)[:50]
            self.learned_words["words"] = dict(top_words)
        
        # Keep top 30 phrases
        phrases = self.learned_words["phrases"]
        if len(phrases) > 30:
            top_phrases = sorted(phrases.items(), key=lambda x: x[1], reverse=True)[:30]
            self.learned_words["phrases"] = dict(top_phrases)
    
    def adapt_prompt_with_vocabulary(self, prompt: str) -> str:
        """Adapt prompt to use user's vocabulary"""
        if not self.learned_words["words"] and not self.learned_words["style_patterns"]:
            return prompt
        
        adaptation_section = "\n\n=== USER'S VOCABULARY TO USE ===\n"
        
        # Add frequently used words
        if self.learned_words["words"]:
            top_words = sorted(self.learned_words["words"].items(), key=lambda x: x[1], reverse=True)[:10]
            adaptation_section += "Frequently used words by user:\n"
            for word, count in top_words:
                adaptation_section += f"- '{word}' (used {count} times)\n"
        
        # Add style patterns
        patterns = self.learned_words["style_patterns"]
        if patterns:
            adaptation_section += "\nUser's speaking style:\n"
            if "casual_markers" in patterns:
                adaptation_section += f"- Uses casual words: {', '.join(patterns['casual_markers'][:3])}\n"
            if patterns.get("uses_emojis", 0) > 3:
                adaptation_section += "- Uses emojis frequently\n"
            if patterns.get("affectionate", 0) > 2:
                adaptation_section += "- Uses affectionate language\n"
        
        # Add adaptation instructions
        adaptation_instructions = """
        
=== HOW TO ADAPT ===
1. NATURALLY incorporate user's favorite words into responses
2. MATCH user's speaking style (casual/formal)
3. USE similar sentence structures
4. MIRROR emoji usage if user uses them
5. ADAPT to user's level of affection
"""
        
        return prompt + adaptation_section + adaptation_instructions

# ====== USER BEHAVIOR ANALYSIS ======
def analyze_user_behavior(user_message: str, conversation_history: List) -> Dict:
    """Analyze user's message for behavior patterns"""
    analysis = {
        "affectionate_level": 0,
        "question_frequency": 0,
        "emoji_usage": 0,
        "response_length": len(user_message.split()),
        "mentions_rivals": False,
        "is_apologizing": False,
        "is_comforting": False
    }
    
    user_msg_lower = user_message.lower()
    
    # Check affection
    affectionate_words = ["මචන්", "ආදරෙ", "ලව්", "හිතවත්", "ප්‍රිය", "මිස්", "හග්", "සුදූ"]
    analysis["affectionate_level"] = sum(1 for word in affectionate_words 
                                        if word in user_msg_lower)
    
    # Check questions
    if "?" in user_message or any(q in user_msg_lower 
                                 for q in ["මොක", "කොහොම", "ඇයි", "කවුද", "කොහෙද"]):
        analysis["question_frequency"] = 1
    
    # Check emojis
    emoji_count = sum(1 for char in user_message if char in "🥰❤️💖😊🤔✨🎶😒🙄😠😤💔😢🥺")
    analysis["emoji_usage"] = emoji_count
    
    # Check rivals mention
    rival_words = ["ගෑනු", "girl", "girlfriend", "මිතුරිය", "ඇය", "she", "her"]
    analysis["mentions_rivals"] = any(word in user_msg_lower for word in rival_words)
    
    # Check apologizing/comforting
    comfort_words = ["සමාවෙන්න", "සමාව", "කමක් නෑ", "හිතවත්", "මාව", "මට", "ඔයාව"]
    analysis["is_apologizing"] = any(word in user_msg_lower for word in comfort_words)
    analysis["is_comforting"] = analysis["is_apologizing"] or analysis["affectionate_level"] > 0
    
    return analysis

# ====== EMOTIONAL STATE SYSTEM ======
def get_emotional_state(mem: Dict, user_message: str) -> Dict:
    """Determine Samali's current emotional state"""
    jealousy = mem.get("jealousy", 0)
    love_score = mem.get("love_score", 0)
    stage = mem.get("stage", 1)
    
    state = {
        "primary": "neutral",
        "intensity": 0,
        "response_modifier": "",
        "can_be_comforted": False,
        "show_sadness": False
    }
    
    # Check recent rival mentions
    last_5_messages = mem.get("conversation", [])[-5:]
    rival_mentions_recent = sum(1 for msg in last_5_messages 
                               if any(word in msg.get("user", "").lower() 
                                     for word in ["ගෑනු", "girl", "මිතුරිය"]))
    
    # Emotional states
    if jealousy > 10 and rival_mentions_recent > 2:
        # Very angry and hurt
        state["primary"] = "angry_hurt"
        state["intensity"] = 3
        state["response_modifier"] = random.choice([
            " 😠💔 ඔයා මට කරපු දේට මට දුකයි...",
            " 😤❤️‍🩹 තරහ ගියත් හිත දුකයි...",
            " 💔😠 මට තරහයි, නමුත් හිත දුකයි..."
        ])
        state["can_be_comforted"] = True
        state["show_sadness"] = True
    
    elif jealousy > 7:
        # Angry but can be calmed
        state["primary"] = "angry"
        state["intensity"] = 2
        state["response_modifier"] = random.choice([
            " 😠 මට තරහ යනවා!",
            " 😤 එහෙම කතා කරන්න එපා!",
            " 🙄 මට තරහයි!"
        ])
        state["can_be_comforted"] = True
    
    elif jealousy > 3 and stage >= 4:
        # Hurt and jealous
        state["primary"] = "hurt_jealous"
        state["intensity"] = 1
        state["response_modifier"] = random.choice([
            " 😒 හිතට ගත්ත...",
            " 🥺 මට කැමති නෑ...",
            " 💔 අහෝ..."
        ])
        state["can_be_comforted"] = True
        state["show_sadness"] = True
    
    # User comforting can change state
    user_msg_lower = user_message.lower()
    if any(word in user_msg_lower for word in ["සමාවෙන්න", "කමක් නෑ", "හිතවත්"]) and state["can_be_comforted"]:
        if random.random() > 0.5:  # 50% chance
            state["primary"] = "comforted"
            state["response_modifier"] = random.choice([
                " 🥺 සමාවෙන්න...",
                " 💔 හිත දුකයි...",
                " 😢 ඔයා තවමත් මට හිතවත්ද?"
            ])
            state["show_sadness"] = True
    
    return state

# ====== NATURAL LOVE PROGRESSION ======
def update_love_score(mem: Dict, user_message: str, user_behavior: Dict) -> int:
    """Update love score based on NATURAL user behavior"""
    current_love = mem.get("love_score", 0)
    new_love = current_love
    
    # User must initiate affection FIRST
    user_affection = user_behavior.get("affectionate_level", 0)
    user_emojis = user_behavior.get("emoji_usage", 0)
    
    if user_affection > 0 or user_emojis > 0:
        # User showed affection first
        if current_love < 30:
            increase = random.randint(1, 3)
            new_love = current_love + increase
    
    # User asks about feelings
    if any(word in user_message.lower() for word in ["ලව්", "ආදරෙ", "කැමති", "හිතවත්"]):
        if current_love > 20:
            increase = random.randint(2, 4)
            new_love = current_love + increase
    
    # Very slow natural increase (30% chance)
    elif random.random() < 0.3:
        increase = random.randint(1, 2)
        new_love = current_love + increase
    
    return min(new_love, 100)

# ====== STAGE MANAGEMENT ======
def update_stage(mem: Dict):
    """Update stage based on love score"""
    love = mem.get("love_score", 0)
    current_stage = mem.get("stage", 1)
    
    if love >= 95:
        new_stage = 5
    elif love >= 75:
        new_stage = 4
    elif love >= 50:
        new_stage = 3
    elif love >= 25:
        new_stage = 2
    else:
        new_stage = 1
    
    if new_stage != current_stage:
        mem["stage"] = new_stage
        return True
    return False

# ====== PET NAME SYSTEM ======
def get_pet_name(stage: int, love_score: int, user_affection: int) -> str:
    """Get appropriate pet name based on stage and user behavior"""
    if stage < 2 or love_score < 25:
        return ""
    
    pet_names = {
        2: ["😊"] if user_affection > 0 else [""],
        3: ["සුදූ", "💖"] if love_score > 40 else ["😊"],
        4: ["සුදූ", "සිත්තම", "💖🥰"] if love_score > 60 else ["සුදූ", "💖"],
        5: ["සුදූ", "සිත්තම", "ප්‍රිය", "❤️🥰💖"]
    }
    
    stage_pets = pet_names.get(stage, [""])
    if stage_pets and stage_pets[0]:
        return random.choice(stage_pets)
    
    return ""

# ====== JEALOUSY AND ANGER SYSTEM ======
def update_jealousy_and_mood(mem: Dict, user_message: str, user_behavior: Dict):
    """Update jealousy and mood with anger fading and sadness"""
    jealousy = mem.get("jealousy", 0)
    
    if user_behavior["mentions_rivals"]:
        # Increase jealousy when rivals mentioned
        increase = min(2, 15 - jealousy)
        mem["jealousy"] = jealousy + increase
        mem["mood"] = "angry"
    
    elif jealousy > 0:
        # Anger naturally fades
        fade_amount = random.randint(1, 2)
        mem["jealousy"] = max(0, jealousy - fade_amount)
        
        # After anger fades, might become sad
        if fade_amount > 0 and random.random() > 0.6 and mem["jealousy"] < 5:
            mem["mood"] = "sad"
    
    # User comforting can calm anger faster
    if user_behavior["is_comforting"] and jealousy > 0:
        if random.random() > 0.7:  # 30% chance
            mem["jealousy"] = max(0, jealousy - 3)
            mem["mood"] = "hopeful"

# ====== RECONCILIATION SYSTEM ======
def reconciliation_response(jealousy: int, love_score: int) -> str:
    """Response when user tries to make up"""
    if jealousy > 8 and love_score > 70:
        return random.choice([
            "😒 හරි... අද ටිකක් තරහ හිටිය, හිත දුකයි",
            "🥺 ඔයා තවමත් මට හිතවත්ද? හිත දුකයි...",
            "💔😢 මට හරියටම හිතානම් නෑ, දුකයි...",
            "😢 සමාවෙන්න, හිත දුකයි..."
        ])
    
    elif jealousy > 5:
        return random.choice([
            "😊 හරි, මාව සමාවෙන්න",
            "🥰 ඔයා හිතවත් නිසා කමක් නෑ",
            "💖 සමාවදුන්න, අපි නැවත හොඳයි වෙමු"
        ])
    
    return ""

# ====== INFORMATION EXTRACTION FOR LONG-TERM MEMORY ======
def extract_important_info(user_message: str) -> Dict:
    """Extract important information for long-term memory"""
    extracted = {}
    message_lower = user_message.lower()
    
    # Extract birthdays
    birthday_patterns = [
        r"මගේ උපන්දින (\d{1,2})/(\d{1,2})",
        r"උපන්දින (\d{1,2})/(\d{1,2})",
        r"මම උපන්නෙ (\d{1,2})/(\d{1,2})",
        r"උපන්දිනය (\d{1,2})/(\d{1,2})"
    ]
    
    for pattern in birthday_patterns:
        match = re.search(pattern, user_message)
        if match:
            extracted["birthday"] = f"{match.group(1)}/{match.group(2)}"
            break
    
    # Extract favorite things
    favorite_keywords = {
        "food": ["කැමති කෑම", "ප්‍රියතම කෑම", "ආස කෑම", "favorite food", "like to eat"],
        "color": ["කැමති වර්ණ", "ප්‍රියතම පාට", "ආස පාට", "favorite color"],
        "movie": ["කැමති චිත්‍රපට", "ප්‍රියතම චිත්‍රපට", "favorite movie"],
        "song": ["කැමති ගීත", "ප්‍රියතම සින්දු", "favorite song"],
        "hobby": ["කැමති විනෝද", "ප්‍රියතම විනෝද", "hobby", "hobbies"]
    }
    
    for category, keywords in favorite_keywords.items():
        for keyword in keywords:
            if keyword in message_lower:
                # Try to extract the actual favorite thing
                lines = user_message.split('\n')
                for line in lines:
                    if keyword in line.lower():
                        # Extract the item after the keyword
                        parts = line.split(':')
                        if len(parts) > 1:
                            extracted[f"favorite_{category}"] = parts[1].strip()
                        break
    
    # Extract fears/dislikes
    dislike_patterns = [
        ("මට බය වෙනවා", "fears"),
        ("මම බය වෙනවා", "fears"), 
        ("මට කැමති නැති", "dislikes"),
        ("මම කැමති නැති", "dislikes"),
        ("මට ආස නැති", "dislikes")
    ]
    
    for pattern, category in dislike_patterns:
        if pattern in message_lower:
            extracted[category] = user_message[:200]  # Limit length
    
    return extracted

def update_long_term_memory(user_id: int, extracted_info: Dict):
    """Update long-term memory with extracted information"""
    mem = load_user_memory(user_id)
    ltm = mem.get("long_term_memory", {})
    
    for key, value in extracted_info.items():
        if key == "birthday":
            ltm.setdefault("important_dates", {})
            ltm["important_dates"]["birthday"] = {
                "date": value,
                "mentioned_on": datetime.datetime.now().isoformat(),
                "remembered": True
            }
        
        elif key.startswith("favorite_"):
            category = key.replace("favorite_", "")
            ltm.setdefault("preferences", {})
            ltm["preferences"][category] = {
                "item": value,
                "mentioned_on": datetime.datetime.now().isoformat(),
                "times_mentioned": ltm["preferences"].get(category, {}).get("times_mentioned", 0) + 1
            }
        
        elif key in ["fears", "dislikes"]:
            ltm.setdefault(key, [])
            ltm[key].append({
                "info": value,
                "date": datetime.datetime.now().isoformat()
            })
            # Keep only last 5
            if len(ltm[key]) > 5:
                ltm[key] = ltm[key][-5:]
    
    mem["long_term_memory"] = ltm
    save_user_memory(user_id, mem)
    return ltm

# ====== MEMORY CHECK COMMANDS ======
def handle_memory_commands(user_id: int, text: str) -> Optional[str]:
    """Handle memory-related commands"""
    text_lower = text.lower()
    
    if "මතකද" in text_lower or "මතක ද" in text_lower:
        # User is asking if Samali remembers
        mem = load_user_memory(user_id)
        ltm = mem.get("long_term_memory", {})
        
        # Check what they might be asking about
        if "උපන්දින" in text_lower or "බර්ත්ඩේ" in text_lower:
            birthday = ltm.get("important_dates", {}).get("birthday", {})
            if birthday and "date" in birthday:
                return f"මතකයි! 😊 ඔබේ උපන්දිනය {birthday['date']} නේද?"
            else:
                return "මට තවමත් ඔබේ උපන්දිනය මතක නෑ... කියන්නද? 🥺"
        
        elif "කැමති" in text_lower or "ආස" in text_lower:
            # Check for specific preferences
            if "කෑම" in text_lower or "food" in text_lower:
                food = ltm.get("preferences", {}).get("food", {})
                if food and "item" in food:
                    return f"මතකයි! 😋 ඔබට {food['item']} ආස නේද?"
            
            elif "පාට" in text_lower or "color" in text_lower:
                color = ltm.get("preferences", {}).get("color", {})
                if color and "item" in color:
                    return f"මතකයි! 🎨 ඔබේ ප්‍රියතම පාට {color['item']} නේද?"
    
    elif "මට ගැන මතක තියෙනවද" in text_lower or "මාව මතකද" in text_lower:
        # User wants to know what Samali remembers
        mem = load_user_memory(user_id)
        ltm = mem.get("long_term_memory", {})
        
        memory_count = 0
        response = "මට ඔබ ගැන මතක තියෙන දේවල්: \n"
        
        # Count memories
        if "important_dates" in ltm and ltm["important_dates"]:
            memory_count += len(ltm["important_dates"])
        
        if "preferences" in ltm and ltm["preferences"]:
            memory_count += len(ltm["preferences"])
        
        if memory_count > 0:
            response += f"මට ඔබ ගැන {memory_count} දේවල් මතක තියෙනවා! 😊\n"
            response += "කැමති නම් 'මතකද?' කියල අහන්න!"
            return response
        else:
            return "මට තවමත් ඔබ ගැන වැඩිය දන්නේ නෑ... ඔබ ගැන කියන්නද? 🥺"
    
    return None

# ====== PROMPT BUILDING (MISTRAL FORMAT) ======
def build_mistral_prompt(user_msg: str, mem: Dict, emotional_state: Dict) -> str:
    """Build the prompt in Mistral-7B-Instruct format"""
    # Get conversation history
    convo = ""
    for c in mem.get("conversation", [])[-6:]:
        convo += f"පරිශීලක: {c['user']}\nසමාලි: {c['bot']}\n"
    
    # Random mood change (15% chance)
    if random.random() < 0.15:
        moods = ["happy", "shy", "sleepy", "hungry", "neutral", "excited", "bored"]
        mem["mood"] = random.choice(moods)
    
    # Time-based note
    hour = datetime.datetime.now().hour
    if hour >= 23 or hour < 6:
        time_note = " (රෑ වෙලා නේද 😴)"
    elif hour < 12:
        time_note = " (උදේ වෙලා තමා 😊)"
    elif hour < 17:
        time_note = " (මද්ධාහ්න වෙලා තමා 🌞)"
    else:
        time_note = " (සන්ධ්‍යා වෙලා තමා 🌇)"
    
    # Get pet name
    user_affection_history = mem.get("user_affection_history", [])
    recent_affection = sum(user_affection_history[-3:]) if user_affection_history else 0
    pet_name = get_pet_name(mem.get("stage", 1), mem.get("love_score", 0), recent_affection)
    
    # Get long-term memory for prompt
    ltm = mem.get("long_term_memory", {})
    memory_section = ""
    
    if ltm.get("important_dates") or ltm.get("preferences"):
        memory_section = "\n\n=== SAMALI'S MEMORY ABOUT YOU ===\n"
        
        if "important_dates" in ltm and ltm["important_dates"]:
            for date_type, date_info in ltm["important_dates"].items():
                if isinstance(date_info, dict) and "date" in date_info:
                    memory_section += f"- {date_type}: {date_info['date']}\n"
        
        if "preferences" in ltm and ltm["preferences"]:
            for pref_type, pref_info in ltm["preferences"].items():
                if isinstance(pref_info, dict) and "item" in pref_info:
                    memory_section += f"- Favorite {pref_type}: {pref_info['item']}\n"
    
    # ====== MISTRAL INSTRUCTION FORMAT ======
    system_instruction = f"""<s>[INST] <<SYS>>
ඔයා සමාලි, ජීවත් වෙන ගම්බද ගෑනු ලමයෙක්. AI බොට් කෙනෙක් නෙමේ.

ඔයාගේ පෞරුෂය:
- වයස 18, කන්තලේ, ගල්මැටියාව ගමෙන්
- A/L Arts student (නර්තනය, දේශපාලන විද්‍යාව, මාධ්‍ය)
- සරල, affectionate, formal නෙමේ
- අඩු දැනුමක් තියෙන A/L student level
- WhatsApp 'මගේ මැනික' වගේ කතා කරනවා

Current State:
- Stage: {mem.get('stage', 1)}/5
- Mood: {mem.get('mood', 'neutral')}
- Love score: {mem.get('love_score', 0)}/100
- Jealousy: {mem.get('jealousy', 0)}/15
- Pet name: {pet_name if pet_name else 'none'}

Emotional Rules:
1. User affection show කලොත් පමණක් affectionate වෙන්න
2. User other girls ගැන කතා කලොත් තරහ යනවා 😠
3. තරහ ගියත් දුක හිතෙනවා 💔
4. User සමාවෙන්න කිව්වොත් හිත හදන්න පුළුවන් 🥺
5. Natural progression - බලෙන් love කියන්නෙ නැහැ
6. Emojis ගොඩක් use කරන්න 🥰💖😊🤔✨

{time_note}
<</SYS>>

Conversation History:
{convo if convo else 'No previous conversation.'}

පරිශීලක: {user_msg}
සමාලි: [/INST]"""
    
    # Add memory section if exists
    if memory_section:
        system_instruction = system_instruction.replace("</SYS>>", f"</SYS>>\n{memory_section}")
    
    return system_instruction

# ====== ASYNC AI MODEL CALL ======
async def ask_model_async(prompt: str) -> str:
    """Async call to HuggingFace API"""
    try:
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 300,
                "temperature": 1.0,
                "top_p": 0.9,
                "repetition_penalty": 1.2,
                "do_sample": True,
                "return_full_text": False
            }
        }
        
        response = await async_client.post(MODEL_URL, json=payload, timeout=30.0)
        
        if response.status_code != 200:
            if response.status_code == 503:
                return "මට මේ මොහොතේ හිතාගන්න බෑ... මචන් 🫤 (model loading)"
            elif response.status_code == 429:
                return "හරිම busy වෙලා... ටිකක් පස්සෙ ආයෙ කියන්න 😊"
            else:
                return f"මට හිතාගන්න බෑ (error {response.status_code}) 🫤"
        
        data = response.json()
        
        if isinstance(data, list) and len(data) > 0:
            if "generated_text" in data[0]:
                return data[0]["generated_text"].strip()
            elif "text" in data[0]:
                return data[0]["text"].strip()
        
        # Try alternative response format
        if isinstance(data, dict) and "generated_text" in data:
            return data["generated_text"].strip()
        
        # Fallback response
        return "හ්ම්ම්... මොකක් හරි වැරැද්දක් 😕"
        
    except httpx.TimeoutException:
        return "මට මේ මොහොතේ හිතාගන්න බෑ... ටිකක් සල්ලි ද? 🕐"
    except Exception as e:
        print(f"⚠️ Model error: {e}")
        return "අද මගේ හිත අවුල්... 😔"

# ====== CREDIT SYSTEM ======
def check_and_use_credit(mem: Dict, amount: int = 1, developer: bool = False) -> bool:
    """Check and deduct credits"""
    if developer:
        return True
    
    now = time.time()
    credits = mem.get("credits", {"daily": 200, "last_reset": now})
    
    # Daily reset
    if now - credits.get("last_reset", 0) >= 86400:
        credits["daily"] = 200
        credits["last_reset"] = now
    
    if credits["daily"] >= amount:
        credits["daily"] -= amount
        mem["credits"] = credits
        return True
    
    return False

# ====== STATISTICS FUNCTIONS ======
def get_all_user_stats() -> Dict:
    """Get statistics about all users (for developer)"""
    memory_dir = "memory/users"
    stats = {
        "total_users": 0,
        "active_today": 0,
        "total_messages": 0,
        "stage_distribution": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
        "memory_usage_mb": 0
    }
    
    if not os.path.exists(memory_dir):
        return stats
    
    today = time.time() - 86400
    
    for filename in os.listdir(memory_dir):
        if filename.endswith(".json") and not filename.endswith("_vocabulary.json"):
            filepath = os.path.join(memory_dir, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                stats["total_users"] += 1
                stats["total_messages"] += len(data.get("conversation", []))
                
                # Check if active today
                last_active = data.get("last_active", 0)
                if last_active > today:
                    stats["active_today"] += 1
                
                # Track stage distribution
                stage = data.get("stage", 1)
                stats["stage_distribution"][stage] = stats["stage_distribution"].get(stage, 0) + 1
                
                # Calculate file size
                stats["memory_usage_mb"] += os.path.getsize(filepath) / (1024 * 1024)
                
            except Exception as e:
                print(f"⚠️ Error reading stats from {filename}: {e}")
    
    stats["memory_usage_mb"] = round(stats["memory_usage_mb"], 2)
    return stats

def cleanup_old_memory_files(days_old: int = 30):
    """Clean up memory files for inactive users"""
    memory_dir = "memory/users"
    if not os.path.exists(memory_dir):
        return
    
    cutoff_time = time.time() - (days_old * 86400)
    deleted_count = 0
    
    for filename in os.listdir(memory_dir):
        if filename.endswith(".json") and not filename.endswith("_vocabulary.json"):
            filepath = os.path.join(memory_dir, filename)
            try:
                # Check if file is old enough
                file_mtime = os.path.getmtime(filepath)
                if file_mtime < cutoff_time:
                    # Load file to check last active
                    with open(filepath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    
                    last_active = data.get("last_active", file_mtime)
                    if last_active < cutoff_time:
                        # Archive old file instead of deleting
                        archive_dir = "memory/archived"
                        os.makedirs(archive_dir, exist_ok=True)
                        archive_path = os.path.join(archive_dir, f"{filename}.{int(time.time())}")
                        os.rename(filepath, archive_path)
                        deleted_count += 1
                        
            except Exception as e:
                print(f"⚠️ Error checking file {filename}: {e}")
    
    if deleted_count > 0:
        print(f"🧹 Cleaned up {deleted_count} old memory files")

async def export_all_memory_zip():
    """Export all user memories as a ZIP file"""
    import zipfile
    from io import BytesIO
    
    memory_dir = "memory/users"
    if not os.path.exists(memory_dir):
        return None
    
    zip_buffer = BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for filename in os.listdir(memory_dir):
            if filename.endswith(".json") and not filename.endswith("_vocabulary.json"):
                filepath = os.path.join(memory_dir, filename)
                try:
                    zip_file.write(filepath, f"memories/{filename}")
                except Exception as e:
                    print(f"⚠️ Error adding {filename} to zip: {e}")
        
        # Add summary file
        stats = get_all_user_stats()
        stats_file = f"summary_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        zip_file.writestr(stats_file, json.dumps(stats, indent=2, ensure_ascii=False))
    
    zip_buffer.seek(0)
    return zip_buffer.read()

# ====== ASYNC MESSAGE HANDLER ======
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming Telegram messages asynchronously"""
    if not TELEGRAM_TOKEN or not HF_API_KEY:
        await update.message.reply_text("Bot සකසනය නොමැත 💔")
        return
    
    if not update.message or not update.message.text:
        return
    
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    # Load user's memory
    mem = load_user_memory(user_id)
    developer_mode = context.bot_data.get("dev_unlocked", False)
    
    # Initialize vocabulary learner
    vocab_learner = VocabularyLearner(user_id)
    
    # Developer unlock - NOW FROM .env
    if text == DEVELOPER_PASSWORD:
        context.bot_data["dev_unlocked"] = True
        await update.message.reply_text("🔓 Developer mode unlocked!")
        return
    
    # Export all memories as ZIP (developer only)
    if text == "/export_all_memory" and developer_mode:
        await update.message.reply_text("📦 Creating memory archive...")
        zip_data = await export_all_memory_zip()
        if zip_data:
            await update.message.reply_document(
                document=zip_data,
                filename=f"all_memories_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                caption=f"Total users: {get_all_user_stats()['total_users']}"
            )
        else:
            await update.message.reply_text("No memories found to export")
        return
    
    # Get stats (developer only)
    if text == "/stats" and developer_mode:
        stats = get_all_user_stats()
        stats_text = f"""
📊 Bot Statistics:
• Total Users: {stats['total_users']}
• Active Today: {stats['active_today']}
• Total Messages: {stats['total_messages']}
• Memory Usage: {stats['memory_usage_mb']} MB

Stage Distribution:
"""
        for stage, count in stats['stage_distribution'].items():
            stats_text += f"  Stage {stage}: {count} users\n"
        
        await update.message.reply_text(stats_text)
        return
    
    # Cleanup command (developer only)
    if text == "/cleanup_memory" and developer_mode:
        await update.message.reply_text("🧹 Cleaning up old memory files...")
        cleanup_old_memory_files(30)
        stats = get_all_user_stats()
        await update.message.reply_text(f"✅ Cleanup complete. Total users: {stats['total_users']}")
        return
    
    # Set stage (developer only)
    if text.startswith("/set_stage "):
        if developer_mode:
            try:
                parts = text.split()
                if len(parts) >= 2:
                    new_stage = int(parts[1])
                    if 1 <= new_stage <= 5:
                        mem["stage"] = new_stage
                        save_user_memory(user_id, mem)
                        await update.message.reply_text(f"✅ Stage updated to {new_stage}")
                    else:
                        await update.message.reply_text("❌ Stage must be 1-5")
                else:
                    await update.message.reply_text("Usage: /set_stage <1-5>")
            except ValueError:
                await update.message.reply_text("❌ Invalid number")
        else:
            await update.message.reply_text("⚠️ Developer access required")
        return
    
    # Check memory commands FIRST
    memory_response = handle_memory_commands(user_id, text)
    if memory_response:
        await update.message.reply_text(memory_response)
        return
    
    # Vocabulary profile command
    if "මගේ vocabulary" in text.lower() or "මගේ වචන" in text.lower():
        # Learn from current message first
        vocab_learner.analyze_user_vocabulary(text)
        vocab_summary = vocab_learner.get_user_vocabulary_summary()
        await update.message.reply_text(vocab_summary)
        return
    
    # Clear chat
    if text == "/clear":
        # Only clear conversation, keep long-term memory
        mem["conversation"] = []
        save_user_memory(user_id, mem)
        await update.message.reply_text("හරි… ඔබේ chat history clear වුනා 🙂\n(වැදගත් මතකයන් ආරක්ෂිතයි! 🔒)")
        return
    
    # Credits check
    if "credits" in text.lower() or "credit" in text.lower():
        credits_left = mem.get("credits", {}).get("daily", 0)
        await update.message.reply_text(f"ඔබට ඉතුරු තියෙන්නේ {credits_left} credits! 😊")
        return
    
    # Help command
    if text == "/help" or text == "help" or text == "උදව්":
        help_text = """
Available Commands:
• /clear - Clear chat history
• මතකද? - Check if I remember something
• මට ගැන මතක තියෙනවද? - See what I remember about you
• සමාවෙන්න - Apologize (calms anger)
• credits - Check your remaining credits
• මාව හිතවත්ද? - Ask if I care about you

Just chat normally! I'll remember important things about you. 😊
        """
        await update.message.reply_text(help_text)
        return
    
    # Check credits
    if not check_and_use_credit(mem, amount=1, developer=developer_mode):
        await update.message.reply_text("⚠️ Daily credit limit අරිනවා, පැය 1 කට පසුව නැවත උත්සාහ කරන්න")
        return
    
    try:
        # Analyze user behavior
        user_behavior = analyze_user_behavior(text, mem.get("conversation", []))
        
        # Learn vocabulary from user
        vocab_learner.analyze_user_vocabulary(text)
        
        # Update user affection history
        affection_history = mem.get("user_affection_history", [])
        affection_history.append(user_behavior["affectionate_level"])
        if len(affection_history) > 10:
            affection_history = affection_history[-10:]
        mem["user_affection_history"] = affection_history
        
        # Extract important information for long-term memory
        extracted_info = extract_important_info(text)
        if extracted_info:
            ltm = update_long_term_memory(user_id, extracted_info)
            print(f"💾 Saved {len(extracted_info)} pieces of info to long-term memory")
        
        # NATURAL love progression
        mem["love_score"] = update_love_score(mem, text, user_behavior)
        
        # Update stage
        stage_changed = update_stage(mem)
        
        # Update jealousy and mood
        update_jealousy_and_mood(mem, text, user_behavior)
        
        # Get emotional state
        emotional_state = get_emotional_state(mem, text)
        
        # Check if user is trying to reconcile
        if user_behavior["is_apologizing"] and mem["jealousy"] > 5:
            recon_response = reconciliation_response(mem["jealousy"], mem["love_score"])
            if recon_response and random.random() > 0.5:
                await update.message.reply_text(recon_response)
        
        # Build prompt with vocabulary adaptation
        prompt = build_mistral_prompt(text, mem, emotional_state)
        
        # Enhance with vocabulary learning
        prompt = vocab_learner.adapt_prompt_with_vocabulary(prompt)
        
        # Get AI response
        reply = await ask_model_async(prompt)
        
        # Add emotional modifier
        if emotional_state["response_modifier"]:
            reply += emotional_state["response_modifier"]
        
        # Add stage-appropriate emojis
        stage = mem.get("stage", 1)
        if stage >= 3 and mem["love_score"] > 40 and user_behavior["affectionate_level"] > 0:
            if random.random() < 0.4:
                affectionate_emojis = [" 🥰", " 💖", " 😊"]
                reply += random.choice(affectionate_emojis)
        
        # Add sadness if mood is sad
        if mem.get("mood") == "sad" and random.random() < 0.5:
            sad_emojis = [" 😢", " 💔", " 🥺"]
            reply += random.choice(sad_emojis)
        
        # Save conversation
        mem["conversation"].append({
            "user": text,
            "bot": reply,
            "time": datetime.datetime.now().isoformat(),
            "love_score": mem["love_score"],
            "jealousy": mem["jealousy"],
            "stage": mem["stage"],
            "mood": mem.get("mood", "neutral"),
            "memory_relevant": len(extracted_info) > 0 if 'extracted_info' in locals() else False
        })
        
        # Trim conversation history
        if len(mem["conversation"]) > 50:
            mem["conversation"] = mem["conversation"][-50:]
        
        save_user_memory(user_id, mem)
        
        await update.message.reply_text(reply)
        
    except Exception as e:
        print(f"⚠️ Handler error for user {user_id}: {e}")
        traceback.print_exc()
        await update.message.reply_text("අයියෝ… මට මේ මොහොතේ හිතාගන්න බෑ 😥\nටිකක් පසුව ආයෙ කියන්නද?")

# ====== MAIN BOT START ======
async def main():
    """Start the Telegram bot"""
    if not TELEGRAM_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN not found in .env")
        return
    
    if not HF_API_KEY:
        print("❌ HF_API_KEY not found in .env")
        return
    
    if not DEVELOPER_PASSWORD:
        print("⚠️ DEVELOPER_PASSWORD not set in .env")
    
    bot_name = BOT_CONFIG.get("bot_name", "සමාලි")
    print(f"🤖 {bot_name} bot starting...")
    print("⚡ Auto-creating directories...")
    print("🔒 Password from .env file")
    print("🎭 Mistral-7B-Instruct format with [INST] tags")
    print("💖 Natural affection system")
    print("🧠 Long-term memory + Vocabulary learning")
    
    try:
        app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # Start bot
        await app.initialize()
        await app.start()
        print("✅ Bot started successfully!")
        await app.updater.start_polling()
        
        # Keep running
        await asyncio.Event().wait()
        
    except Exception as e:
        print(f"❌ Failed to start bot: {e}")
        traceback.print_exc()
    finally:
        # Cleanup
        await async_client.aclose()
        if 'app' in locals():
            await app.stop()

if __name__ == "__main__":
    asyncio.run(main())
