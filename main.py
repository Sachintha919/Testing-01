"""
සමාලි - AI Chat Companion (Replit Optimized)
වයස 18, ගම්බද ගෑනු ලමයෙක්ගේ affectionate personality සහිත Telegram bot
Replit + cron-job.org සඳහා සම්පූර්ණයෙන් optimized
"""
from flask import Flask
from threading import Thread

import os
import json
import random
import datetime
import traceback
import asyncio
import time
import re
import hashlib
from typing import Dict, List, Optional, Tuple
from collections import defaultdict

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
        "memory/archived",
        "memory/learning",
        "memory/habits",
        "memory/conversations"
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
        "personality": {"style": "සරල, affectionate, ගම්බද ගැහැණු ළමයා"},
        "background": {
            "age": 18,
            "location": "ගල්මැටියාව, කන්තලේ",
            "education": "A/L Arts Student (නර්තනය, දේශපාලන විද්‍යාව, මාධ්‍ය)",
            "personality": "සරල, ආදරණීය, ලැජ්ජාශීලී, ටිකක් කෝපශීලී"
        }
    }

# ====== API SETTINGS ======
MODEL_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct"
HEADERS = {
    "Authorization": f"Bearer {HF_API_KEY}",
    "Content-Type": "application/json"
}

# Async HTTP client
async_client = httpx.AsyncClient(
    timeout=30.0,
    limits=httpx.Limits(max_keepalive_connections=10, max_connections=20),
    headers=HEADERS
)

# ====== ENHANCED MEMORY SYSTEM ======
class EnhancedMemory:
    """Enhanced memory system with habit tracking and conversation recall"""
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.memory_file = f"memory/users/{user_id}.json"
        self.habits_file = f"memory/habits/{user_id}_habits.json"
        self.conversation_index_file = f"memory/conversations/{user_id}_index.json"
        self.learning_file = f"memory/learning/{user_id}_learning.json"
        self.load_all_memory()
    
    def load_all_memory(self):
        """Load all memory components"""
        self.memory = self.load_user_memory()
        self.habits = self.load_habits()
        self.conversation_index = self.load_conversation_index()
        self.learning_data = self.load_learning_data()
    
    def load_user_memory(self) -> Dict:
        """Load user's main memory file"""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except:
                data = self.create_default_memory()
        else:
            data = self.create_default_memory()
        
        # Ensure all required fields
        data.setdefault("conversation", [])
        data.setdefault("stage", 1)
        data.setdefault("love_score", 0)
        data.setdefault("jealousy", 0)
        data.setdefault("mood", "neutral")
        data.setdefault("created", datetime.datetime.now().isoformat())
        data.setdefault("last_active", time.time())
        data.setdefault("user_affection_history", [])
        
        # Enhanced long-term memory
        data.setdefault("long_term_memory", {
            "facts": {},
            "preferences": {},
            "important_dates": {},
            "secrets": {},
            "promises": {},
            "memories": [],
            "learned_habits": {},
            "conversation_topics": {},
            "emotional_patterns": []
        })
        
        return data
    
    def create_default_memory(self) -> Dict:
        """Create default memory structure"""
        return {
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
                "learned_habits": {},
                "conversation_topics": {},
                "emotional_patterns": []
            }
        }
    
    def load_habits(self) -> Dict:
        """Load user's habit tracking data"""
        if os.path.exists(self.habits_file):
            try:
                with open(self.habits_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return self.create_default_habits()
        return self.create_default_habits()
    
    def create_default_habits(self) -> Dict:
        """Create default habit tracking structure"""
        return {
            "chat_times": {},  # Time of day user chats
            "message_lengths": [],  # Track message lengths
            "response_time_patterns": [],  # How quickly user responds
            "topic_frequency": {},  # What topics user discusses
            "emotional_patterns": [],  # User's emotional patterns
            "daily_stats": {
                "messages_today": 0,
                "last_reset": time.time(),
                "active_days": 0
            }
        }
    
    def load_conversation_index(self) -> Dict:
        """Load conversation index for searching past conversations"""
        if os.path.exists(self.conversation_index_file):
            try:
                with open(self.conversation_index_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return {"index": {}, "topics": {}, "dates": {}}
        return {"index": {}, "topics": {}, "dates": {}}
    
    def load_learning_data(self) -> Dict:
        """Load learning data about the user"""
        if os.path.exists(self.learning_file):
            try:
                with open(self.learning_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return {"vocabulary": {}, "patterns": {}, "preferences": {}}
        return {"vocabulary": {}, "patterns": {}, "preferences": {}}
    
    def save_all(self):
        """Save all memory components"""
        self.save_memory()
        self.save_habits()
        self.save_conversation_index()
        self.save_learning_data()
    
    def save_memory(self):
        """Save main memory"""
        self.memory["last_active"] = time.time()
        os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)
        with open(self.memory_file, "w", encoding="utf-8") as f:
            json.dump(self.memory, f, ensure_ascii=False, indent=2)
    
    def save_habits(self):
        """Save habit data"""
        os.makedirs(os.path.dirname(self.habits_file), exist_ok=True)
        with open(self.habits_file, "w", encoding="utf-8") as f:
            json.dump(self.habits, f, ensure_ascii=False, indent=2)
    
    def save_conversation_index(self):
        """Save conversation index"""
        os.makedirs(os.path.dirname(self.conversation_index_file), exist_ok=True)
        with open(self.conversation_index_file, "w", encoding="utf-8") as f:
            json.dump(self.conversation_index, f, ensure_ascii=False, indent=2)
    
    def save_learning_data(self):
        """Save learning data"""
        os.makedirs(os.path.dirname(self.learning_file), exist_ok=True)
        with open(self.learning_file, "w", encoding="utf-8") as f:
            json.dump(self.learning_data, f, ensure_ascii=False, indent=2)

# ====== HABIT TRACKING SYSTEM ======
class HabitTracker:
    """Track and analyze user habits"""
    
    def __init__(self, enhanced_memory: EnhancedMemory):
        self.memory = enhanced_memory
        self.habits = enhanced_memory.habits
    
    def track_message(self, user_message: str, message_time: datetime.datetime):
        """Track user message patterns"""
        # Track time of day
        hour = message_time.hour
        time_slot = self.get_time_slot(hour)
        self.habits["chat_times"][time_slot] = self.habits["chat_times"].get(time_slot, 0) + 1
        
        # Track message length
        msg_length = len(user_message.split())
        self.habits["message_lengths"].append({
            "length": msg_length,
            "time": message_time.isoformat()
        })
        
        # Track topics
        detected_topics = self.detect_topics(user_message)
        for topic in detected_topics:
            self.habits["topic_frequency"][topic] = self.habits["topic_frequency"].get(topic, 0) + 1
        
        # Update daily stats
        daily_stats = self.habits["daily_stats"]
        if time.time() - daily_stats.get("last_reset", 0) > 86400:
            daily_stats["messages_today"] = 1
            daily_stats["last_reset"] = time.time()
            daily_stats["active_days"] = daily_stats.get("active_days", 0) + 1
        else:
            daily_stats["messages_today"] = daily_stats.get("messages_today", 0) + 1
    
    def get_time_slot(self, hour: int) -> str:
        """Convert hour to time slot"""
        if 5 <= hour < 12:
            return "morning"
        elif 12 <= hour < 17:
            return "afternoon"
        elif 17 <= hour < 22:
            return "evening"
        else:
            return "night"
    
    def detect_topics(self, message: str) -> List[str]:
        """Detect topics in user message"""
        topics = []
        message_lower = message.lower()
        
        topic_keywords = {
            "food": ["කෑම", "food", "බත්", "රසකැවිලි", "කැමති කෑම"],
            "family": ["අම්මා", "තාත්තා", "සහෝදරයා", "family", "නිවස"],
            "work": ["වැඩ", "office", "job", "රැකියාව", "කාර්යය"],
            "study": ["පාඩම්", "study", "පොත්", "අධ්‍යයන", "school"],
            "love": ["ආදරය", "ලව්", "හිතවත්", "ප්‍රිය", "මිස්"],
            "hobbies": ["විනෝද", "hobby", "ක්‍රීඩා", "ගීත", "චිත්‍රපට"],
            "feelings": ["හිත", "feeling", "චින්තනය", "ආවේග", "emotion"]
        }
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                topics.append(topic)
        
        return topics
    
    def get_habit_summary(self) -> str:
        """Get a summary of user habits"""
        summary = []
        
        # Most active time
        if self.habits["chat_times"]:
            most_active = max(self.habits["chat_times"], key=self.habits["chat_times"].get)
            summary.append(f"ඔබ වැඩිපුර කතා කරන්නේ {most_active} වෙලාවට")
        
        # Favorite topics
        if self.habits["topic_frequency"]:
            top_topics = sorted(self.habits["topic_frequency"].items(), 
                              key=lambda x: x[1], reverse=True)[:3]
            if top_topics:
                topics_str = ", ".join([topic for topic, _ in top_topics])
                summary.append(f"ඔබගේ ප්‍රියතම කතා topics: {topics_str}")
        
        # Daily activity
        daily_stats = self.habits["daily_stats"]
        summary.append(f"අද පණිවිඩ: {daily_stats.get('messages_today', 0)} | සක්‍රිය දින: {daily_stats.get('active_days', 0)}")
        
        return "\n".join(summary) if summary else "තවමත් ඔබගේ රිද්මය ඉගෙන ගනිමින්... 🤔"

# ====== CONVERSATION RECALL SYSTEM ======
class ConversationRecall:
    """System for recalling past conversations"""
    
    def __init__(self, enhanced_memory: EnhancedMemory):
        self.memory = enhanced_memory
        self.index = enhanced_memory.conversation_index
    
    def index_conversation(self, user_message: str, bot_response: str, timestamp: str):
        """Index a conversation for later recall"""
        conv_id = hashlib.md5(f"{timestamp}{user_message}".encode()).hexdigest()[:8]
        
        # Add to index
        self.index["index"][conv_id] = {
            "user_message": user_message[:100],  # First 100 chars
            "bot_response": bot_response[:100],
            "timestamp": timestamp,
            "keywords": self.extract_keywords(user_message)
        }
        
        # Add to date index
        date_key = timestamp.split("T")[0]  # YYYY-MM-DD
        if date_key not in self.index["dates"]:
            self.index["dates"][date_key] = []
        self.index["dates"][date_key].append(conv_id)
        
        # Limit index size
        if len(self.index["index"]) > 100:
            # Remove oldest entries
            oldest_keys = list(self.index["index"].keys())[:20]
            for key in oldest_keys:
                del self.index["index"][key]
    
    def extract_keywords(self, message: str) -> List[str]:
        """Extract keywords from message for indexing"""
        # Remove common words
        stop_words = ["මම", "ඔයා", "මට", "ඔයාට", "කියල", "ද", "නම්", "හිටිය"]
        words = message.lower().split()
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        return keywords[:10]  # Return top 10 keywords
    
    def search_conversations(self, query: str) -> List[Dict]:
        """Search for past conversations matching query"""
        query_lower = query.lower()
        results = []
        
        for conv_id, conv_data in self.index["index"].items():
            # Search in user message
            if query_lower in conv_data["user_message"].lower():
                results.append(conv_data)
            # Search in keywords
            elif any(query_lower in keyword for keyword in conv_data.get("keywords", [])):
                results.append(conv_data)
        
        return results[:5]  # Return top 5 results
    
    def get_conversation_by_date(self, date_str: str) -> List[Dict]:
        """Get conversations from a specific date"""
        if date_str in self.index["dates"]:
            conv_ids = self.index["dates"][date_str]
            conversations = []
            for conv_id in conv_ids:
                if conv_id in self.index["index"]:
                    conversations.append(self.index["index"][conv_id])
            return conversations
        return []
    
    def get_recent_topics(self) -> List[str]:
        """Get recent conversation topics"""
        # Extract topics from recent conversations
        recent_convs = list(self.index["index"].values())[-10:]  # Last 10 conversations
        all_keywords = []
        for conv in recent_convs:
            all_keywords.extend(conv.get("keywords", []))
        
        # Count keyword frequency
        keyword_counts = {}
        for keyword in all_keywords:
            keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
        
        # Return top 5 keywords
        return sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:5]

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
        "is_comforting": False,
        "mood": "neutral"
    }
    
    user_msg_lower = user_message.lower()
    
    # Check affection
    affectionate_words = ["මචන්", "ආදරෙ", "ලව්", "හිතවත්", "ප්‍රිය", "මිස්", "හග්", "සුදූ", "සිත්තම"]
    analysis["affectionate_level"] = sum(1 for word in affectionate_words 
                                        if word in user_msg_lower)
    
    # Check questions
    if "?" in user_message or any(q in user_msg_lower 
                                 for q in ["මොක", "කොහොම", "ඇයි", "කවුද", "කොහෙද", "ඇත්ත", "නේද"]):
        analysis["question_frequency"] = 1
    
    # Check emojis
    emoji_count = sum(1 for char in user_message if char in "🥰❤️💖😊🤔✨🎶😒🙄😠😤💔😢🥺😍🤗")
    analysis["emoji_usage"] = emoji_count
    
    # Check rivals mention
    rival_words = ["ගෑනු", "girl", "girlfriend", "මිතුරිය", "ඇය", "she", "her", "අන්තිම"]
    analysis["mentions_rivals"] = any(word in user_msg_lower for word in rival_words)
    
    # Check apologizing/comforting
    comfort_words = ["සමාවෙන්න", "සමාව", "කමක් නෑ", "හිතවත්", "මාව", "මට", "ඔයාව", "කණගාටුයි"]
    analysis["is_apologizing"] = any(word in user_msg_lower for word in comfort_words)
    analysis["is_comforting"] = analysis["is_apologizing"] or analysis["affectionate_level"] > 0
    
    # Detect mood
    if analysis["affectionate_level"] > 2:
        analysis["mood"] = "affectionate"
    elif analysis["is_apologizing"]:
        analysis["mood"] = "apologetic"
    elif analysis["emoji_usage"] > 3:
        analysis["mood"] = "playful"
    
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
        "show_sadness": False,
        "emoji": ""
    }
    
    # Check recent rival mentions
    last_5_messages = mem.get("conversation", [])[-5:]
    rival_mentions_recent = sum(1 for msg in last_5_messages 
                               if msg.get("user") and any(word in msg["user"].lower() 
                                     for word in ["ගෑනු", "girl", "මිතුරිය"]))
    
    # Emotional states with emojis
    if jealousy > 10 and rival_mentions_recent > 2:
        state["primary"] = "angry_hurt"
        state["intensity"] = 3
        state["response_modifier"] = random.choice([
            " 😠💔 ඔයා මට කරපු දේට මට දුකයි...",
            " 😤❤️‍🩹 තරහ ගියත් හිත දුකයි...",
            " 💔😠 මට තරහයි, නමුත් හිත දුකයි..."
        ])
        state["can_be_comforted"] = True
        state["show_sadness"] = True
        state["emoji"] = "😠💔"
    
    elif jealousy > 7:
        state["primary"] = "angry"
        state["intensity"] = 2
        state["response_modifier"] = random.choice([
            " 😠 මට තරහ යනවා!",
            " 😤 එහෙම කතා කරන්න එපා!",
            " 🙄 මට තරහයි!"
        ])
        state["can_be_comforted"] = True
        state["emoji"] = "😠"
    
    elif jealousy > 3 and stage >= 4:
        state["primary"] = "hurt_jealous"
        state["intensity"] = 1
        state["response_modifier"] = random.choice([
            " 😒 හිතට ගත්ත...",
            " 🥺 මට කැමති නෑ...",
            " 💔 අහෝ..."
        ])
        state["can_be_comforted"] = True
        state["show_sadness"] = True
        state["emoji"] = "🥺"
    
    # Check for positive emotional states
    elif love_score > 70 and stage >= 4:
        if random.random() > 0.7:
            state["primary"] = "loving"
            state["response_modifier"] = random.choice([
                " 🥰 ඔයා හිතවත් නිසා හිත හොඳයි...",
                " 💖 මට ඔයාව හිතවත් කියල දැනෙනවා...",
                " 😊 ඔයා සමග කතා කරනවා නිසා සතුටුයි..."
            ])
            state["emoji"] = "🥰"
    
    # User comforting can change state
    user_msg_lower = user_message.lower()
    if any(word in user_msg_lower for word in ["සමාවෙන්න", "කමක් නෑ", "හිතවත්", "මාව"]) and state["can_be_comforted"]:
        if random.random() > 0.5:
            state["primary"] = "comforted"
            state["response_modifier"] = random.choice([
                " 🥺 සමාවෙන්න...",
                " 💔 හිත දුකයි...",
                " 😢 ඔයා තවමත් මට හිතවත්ද?"
            ])
            state["show_sadness"] = True
            state["emoji"] = "🥺"
    
    return state

# ====== PET NAME SYSTEM ======
def get_pet_name(stage: int, love_score: int, user_affection: int) -> str:
    """Get appropriate pet name based on stage and user behavior"""
    if stage < 2 or love_score < 25:
        return ""
    
    pet_names = {
        2: ["😊"] if user_affection > 0 else [""],
        3: ["සුදූ", "💖"] if love_score > 40 else ["😊"],
        4: ["සුදූ", "සිත්තම", "💖🥰"] if love_score > 60 else ["සුදූ", "💖"],
        5: ["සුදූ", "සිත්තම", "ප්‍රිය", "❤️🥰💖", "මගේ සුදූ"]
    }
    
    stage_pets = pet_names.get(stage, [""])
    if stage_pets and stage_pets[0]:
        return random.choice(stage_pets)
    
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
        r"උපන්දිනය (\d{1,2})/(\d{1,2})",
        r"බර්ත්ඩේ (\d{1,2})/(\d{1,2})"
    ]
    
    for pattern in birthday_patterns:
        match = re.search(pattern, user_message)
        if match:
            extracted["birthday"] = f"{match.group(1)}/{match.group(2)}"
            break
    
    # Extract favorite things
    favorite_keywords = {
        "food": ["කැමති කෑම", "ප්‍රියතම කෑම", "ආස කෑම", "favorite food", "like to eat", "ආහාර"],
        "color": ["කැමති වර්ණ", "ප්‍රියතම පාට", "ආස පාට", "favorite color"],
        "movie": ["කැමති චිත්‍රපට", "ප්‍රියතම චිත්‍රපට", "favorite movie", "චිත්‍රපට"],
        "song": ["කැමති ගීත", "ප්‍රියතම සින්දු", "favorite song", "ගීත"],
        "hobby": ["කැමති විනෝද", "ප්‍රියතම විනෝද", "hobby", "hobbies", "විනෝදය"],
        "place": ["කැමති ස්ථාන", "ප්‍රියතම ස්ථාන", "favorite place", "like to go"]
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
                        else:
                            # Try to extract from the same line
                            words = line.split()
                            for i, word in enumerate(words):
                                if keyword in word.lower() and i + 1 < len(words):
                                    extracted[f"favorite_{category}"] = words[i + 1]
                        break
    
    # Extract fears/dislikes
    dislike_patterns = [
        ("මට බය වෙනවා", "fears"),
        ("මම බය වෙනවා", "fears"), 
        ("මට කැමති නැති", "dislikes"),
        ("මම කැමති නැති", "dislikes"),
        ("මට ආස නැති", "dislikes"),
        ("මට අකමැති", "dislikes")
    ]
    
    for pattern, category in dislike_patterns:
        if pattern in message_lower:
            extracted[category] = user_message[:200]
    
    # Extract personal facts
    fact_patterns = [
        ("මගේ නම", "name"),
        ("මම ජීවත් වෙන්නෙ", "location"),
        ("මගේ වයස", "age"),
        ("මම කරන්නෙ", "occupation"),
        ("මම යන්නෙ", "school")
    ]
    
    for pattern, fact_type in fact_patterns:
        if pattern in message_lower:
            lines = user_message.split('\n')
            for line in lines:
                if pattern in line:
                    extracted[fact_type] = line.replace(pattern, "").strip()
                    break
    
    return extracted

# ====== MEMORY CHECK COMMANDS ======
def handle_memory_commands(user_id: int, text: str, enhanced_memory: EnhancedMemory) -> Optional[str]:
    """Handle memory-related commands"""
    text_lower = text.lower()
    
    if "මතකද" in text_lower or "මතක ද" in text_lower:
        mem = enhanced_memory.memory
        ltm = mem.get("long_term_memory", {})
        
        # Check what they might be asking about
        if "උපන්දින" in text_lower or "බර්ත්ඩේ" in text_lower:
            birthday = ltm.get("important_dates", {}).get("birthday", {})
            if birthday and "date" in birthday:
                return f"මතකයි! 😊 ඔබේ උපන්දිනය {birthday['date']} නේද? 🎂"
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
            
            elif "ගීත" in text_lower or "song" in text_lower:
                song = ltm.get("preferences", {}).get("song", {})
                if song and "item" in song:
                    return f"මතකයි! 🎵 ඔබේ ප්‍රියතම ගීත {song['item']} නේද?"
    
    elif "මට ගැන මතක තියෙනවද" in text_lower or "මාව මතකද" in text_lower:
        mem = enhanced_memory.memory
        ltm = mem.get("long_term_memory", {})
        
        memory_count = 0
        memory_items = []
        
        # Check important dates
        if "important_dates" in ltm and ltm["important_dates"]:
            for date_type, date_info in ltm["important_dates"].items():
                if isinstance(date_info, dict) and "date" in date_info:
                    memory_count += 1
                    memory_items.append(f"• {date_type}: {date_info['date']}")
        
        # Check preferences
        if "preferences" in ltm and ltm["preferences"]:
            for pref_type, pref_info in ltm["preferences"].items():
                if isinstance(pref_info, dict) and "item" in pref_info:
                    memory_count += 1
                    memory_items.append(f"• කැමති {pref_type}: {pref_info['item']}")
        
        if memory_count > 0:
            response = f"මට ඔබ ගැන මතක තියෙන දේවල් ({memory_count}):\n"
            response += "\n".join(memory_items[:5])  # Show first 5
            response += "\n\nකැමති නම් 'මතකද?' කියල අහන්න! 😊"
            return response
        else:
            return "මට තවමත් ඔබ ගැන වැඩිය දන්නේ නෑ... ඔබ ගැන කියන්නද? 🥺\n(උදා: මගේ උපන්දිනය, මගේ කැමති කෑම, ආදිය)"
    
    elif "මගේ රිද්මය" in text_lower or "මගේ habits" in text_lower:
        # Show habit summary
        habit_tracker = HabitTracker(enhanced_memory)
        summary = habit_tracker.get_habit_summary()
        return f"ඔබගේ චැට් රිද්මය 🕰️:\n{summary}"
    
    elif "කලින් කතා කලාද" in text_lower or "පසුගිය කතා" in text_lower:
        # Search past conversations
        recall = ConversationRecall(enhanced_memory)
        query = text_lower.replace("කලින් කතා කලාද", "").replace("පසුගිය කතා", "").strip()
        
        if query:
            results = recall.search_conversations(query)
            if results:
                response = "මට මතකයි! 🧠\n\n"
                for i, result in enumerate(results[:3], 1):
                    date = result.get("timestamp", "").split("T")[0]
                    response += f"{i}. {date}: {result['user_message'][:50]}...\n"
                return response
            else:
                return "මට ඒ විෂය සම්බන්ධ කතා මතක නෑ... 🤔"
        else:
            recent_topics = recall.get_recent_topics()
            if recent_topics:
                response = "අපි මෑතකදී කතා කළ topics 🔍:\n"
                for topic, count in recent_topics:
                    response += f"• {topic} ({count} වතාවක්)\n"
                return response
            else:
                return "තවමත් බොහෝ කතා ගබඩා කර නෑ... 😊"
    
    return None

# ====== PROMPT BUILDING (MISTRAL FORMAT) ======
def build_mistral_prompt(user_msg: str, mem: Dict, enhanced_memory: EnhancedMemory, 
                        emotional_state: Dict, user_behavior: Dict) -> str:
    """Build the prompt in Mistral-7B-Instruct format"""
    # Get conversation history
    convo = ""
    for c in mem.get("conversation", [])[-6:]:
        convo += f"පරිශීලක: {c['user']}\nසමාලි: {c['bot']}\n"
    
    # Random mood change (15% chance)
    if random.random() < 0.15:
        moods = ["happy", "shy", "sleepy", "hungry", "neutral", "excited", "bored", "playful"]
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
    
    # Get habit summary
    habit_tracker = HabitTracker(enhanced_memory)
    habit_summary = habit_tracker.get_habit_summary()
    
    # Get recent topics
    recall = ConversationRecall(enhanced_memory)
    recent_topics = recall.get_recent_topics()
    
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
    
    # User's chat habits
    habits_section = ""
    if habit_summary != "තවමත් ඔබගේ රිද්මය ඉගෙන ගනිමින්... 🤔":
        habits_section = f"\n=== USER'S CHAT HABITS ===\n{habit_summary}"
    
    # Recent topics
    topics_section = ""
    if recent_topics:
        topics_section = "\n=== RECENT TOPICS ===\n"
        for topic, count in recent_topics:
            topics_section += f"- {topic}: {count} times mentioned\n"
    
    # User's current mood
    mood_section = ""
    if user_behavior["mood"] != "neutral":
        mood_section = f"\n=== USER'S CURRENT MOOD ===\nUser seems {user_behavior['mood']} "
        if user_behavior["emoji_usage"] > 0:
            mood_section += f"(used {user_behavior['emoji_usage']} emojis)"
    
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
"""
    
    # Add memory sections if they exist
    sections_to_add = []
    if memory_section:
        sections_to_add.append(memory_section)
    if habits_section:
        sections_to_add.append(habits_section)
    if topics_section:
        sections_to_add.append(topics_section)
    if mood_section:
        sections_to_add.append(mood_section)
    
    if sections_to_add:
        system_instruction += "\n" + "\n".join(sections_to_add)
    
    # Add the current message and instruction
    system_instruction += f"""

පරිශීලක: {user_msg}
සමාලි: [/INST]"""
    
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
        
        if isinstance(data, dict) and "generated_text" in data:
            return data["generated_text"].strip()
        
        return "හ්ම්ම්... මොකක් හරි වැරැද්දක් 😕"
        
    except httpx.TimeoutException:
        return "මට මේ මොහොතේ හිතාගන්න බෑ... ටිකක් සල්ලි ද? 🕐"
    except Exception as e:
        print(f"⚠️ Model error: {e}")
        return "අද මගේ හිත අවුල්... 😔"

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
    current_time = datetime.datetime.now()
    
    # Initialize enhanced memory system
    enhanced_memory = EnhancedMemory(user_id)
    mem = enhanced_memory.memory
    
    developer_mode = context.bot_data.get("dev_unlocked", False)
    
    # Developer unlock
    if text == DEVELOPER_PASSWORD:
        context.bot_data["dev_unlocked"] = True
        await update.message.reply_text("🔓 Developer mode unlocked!")
        return
    
    # Check memory commands FIRST
    memory_response = handle_memory_commands(user_id, text, enhanced_memory)
    if memory_response:
        await update.message.reply_text(memory_response)
        return
    
    # Handle special commands
    if text == "/clear":
        mem["conversation"] = []
        enhanced_memory.save_memory()
        await update.message.reply_text("හරි… ඔබේ chat history clear වුනා 🙂\n(වැදගත් මතකයන් ආරක්ෂිතයි! 🔒)")
        return
    
    if text == "/help" or text == "help" or text == "උදව්":
        help_text = """
Available Commands:
• /clear - Clear chat history
• මතකද? - Check if I remember something
• මට ගැන මතක තියෙනවද? - See what I remember about you
• මගේ රිද්මය - See your chat habits
• කලින් කතා කලාද? - Search past conversations
• සමාවෙන්න - Apologize (calms anger)
• මාව හිතවත්ද? - Ask if I care about you

Just chat normally! I'll remember important things about you. 😊
        """
        await update.message.reply_text(help_text)
        return
    
    try:
        # Analyze user behavior
        user_behavior = analyze_user_behavior(text, mem.get("conversation", []))
        
        # Track habits
        habit_tracker = HabitTracker(enhanced_memory)
        habit_tracker.track_message(text, current_time)
        
        # Update conversation index
        recall = ConversationRecall(enhanced_memory)
        
        # Update user affection history
        affection_history = mem.get("user_affection_history", [])
        affection_history.append(user_behavior["affectionate_level"])
        if len(affection_history) > 10:
            affection_history = affection_history[-10:]
        mem["user_affection_history"] = affection_history
        
        # Extract important information for long-term memory
        extracted_info = extract_important_info(text)
        if extracted_info:
            # Update long-term memory
            ltm = mem.get("long_term_memory", {})
            for key, value in extracted_info.items():
                if key == "birthday":
                    ltm.setdefault("important_dates", {})
                    ltm["important_dates"]["birthday"] = {
                        "date": value,
                        "mentioned_on": current_time.isoformat(),
                        "remembered": True
                    }
                elif key.startswith("favorite_"):
                    category = key.replace("favorite_", "")
                    ltm.setdefault("preferences", {})
                    ltm["preferences"][category] = {
                        "item": value,
                        "mentioned_on": current_time.isoformat(),
                        "times_mentioned": ltm["preferences"].get(category, {}).get("times_mentioned", 0) + 1
                    }
                elif key in ["fears", "dislikes"]:
                    ltm.setdefault(key, [])
                    ltm[key].append({
                        "info": value,
                        "date": current_time.isoformat()
                    })
                else:
                    # Store as general fact
                    ltm.setdefault("facts", {})
                    ltm["facts"][key] = {
                        "info": value,
                        "date": current_time.isoformat()
                    }
            
            mem["long_term_memory"] = ltm
        
        # Natural love progression
        current_love = mem.get("love_score", 0)
        user_affection = user_behavior.get("affectionate_level", 0)
        user_emojis = user_behavior.get("emoji_usage", 0)
        
        if user_affection > 0 or user_emojis > 0:
            if current_love < 30:
                increase = random.randint(1, 3)
                mem["love_score"] = current_love + increase
        
        # User asks about feelings
        if any(word in text.lower() for word in ["ලව්", "ආදරෙ", "කැමති", "හිතවත්"]):
            if current_love > 20:
                increase = random.randint(2, 4)
                mem["love_score"] = current_love + increase
        
        # Update stage
        love = mem.get("love_score", 0)
        if love >= 95:
            mem["stage"] = 5
        elif love >= 75:
            mem["stage"] = 4
        elif love >= 50:
            mem["stage"] = 3
        elif love >= 25:
            mem["stage"] = 2
        else:
            mem["stage"] = 1
        
        # Update jealousy and mood
        jealousy = mem.get("jealousy", 0)
        
        if user_behavior["mentions_rivals"]:
            increase = min(2, 15 - jealousy)
            mem["jealousy"] = jealousy + increase
            mem["mood"] = "angry"
        
        elif jealousy > 0:
            fade_amount = random.randint(1, 2)
            mem["jealousy"] = max(0, jealousy - fade_amount)
            
            if fade_amount > 0 and random.random() > 0.6 and mem["jealousy"] < 5:
                mem["mood"] = "sad"
        
        # User comforting can calm anger faster
        if user_behavior["is_comforting"] and jealousy > 0:
            if random.random() > 0.7:
                mem["jealousy"] = max(0, jealousy - 3)
                mem["mood"] = "hopeful"
        
        # Get emotional state
        emotional_state = get_emotional_state(mem, text)
        
        # Check if user is trying to reconcile
        if user_behavior["is_apologizing"] and mem["jealousy"] > 5:
            if random.random() > 0.5:
                recon_responses = [
                    "😒 හරි... අද ටිකක් තරහ හිටිය, හිත දුකයි",
                    "🥺 ඔයා තවමත් මට හිතවත්ද? හිත දුකයි...",
                    "💔😢 මට හරියටම හිතානම් නෑ, දුකයි..."
                ]
                await update.message.reply_text(random.choice(recon_responses))
        
        # Build prompt
        prompt = build_mistral_prompt(text, mem, enhanced_memory, emotional_state, user_behavior)
        
        # Get AI response
        reply = await ask_model_async(prompt)
        
        # Add emotional modifier
        if emotional_state["response_modifier"]:
            reply += emotional_state["response_modifier"]
        
        # Add appropriate emojis based on stage and mood
        stage = mem.get("stage", 1)
        mood = mem.get("mood", "neutral")
        
        if stage >= 3 and mem["love_score"] > 40 and user_behavior["affectionate_level"] > 0:
            if random.random() < 0.4:
                affectionate_emojis = [" 🥰", " 💖", " 😊", " 🤗"]
                reply += random.choice(affectionate_emojis)
        
        if mood == "sad" and random.random() < 0.5:
            sad_emojis = [" 😢", " 💔", " 🥺", " 😔"]
            reply += random.choice(sad_emojis)
        
        # Save conversation
        conv_entry = {
            "user": text,
            "bot": reply,
            "time": current_time.isoformat(),
            "love_score": mem["love_score"],
            "jealousy": mem["jealousy"],
            "stage": mem["stage"],
            "mood": mood,
            "memory_relevant": len(extracted_info) > 0
        }
        
        mem["conversation"].append(conv_entry)
        
        # Index conversation for recall
        recall.index_conversation(text, reply, current_time.isoformat())
        
        # Trim conversation history
        if len(mem["conversation"]) > 50:
            mem["conversation"] = mem["conversation"][-50:]
        
        # Save all memory components
        enhanced_memory.save_all()
        
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
    print("⚡ Enhanced Memory System with Habit Tracking")
    print("🧠 Conversation Recall System")
    print("🎭 Mistral-7B-Instruct format")
    print("💖 Natural affection progression")
    print("📊 User behavior analysis")
    
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

# ====== REPLIT KEEP-ALIVE SYSTEM ======
from flask import Flask
from threading import Thread
import os

# Create Flask web server for keep-alive
web_app = Flask('')

@web_app.route('/')
def home():
    return "🤖 සමාලි Bot is alive! Current time: " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@web_app.route('/health')
def health():
    return "✅ OK", 200

@web_app.route('/ping')
def ping():
    return "🏓 Pong! Bot is running", 200

@web_app.route('/status')
def status():
    return {
        "status": "online",
        "bot": "සමාලි",
        "timestamp": datetime.datetime.now().isoformat(),
        "platform": "Replit + cron-job.org"
    }

def run_web_server():
    """Run Flask web server in a separate thread"""
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host='0.0.0.0', port=port, debug=False, threaded=True)

# ====== MODIFIED MAIN FOR REPLIT ======
def replit_main():
    """Start both Flask server and Telegram bot for Replit"""
    
    print("=" * 50)
    print("🚀 Starting සමාලි Bot on Replit...")
    print("=" * 50)
    
    # Start Flask web server in background thread for keep-alive
    print("🌐 Starting Flask web server for keep-alive...")
    web_thread = Thread(target=run_web_server, daemon=True)
    web_thread.start()
    print(f"✅ Web server started on port {os.environ.get('PORT', 8080)}")
    
    # Start Telegram bot
    print("🤖 Starting සමාලි Telegram bot...")
    asyncio.run(main())

if __name__ == "__main__":
    replit_main()