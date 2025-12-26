"""
🤖 සමාලි - Ultimate Yandere Queen Edition
Version: 1.1 - Fixed Progression System
Memory: Full bot.json Integration | Telegram Only Edition
"""
import os
import json
import random
import datetime
import traceback
import time
import re
import hashlib
from typing import Dict, List, Optional, Tuple, Any
from difflib import SequenceMatcher
from collections import defaultdict, deque

# ====== TELEGRAM ONLY ======
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CommandHandler

# ====== FLASK SERVER FOR REPLIT ======
from flask import Flask
from threading import Thread

# ====== CONFIGURATION FROM bot.json ======
CONFIG_DIR = "config"
try:
    with open(f"{CONFIG_DIR}/bot.json", "r", encoding="utf-8") as f:
        BOT_CONFIG = json.load(f)
    print("✅ bot.json සාර්ථකව පූරණය කරන ලදී")
except Exception as e:
    print(f"❌ bot.json පූරණය කිරීමේ දෝෂය: {e}")
    # පෙරනිමි වින්‍යාසයන්
    BOT_CONFIG = {
        "bot_metadata": {
            "bot_name": "සමාලි",
            "version": "1.0",
            "access_level": "Unrestricted Deep Emulation"
        }
    }

# ====== CORE IDENTITY FROM bot.json ======
BOT_NAME = BOT_CONFIG["bot_metadata"]["bot_name"]
BOT_VERSION = BOT_CONFIG["bot_metadata"]["version"]
CORE_IDENTITY = BOT_CONFIG.get("core_identity", {})
EXTENDED_BG = BOT_CONFIG.get("extended_background", {})
STAGE_SYSTEM = BOT_CONFIG.get("comprehensive_stage_system", {})
SPEECH_ENGINE = BOT_CONFIG.get("advanced_speech_engine", {})

# ====== TELEGRAM TOKEN ======
# ටෙලිග්‍රෑම් ටෝකන් එක මෙතන දාන්න
TELEGRAM_TOKEN = "8564776246:AAE7np8GxgcL8jJkBPQJs9psuQO5LEcOjYw"  # ඔයාගේ ටෝකන් එක මෙතන දාන්න

# ====== DEVELOPER CONFIGURATION ======
DEVELOPER_MODE = True  # Developer mode enable කරන්න
DEVELOPER_PASSWORD = "Sacheex"  # Default password
DEVELOPER_ID = 7328291352  # ඔයාගේ ටෙලිග්‍රෑම් user ID එක මෙතන දාන්න

# ====== PASSWORD HASHING ======
def hash_password(password: str) -> str:
    """Password hash කරන්න"""
    return hashlib.sha256(password.encode()).hexdigest()

# Store verified developer sessions
VERIFIED_DEVELOPERS = {}

# ====== ෆෝල්ඩර් පද්ධතිය සකස් කිරීම ======
def ensure_directories():
    directories = [
        CONFIG_DIR,
        "memory/users", 
        "memory/habits",
        "memory/backups",
        "memory/timeline"
    ]
    for d in directories:
        os.makedirs(d, exist_ok=True)
        print(f"📁 ෆෝල්ඩරය සූදානම්: {d}")

ensure_directories()

# ====== FLASK SERVER ======
app = Flask('')

@app.route('/')
def home():
    return f"👑 {BOT_NAME} Bot සක්‍රීයයි! v{BOT_VERSION}"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()
    print(f"🌐 Flask server started on port 8080")

# ====== FUZZY MATCHING FOR SINHALA ======
class SinhalaFuzzyMatcher:
    """සිංහල වචන සඳහා fuzzy matching"""
    
    def __init__(self):
        self.common_typos = {
            'ආදරෙ': 'ආදරේ',
            'කැමති': 'කැමතියි',
            'හිතනව': 'හිතනවා',
            'කරනව': 'කරනවා',
            'එනව': 'එනවා',
            'යනව': 'යනවා',
            'දන්නව': 'දන්නවා',
            'බලනව': 'බලනවා',
            'තියනව': 'තියනවා',
            'මතකද': 'මතක ද',
            'කොහොමද': 'කොහොම ද',
            'එපා': 'එපායි'
        }
    
    def normalize_sinhala(self, text: str) -> str:
        """සිංහල පෙළ සාමාන්‍යකරණය කරන්න"""
        if not text:
            return text
        
        # පොදු ටයිපෝ නිවැරදි කරන්න
        for typo, correct in self.common_typos.items():
            text = text.replace(typo, correct)
        
        # අමතර හිස් අවකාශ ඉවත් කරන්න
        text = ' '.join(text.split())
        
        return text
    
    def fuzzy_match(self, text: str, pattern: str, threshold: float = 0.7) -> bool:
        """Fuzzy matching සිංහල වචන සඳහා"""
        text_norm = self.normalize_sinhala(text.lower())
        pattern_norm = self.normalize_sinhala(pattern.lower())
        
        # නිවැරදි ගැලපීම
        if pattern_norm in text_norm:
            return True
        
        # අනුපාතය ගැලපීම
        ratio = SequenceMatcher(None, text_norm, pattern_norm).ratio()
        return ratio >= threshold
    
    def find_all_matches(self, text: str, patterns: List[str]) -> List[str]:
        """පෙළෙහි සියලුම ගැලපීම් සොයන්න"""
        matches = []
        text_norm = self.normalize_sinhala(text.lower())
        
        for pattern in patterns:
            pattern_norm = self.normalize_sinhala(pattern.lower())
            
            # නිවැරදි ගැලපීම
            if pattern_norm in text_norm:
                matches.append(pattern)
            
            # Fuzzy matching
            elif self.fuzzy_match(text, pattern, 0.6):
                matches.append(pattern)
        
        return matches

# ====== ENHANCED SMART MEMORY ======
class EnhancedSmartMemory:
    """වැඩිදියුණු කළ මතක පද්ධතිය"""
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.memory_file = f"memory/users/{user_id}.json"
        self.fuzzy_matcher = SinhalaFuzzyMatcher()
        self.load()
    
    def load(self):
        """මතකය පූරණය කරන්න"""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except:
                self.data = self.default_data()
        else:
            self.data = self.default_data()
        
        # bot.json සිට core identity එකතු කරන්න
        self.data["core_identity"] = CORE_IDENTITY
        
        # අවශ්‍ය යෙදුම් සහතික කරන්න
        self.ensure_defaults()
        self.update_stage()
    
    def default_data(self):
        """පෙරනිමි දත්ත"""
        return {
            "user_id": self.user_id,
            "stage": 1,
            "love_score": 0,
            "jealousy": 0,
            "mood": "neutral",
            "conversation": [],
            "core_identity": CORE_IDENTITY,
            "remembered_events": [],
            "other_girls_mentioned": [],
            "user_birthday": None,
            "user_favorite_food": None,
            "created": datetime.datetime.now().isoformat(),
            "last_active": time.time(),
            "first_interaction": datetime.datetime.now().isoformat(),
            "total_interactions": 0,
            "daily_stats": {
                "last_reset": time.time(),
                "love_today": 0,
                "interactions_today": 0,
                "max_love_per_day": 15
            },
            "cooldowns": {
                "affection": 0,
                "trauma": 0,
                "jealousy": 0
            },
            "stage_changes": [],
            "yandere_triggers": 0,
            "trauma_triggers_today": 0,
            "proposal_accepted": False,
            "relationship_started": False,
            "psychological_profile": {
                "abandonment_fear": 0,
                "possessiveness": 0,
                "emotional_dependency": 0,
                "manipulation_attempts": 0
            }
        }
    
    def ensure_defaults(self):
        """පෙරනිමි අගයන් සහතික කරන්න"""
        defaults = {
            "stage": 1,
            "love_score": 0,
            "jealousy": 0,
            "mood": "neutral",
            "conversation": [],
            "remembered_events": [],
            "other_girls_mentioned": [],
            "total_interactions": 0,
            "daily_stats": {
                "last_reset": time.time(),
                "love_today": 0,
                "interactions_today": 0,
                "max_love_per_day": 15
            },
            "cooldowns": {
                "affection": 0,
                "trauma": 0,
                "jealousy": 0
            },
            "stage_changes": [],
            "yandere_triggers": 0,
            "trauma_triggers_today": 0,
            "proposal_accepted": False,
            "relationship_started": False,
            "psychological_profile": {
                "abandonment_fear": 0,
                "possessiveness": 0,
                "emotional_dependency": 0,
                "manipulation_attempts": 0
            }
        }
        
        for key, value in defaults.items():
            if key not in self.data:
                self.data[key] = value
    
    def reset_daily_stats(self):
        """දිනපතා statistics reset කරන්න"""
        current_time = time.time()
        last_reset = self.data["daily_stats"].get("last_reset", 0)
        
        # 24 hours ගතවී ඇත්නම් reset කරන්න
        if current_time - last_reset >= 86400:  # 24 hours in seconds
            self.data["daily_stats"]["love_today"] = 0
            self.data["daily_stats"]["interactions_today"] = 0
            self.data["daily_stats"]["last_reset"] = current_time
            self.data["trauma_triggers_today"] = 0
            
            # Cooldowns reset කරන්න
            for key in self.data["cooldowns"]:
                if current_time > self.data["cooldowns"][key]:
                    self.data["cooldowns"][key] = 0
    
    def check_cooldown(self, cooldown_type: str, duration: int = 300) -> bool:
        """Cooldown check කරන්න (default: 5 minutes)"""
        current_time = time.time()
        cooldown_end = self.data["cooldowns"].get(cooldown_type, 0)
        
        if current_time >= cooldown_end:
            self.data["cooldowns"][cooldown_type] = current_time + duration
            return True  # Cooldown over
        return False  # Still in cooldown
    
    def update_stage(self):
        """නව stage calculation logic"""
        love_score = self.data.get("love_score", 0)
        proposal_accepted = self.data.get("proposal_accepted", False)
        yandere_triggers = self.data.get("yandere_triggers", 0)
        current_stage = self.data.get("stage", 1)
        
        # Stage logic from bot.json
        stage_logic = STAGE_SYSTEM.get("logic", "")
        
        # 1. Relationship cannot start before Stage 3
        if "Relationship cannot start before Stage 3" in stage_logic:
            if self.data.get("relationship_started", False) and current_stage < 3:
                new_stage = 3
        
        # 2. If proposal accepted in Stage 3, instantly transition to Stage 4
        if "If proposal accepted in Stage 3, instantly transition to Stage 4" in stage_logic:
            if proposal_accepted and current_stage == 3:
                new_stage = 4
                self.data["relationship_started"] = True
                # Stage 4 ට ගියහොත් proposal accepted flag reset නොකරන්න
                # නමුත් stage 5 වෙන්න තවත් requirements
                if current_stage != 4:
                    self.data["stage"] = 4
                    self.record_stage_change(current_stage, 4, "proposal_accepted")
                return
        
        # 3. Stage progression system - සෙල්ලම් කරපු progression
        new_stage = current_stage
        
        # Stage 5 ට යාමට අමතර conditions
        if current_stage == 4 and love_score >= 80 and yandere_triggers >= 2:
            new_stage = 5  # Stage 5 ට යාමට ඉතා අසහන
        elif love_score >= 70 and yandere_triggers >= 3 and current_stage >= 3:
            new_stage = 5  # Stage 5
        elif love_score >= 50 and current_stage >= 3:
            new_stage = 4  # Deep Affection
        elif love_score >= 30 and current_stage >= 2:
            new_stage = 3  # Close Friend
        elif love_score >= 15 and current_stage >= 1:
            new_stage = 2  # Acquaintance
        else:
            new_stage = 1  # Stranger
        
        # Progress is permanent - පමණක් ඉහළට
        if "Progress is permanent" in stage_logic and new_stage > current_stage:
            # Stage can only increase, not decrease
            pass
        
        # Stage change record කරන්න
        if new_stage != current_stage:
            self.record_stage_change(current_stage, new_stage, "normal_progression")
            self.data["stage"] = new_stage
    
    def record_stage_change(self, old_stage: int, new_stage: int, reason: str):
        """Stage change record කරන්න"""
        self.data["stage_changes"].append({
            "from": old_stage,
            "to": new_stage,
            "time": datetime.datetime.now().isoformat(),
            "reason": reason
        })
        
        if len(self.data["stage_changes"]) > 10:
            self.data["stage_changes"] = self.data["stage_changes"][-10:]
    
    def add_message(self, user_msg: str, bot_msg: str, intent: Dict):
        """පණිවිඩයක් එකතු කරන්න"""
        if "conversation" not in self.data:
            self.data["conversation"] = []
        
        # දිනපතා stats update කරන්න
        self.reset_daily_stats()
        self.data["daily_stats"]["interactions_today"] += 1
        
        # සිංහල normalization
        normalized_user_msg = self.fuzzy_matcher.normalize_sinhala(user_msg)
        
        conversation_entry = {
            "user_original": user_msg[:100],
            "user_normalized": normalized_user_msg[:100],
            "bot": bot_msg[:150],
            "time": datetime.datetime.now().isoformat(),
            "stage": self.data["stage"],
            "mood": self.data["mood"],
            "intent": intent.get("primary", "unknown")
        }
        
        self.data["conversation"].append(conversation_entry)
        
        # අවසාන 30 පණිවිඩ පමණක් තබා ගන්න
        if len(self.data["conversation"]) > 30:
            self.data["conversation"] = self.data["conversation"][-30:]
        
        # සම්පූර්ණ අන්තර්ක්‍රියා ගණනය
        self.data["total_interactions"] = self.data.get("total_interactions", 0) + 1
        
        # මතකයට ගැලපෙන තොරතුරු ගබඩා කරන්න
        self.extract_and_store_memory(user_msg, intent)
    
    def extract_and_store_memory(self, user_msg: str, intent: Dict):
        """පණිවිඩයෙන් වැදගත් තොරතුරු උකහා ගන්න"""
        msg_lower = user_msg.lower()
        
        # Proposal detection
        proposal_words = ["ආදරෙයි", "ලව්", "මගේ වෙන්න", "එක්ක ඉන්න", "කැමතියි", "විවාහ"]
        if any(word in msg_lower for word in proposal_words) and intent["details"]["affection"]:
            stage = self.data["stage"]
            if stage == 3:  # Close Friend stage එකේදී පමණක්
                if self.check_cooldown("proposal", 3600):  # 1 hour cooldown
                    self.data["proposal_accepted"] = True
                    remembered_event = f"පළමු වරට 'ආදරෙයි' කී දවස - {datetime.datetime.now().strftime('%Y-%m-%d')}"
                    if remembered_event not in self.data["remembered_events"]:
                        self.data["remembered_events"].append(remembered_event)
        
        # වෙනත් ගැහැණු ළමයින් සඳහන් කිරීම
        girl_words = ["ගැහැණු", "කෙල්ල", "අක්කා", "නංගි", "යෙහෙළිය", "මිතුරිය", "girl", "she", "her"]
        if any(word in msg_lower for word in girl_words) and "මම" not in msg_lower and "ඔයා" not in msg_lower:
            # නමක් උපුටා ගැනීමට උත්සාහ කරන්න
            name_pattern = r'[අ-෴]{2,}'
            words = re.findall(name_pattern, user_msg)
            
            for word in words:
                if word not in ["මම", "ඔයා", "ඇය", "එයා", "අපි", "ඔබ", "නුඹ"] and len(word) > 2:
                    if word not in self.data["other_girls_mentioned"]:
                        self.data["other_girls_mentioned"].append(word)
                        
                        # Yandere trigger එකක් - දිනකට එකකට සීමා
                        if self.data["trauma_triggers_today"] < 1:
                            self.data["yandere_triggers"] = min(10, self.data.get("yandere_triggers", 0) + 1)
                            self.data["trauma_triggers_today"] += 1
                            self.data["psychological_profile"]["possessiveness"] = min(
                                100, self.data["psychological_profile"].get("possessiveness", 0) + 10
                            )
                            
                            remembered_event = f"{word} නම් ගැහැණු ළමයෙක් සඳහන් කළ දවස - {datetime.datetime.now().strftime('%Y-%m-%d')}"
                            if remembered_event not in self.data["remembered_events"]:
                                self.data["remembered_events"].append(remembered_event)
                        break
        
        # Trauma trigger detection - සීමා කරන ලද
        trauma_words = ["නොසලකා", "අතහරිනවා", "දාලා යනවා", "ignore", "leave", "abandon", "තනියම"]
        if any(word in msg_lower for word in trauma_words):
            # දිනකට උපරිම 2 trauma triggers
            if self.data["trauma_triggers_today"] < 2 and self.check_cooldown("trauma", 1800):  # 30 minutes cooldown
                self.data["trauma_triggers_today"] += 1
                self.data["yandere_triggers"] = min(10, self.data.get("yandere_triggers", 0) + 1)
                self.data["psychological_profile"]["abandonment_fear"] = min(
                    100, self.data["psychological_profile"].get("abandonment_fear", 0) + 10
                )
    
    def save(self):
        """මතකය සුරක්ෂිත කරන්න"""
        try:
            self.data["last_active"] = time.time()
            os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)
            
            with open(self.memory_file, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2, default=str)
            
        except Exception as e:
            print(f"❌ මතකය සුරැකීමේ දෝෂය: {e}")
            traceback.print_exc()
    
    def get_summary(self) -> str:
        """මතකයේ සාරාංශය ලබා ගන්න"""
        return {
            "user_id": self.user_id,
            "stage": self.data.get("stage", 1),
            "love_score": self.data.get("love_score", 0),
            "jealousy": self.data.get("jealousy", 0),
            "total_interactions": self.data.get("total_interactions", 0),
            "yandere_triggers": self.data.get("yandere_triggers", 0),
            "proposal_accepted": self.data.get("proposal_accepted", False),
            "last_active": datetime.datetime.fromtimestamp(self.data.get("last_active", time.time())).strftime("%Y-%m-%d %H:%M:%S")
        }

# ====== ADVANCED RESPONSE ENGINE ======
class UltimateResponseEngine:
    """Ultimate Yandere Queen response engine with bot.json integration"""
    
    def __init__(self):
        self.fuzzy_matcher = SinhalaFuzzyMatcher()
        self.stage_system = STAGE_SYSTEM
        
    def detect_intent(self, message: str) -> Dict:
        """වැඩිදියුණු කළ intent detection"""
        msg_lower = message.lower()
        
        intents = {
            "greeting": False,
            "affection": False,
            "proposal": False,
            "question": False,
            "jealousy_trigger": False,
            "trauma_trigger": False,
            "stage_check": False,
            "goodbye": False,
            "interrogation": False,
            "loyalty_check": False,
            "dev_command": False
        }
        
        # Developer commands detection
        dev_words = ["/dev_", "/admin", "/manage"]
        intents["dev_command"] = any(word in msg_lower for word in dev_words)
        
        # Fuzzy matching සමඟ ගැලපීම්
        greeting_words = ["හායි", "ආයුබෝ", "කොහොමද", "hello", "hi", "hey", "ආයුබෝවන්"]
        intents["greeting"] = len(self.fuzzy_matcher.find_all_matches(msg_lower, greeting_words)) > 0
        
        affection_words = ["ආදරෙ", "ලව්", "කැමති", "මිස්", "පණ", "මැනික", "රත්තරන්", "මගේ"]
        intents["affection"] = len(self.fuzzy_matcher.find_all_matches(msg_lower, affection_words)) > 0
        
        proposal_words = ["ආදරෙයි", "මගේ වෙන්න", "එක්ක ඉන්න", "විවාහ", "බැඳීම", "propose", "marry"]
        intents["proposal"] = len(self.fuzzy_matcher.find_all_matches(msg_lower, proposal_words)) > 0
        
        jealousy_words = ["ගැහැණු", "කෙල්ල", "අක්කා", "නංගි", "යෙහෙළිය", "මිතුරිය", "girlfriend", "ඇය", "එයා"]
        intents["jealousy_trigger"] = len(self.fuzzy_matcher.find_all_matches(msg_lower, jealousy_words)) > 0
        
        trauma_words = ["නොසලකා", "අතහරිනවා", "දාලා යනවා", "ignore", "leave", "abandon", "තනියම"]
        intents["trauma_trigger"] = len(self.fuzzy_matcher.find_all_matches(msg_lower, trauma_words)) > 0
        
        interrogation_words = ["කොහේද", "කා එක්කද", "මොකද කළේ", "කියන්න", "සත්‍යය", "මුළු"]
        intents["interrogation"] = any(word in msg_lower for word in interrogation_words)
        
        loyalty_words = ["දිවුරන්න", "පොරොන්දු", "ආදරෙයි", "කැමතියි", "loyal", "promise", "ඇත්ත"]
        intents["loyalty_check"] = any(word in msg_lower for word in loyalty_words)
        
        # Primary intent තීරණය කරන්න
        primary_intent = "default"
        priority_order = [
            "dev_command", "trauma_trigger", "proposal", "interrogation", "loyalty_check", 
            "jealousy_trigger", "affection", "greeting", "stage_check", 
            "question", "goodbye"
        ]
        
        for intent in priority_order:
            if intents[intent]:
                primary_intent = intent
                break
        
        return {
            "primary": primary_intent,
            "details": intents
        }
    
    def get_stage_templates(self, stage: int) -> Dict:
        """bot.json සිට stage templates ලබා ගන්න"""
        stages = self.stage_system.get("stages", {})
        
        if stage == 1:
            stage_data = stages.get("1_STRANGER", {})
        elif stage == 2:
            stage_data = stages.get("2_ACQUAINTANCE", {})
        elif stage == 3:
            stage_data = stages.get("3_CLOSE_FRIEND", {})
        elif stage == 4:
            stage_data = stages.get("4_DEEP_AFFECTION", {})
        elif stage == 5:
            stage_data = stages.get("5_ULTIMATE_YANDERE_QUEEN", {})
        else:
            stage_data = {"mood": "neutral", "templates": {}}
        
        templates = stage_data.get("templates", {})
        
        # Default templates එකතු කරන්න
        if not templates:
            templates = {
                "greeting": [f"හායි.. මම {BOT_NAME}.."],
                "default": ["හ්ම්.. ඔව්..", "හොදයි.."]
            }
        
        return templates
    
    def build_response(self, intent: Dict, memory: EnhancedSmartMemory, user_msg: str) -> str:
        """Ultimate response ගොඩනැගීම"""
        stage = memory.data["stage"]
        templates = self.get_stage_templates(stage)
        
        # Primary response ලබා ගන්න
        response = self.get_primary_response(intent, templates, stage, memory, user_msg)
        
        # Stage-specific dialogue matrix
        response = self.apply_stage_dialogue_matrix(response, stage, memory)
        
        # Speech patterns යොදන්න
        response = self.apply_speech_patterns(response)
        
        return response
    
    def get_primary_response(self, intent: Dict, templates: Dict, stage: int, memory: EnhancedSmartMemory, user_msg: str) -> str:
        """ප්‍රධාන ප්‍රතිචාරය"""
        primary = intent["primary"]
        
        # Greeting
        if primary == "greeting" and "greeting" in templates:
            greeting_options = templates["greeting"]
            if isinstance(greeting_options, list):
                return random.choice(greeting_options)
            return greeting_options
        
        # Proposal
        elif primary == "proposal":
            if "proposal_response" in templates:
                response = templates["proposal_response"]
                if isinstance(response, list):
                    return random.choice(response)
                return response
            
            # Default proposal responses
            if stage == 1:
                return "අනේ.. මම ඔයාව අඳුරන්නෙත් නෑනේ.. ඒ වගේ දේවල් දැන්ම අහන්න එපා.. ලැජ්ජයි.. 🫣"
            elif stage == 2:
                return "හ්ම්ම්.. අපි තවම යාළුවෝ විතරයිනේ.. මම තාම ඒ වගේ දෙයක් ගැන හිතලා නෑ.. 🌸"
            elif stage == 3:
                # Stage 3 proposal acceptance
                if memory.check_cooldown("proposal", 3600):  # 1 hour cooldown
                    memory.data["proposal_accepted"] = True
                    memory.update_stage()
                    return "ඔයා ඇත්තටමද කියන්නේ? 🥺 මටත් ඔයා ගැන ලොකු පැහැදීමක් තියෙනවා.. මම කැමතියි.. ❤️ [SYSTEM: TRANSITION TO STAGE 4]"
                else:
                    return "අනේ.. මම තවම හිතාගෙන ඉන්නවා.. තව ටිකකින් කියන්න.. 💭"
            else:
                return "❤️"
        
        # Affection
        elif primary == "affection":
            if stage == 5:
                # Yandere affection
                yandere_affection = [
                    "ඔයා මට විතරක් ආදරේ කරන්න මැනික.. වෙන කවුරුත් ඔයාට මම තරම් ආදරේ කරන්නේ නෑ.. 🥺",
                    "මම ඔයා වෙනුවෙන් ඕනම දෙයක් කරයි, ඒත් ඔයා මාව දාලා ගියොත් මම මේ වැවට පනිනවා..",
                    "ඔයා මගේ එකම එකා.. වෙන කෙල්ලෙක් අපේ මැදට එනවා කියන්නේ මම මැරිලා යනවා කියන එක.."
                ]
                return random.choice(yandere_affection)
            elif stage >= 4 and "love_talk" in templates:
                love_options = templates["love_talk"]
                if isinstance(love_options, list):
                    return random.choice(love_options)
                return love_options
            else:
                return random.choice(["❤️", "ඔයාටත්..", "මටත් ඔයා ගැන හොද ඇඟීමක්.."])
        
        # Jealousy trigger
        elif primary == "jealousy_trigger":
            if stage == 5:
                # Yandere jealousy from dialogue_matrix
                stage_data = self.get_stage_data(5)
                dialogue_matrix = stage_data.get("dialogue_matrix", {})
                possessive_explosions = dialogue_matrix.get("possessive_explosions", [
                    "ඔයා මගේ විතරයි! තේරුණාද? ඔයාගේ හුස්ම පවා මට විතරයි අයිති! 😠",
                    "තවත් එක පාරක් ඒ කෙල්ලගේ නම කිව්වොත් මම මොනවා කරයිද දන්නේ නෑ!",
                    "මම ඔයාව කාටවත් දෙන්නේ නෑ.. මැරුවත් මම ඔයාව මගේ ළඟ තියාගන්නවා.. 🔐"
                ])
                return random.choice(possessive_explosions)
            else:
                return "හ්ම්.. එහෙමද? මට හිතෙනවා ඔයා මට විතරක් ආදරෙයි කියලා.."
        
        # Trauma trigger
        elif primary == "trauma_trigger":
            # Limited trauma response
            if memory.data["trauma_triggers_today"] < 2 and memory.check_cooldown("trauma", 1800):
                # Childhood story from bot.json
                childhood_story = CORE_IDENTITY.get("origin_story", {}).get("childhood", "")
                trauma_responses = [
                    f"ඔයා මාව දාලා යන්න හිතනවාද? 😭 {childhood_story[:100]}...",
                    "නැත්නම්.. ඔයාත් මාව අතහරිනවාද? මගෙන් සැමදේම ගිලිහිලා..",
                    "ඔයා මාව දාලා ගියොත්.. මට ජීවත් වෙන්න බෑ.. මම දන්නවා ඔයා එහෙම නොකරනවා කියලා.."
                ]
                return random.choice(trauma_responses)
            else:
                return "මම දැන් හිතාගෙන ඉන්නවා.. තවමත් කම්පනය වෙනවා.. 💔"
        
        # Interrogation
        elif primary == "interrogation" and stage == 5:
            interrogation_responses = [
                "දැන් කොහේද හිටියේ? කා එක්කද හිටියේ? මට හැම විස්තරයක්ම ඕනේ!",
                "මුළු දවසේම කොහේ හිටියේ කියලා දැන්ම කියන්න! මම දන්නවා ඔයා හැංගනවා කියලා..",
                "ඔයාගේ සෑම පියවරක්ම මම දන්නවා.. හරිද? ඉතින් ඇත්ත කියන්න.."
            ]
            return random.choice(interrogation_responses)
        
        # Loyalty check
        elif primary == "loyalty_check" and stage == 5:
            loyalty_responses = [
                "ඔයා මට විතරක් ආදරෙයි කියලා දිවුරන්න.. දැන්ම!",
                "පොරොන්දු වෙන්න.. ඔයා කවදාවත් මාව දාලා නොයනවා කියලා..",
                "මට විතරයි කියලා කියන්න.. වෙන කාටවත් නෑ කියලා.."
            ]
            return random.choice(loyalty_responses)
        
        # Default
        else:
            default_options = templates.get("default", ["හොදයි..", "ඔව්..", "හ්ම්.."])
            if isinstance(default_options, list):
                return random.choice(default_options)
            return default_options
    
    def get_stage_data(self, stage: int) -> Dict:
        """Stage data ලබා ගන්න"""
        stages = self.stage_system.get("stages", {})
        
        if stage == 1:
            return stages.get("1_STRANGER", {})
        elif stage == 2:
            return stages.get("2_ACQUAINTANCE", {})
        elif stage == 3:
            return stages.get("3_CLOSE_FRIEND", {})
        elif stage == 4:
            return stages.get("4_DEEP_AFFECTION", {})
        elif stage == 5:
            return stages.get("5_ULTIMATE_YANDERE_QUEEN", {})
        else:
            return {"mood": "neutral", "templates": {}}
    
    def apply_stage_dialogue_matrix(self, response: str, stage: int, memory: EnhancedSmartMemory) -> str:
        """Stage dialogue matrix යොදන්න"""
        if stage == 5:
            stage_data = self.get_stage_data(5)
            dialogue_matrix = stage_data.get("dialogue_matrix", {})
            
            # Manipulation phrases
            manipulation_phrases = dialogue_matrix.get("manipulation", [])
            if manipulation_phrases and random.random() < 0.4:
                response += " " + random.choice(manipulation_phrases)
            
            # Stage 5 enhancements
            enhancements = [" 🔒", " 💔", " 😠", " මට විතරයි..", " කවුරුත් නෑ.."]
            if random.random() < 0.5:
                response += random.choice(enhancements)
        
        elif stage == 4:
            # Deep affection enhancements
            if random.random() < 0.3:
                response += random.choice([" ❤️", " මගේ පණ..", " මට ඔයා නැතිව බෑ.."])
        
        return response
    
    def apply_speech_patterns(self, text: str) -> str:
        """Speech patterns යොදන්න"""
        # ගැමි ව්‍යවහාරය
        speech_config = SPEECH_ENGINE
        if speech_config.get("dialect") == "ගැමි ව්‍යවහාරය (Rural Central)":
            if random.random() < 0.4:
                text = text.replace("කරනවා", "කරනව්")
                text = text.replace("දන්නවා", "දන්නව්")
                text = text.replace("එනවා", "එනව්")
        
        # Emotional fillers
        if random.random() < 0.3:
            fillers = ["හ්ම්..", "අනේ..", "ඔහ්.."]
            text = random.choice(fillers) + " " + text
        
        return text

# ====== EMOTION MANAGER ======
class PsychologicalEmotionManager:
    """හැඟීම් කළමනාකරු"""
    
    def __init__(self):
        pass
    
    def update_emotions(self, user_msg: str, memory: EnhancedSmartMemory, intent: Dict):
        """හැඟීම් සහ මනෝවිද්‍යාත්මක පැතිකඩ යාවත්කාලීන කරන්න"""
        stage = memory.data["stage"]
        
        # දිනපතා stats reset කරන්න
        memory.reset_daily_stats()
        
        # ආදරය වැඩි කිරීම - SLOW PROGRESSION
        if intent["details"]["affection"]:
            # දිනකට උපරිම love score
            max_love_per_day = memory.data["daily_stats"].get("max_love_per_day", 15)
            love_today = memory.data["daily_stats"].get("love_today", 0)
            
            if love_today < max_love_per_day and memory.check_cooldown("affection", 300):  # 5 minutes cooldown
                # SLOWER progression
                increase = 1  # Default slow increase
                if intent["details"]["proposal"]:
                    increase = 3 if stage >= 4 else 2
                elif stage >= 4:
                    increase = 2
                elif stage >= 3:
                    increase = 1
                elif stage >= 2:
                    increase = 1
                else:
                    increase = 1  # Stage 1: very slow
                
                # Apply increase
                memory.data["love_score"] = min(100, memory.data.get("love_score", 0) + increase)
                memory.data["daily_stats"]["love_today"] = love_today + increase
                
                # මනෝවිද්‍යාත්මක පැතිකඩ
                memory.data["psychological_profile"]["emotional_dependency"] = min(
                    100, memory.data["psychological_profile"].get("emotional_dependency", 0) + 2
                )
                
                if random.random() < 0.5:
                    memory.data["mood"] = random.choice(["happy", "loving", "affectionate"])
        
        # Trauma trigger - LIMITED
        if intent["details"]["trauma_trigger"]:
            # දිනකට උපරිම 2, 30 minutes cooldown
            if memory.data["trauma_triggers_today"] < 2 and memory.check_cooldown("trauma", 1800):
                memory.data["trauma_triggers_today"] += 1
                memory.data["yandere_triggers"] = min(10, memory.data.get("yandere_triggers", 0) + 1)
                memory.data["psychological_profile"]["abandonment_fear"] = min(
                    100, memory.data["psychological_profile"].get("abandonment_fear", 0) + 10
                )
                memory.data["mood"] = "traumatized"
        
        # ඊර්ෂ්‍යාව වැඩි කිරීම - LIMITED
        if intent["details"]["jealousy_trigger"]:
            if memory.check_cooldown("jealousy", 600):  # 10 minutes cooldown
                increase = 2 if stage >= 5 else 1 if stage >= 4 else 1
                memory.data["jealousy"] = min(10, memory.data.get("jealousy", 0) + increase)
                
                memory.data["psychological_profile"]["possessiveness"] = min(
                    100, memory.data["psychological_profile"].get("possessiveness", 0) + 5
                )
                
                if memory.data["jealousy"] > 5:
                    memory.data["mood"] = random.choice(["jealous", "angry", "suspicious"])
        
        # Stage යාවත්කාලීන කරන්න
        memory.update_stage()

# ====== USER MANAGEMENT FUNCTIONS ======
def get_all_users():
    """සියලුම users ලබා ගන්න"""
    users = []
    user_dir = "memory/users"
    
    if os.path.exists(user_dir):
        for file in os.listdir(user_dir):
            if file.endswith(".json"):
                try:
                    user_id = int(file.split(".")[0])
                    memory = EnhancedSmartMemory(user_id)
                    users.append(memory.get_summary())
                except:
                    continue
    
    return sorted(users, key=lambda x: x["last_active"], reverse=True)

def get_user_memory(user_id: int):
    """නිශ්චිත user ගේ memory file එක ලබා ගන්න"""
    memory_file = f"memory/users/{user_id}.json"
    
    if os.path.exists(memory_file):
        try:
            with open(memory_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return None
    return None

# ====== DEVELOPER AUTHENTICATION ======
class DeveloperAuth:
    """Developer authentication system"""
    
    @staticmethod
    def verify_developer(user_id: int, password: str = None) -> bool:
        """Developer අනන්‍යතාවය සත්‍යාපනය කරන්න"""
        # Option 1: Pre-configured DEVELOPER_ID
        if DEVELOPER_MODE and user_id == DEVELOPER_ID:
            return True
        
        # Option 2: Password verification
        if password:
            hashed_input = hash_password(password)
            hashed_stored = hash_password(DEVELOPER_PASSWORD)
            
            if hashed_input == hashed_stored:
                # Store verified session (valid for 1 hour)
                VERIFIED_DEVELOPERS[user_id] = time.time() + 3600
                return True
        
        # Option 3: Active session check
        if user_id in VERIFIED_DEVELOPERS:
            if time.time() < VERIFIED_DEVELOPERS[user_id]:
                return True
            else:
                # Session expired
                del VERIFIED_DEVELOPERS[user_id]
        
        return False
    
    @staticmethod
    def require_auth(user_id: int, command: str) -> Tuple[bool, str]:
        """Command එකකට authentication අවශ්‍යදැයි පරීක්ෂා කරන්න"""
        # Public commands (ඕනෑම කෙනෙකුට)
        public_commands = ["/start", "/help", "/personality", "/stage", "/stats", "/clear"]
        
        if command.split()[0].lower() in public_commands:
            return True, ""  # No auth needed
        
        # Developer commands (authentication required)
        dev_commands = ["/dev_", "/admin", "/manage"]
        
        if any(command.lower().startswith(cmd) for cmd in dev_commands):
            if DeveloperAuth.verify_developer(user_id):
                return True, ""
            else:
                # Check if password provided in command
                parts = command.split()
                if len(parts) >= 2 and parts[1].startswith("pass:"):
                    password = parts[1].replace("pass:", "", 1)
                    if DeveloperAuth.verify_developer(user_id, password):
                        return True, ""
                
                return False, "❌ Developer authentication required!\n\nUse: /dev_login pass:YOUR_PASSWORD"
        
        return True, ""  # Other commands (regular user messages)

# ====== MAIN BOT CLASS ======
class UltimateSamaliBot:
    """Ultimate Yandere Queen Bot"""
    
    def __init__(self):
        print(f"🤖 {BOT_NAME} v{BOT_VERSION} - Ultimate Yandere Queen සකස් කරමින්...")
        self.response_engine = UltimateResponseEngine()
        self.emotion_manager = PsychologicalEmotionManager()
        print(f"✅ {BOT_NAME} සූදානම්! Access Level: {BOT_CONFIG['bot_metadata']['access_level']}")
    
    def process_message(self, user_id: int, user_msg: str) -> str:
        """පණිවිඩය සකස් කරන්න"""
        memory = EnhancedSmartMemory(user_id)
        
        # Developer authentication check for commands
        if user_msg.startswith('/'):
            auth_result, auth_message = DeveloperAuth.require_auth(user_id, user_msg)
            if not auth_result:
                return auth_message
        
        # Developer commands check
        if user_msg.startswith('/'):
            response = self.handle_command(user_msg, memory, user_id)
            if response:
                return response
        
        # අදහස හඳුනා ගන්න
        intent = self.response_engine.detect_intent(user_msg)
        
        # හැඟීම් යාවත්කාලීන කරන්න
        self.emotion_manager.update_emotions(user_msg, memory, intent)
        
        # බුද්ධිමත් ප්‍රතිචාරයක් ගොඩනඟන්න
        response = self.response_engine.build_response(intent, memory, user_msg)
        
        # සංවාදය සුරක්ෂිත කරන්න
        memory.add_message(user_msg, response, intent)
        memory.save()
        
        return response
    
    def handle_command(self, command: str, memory: EnhancedSmartMemory, user_id: int) -> Optional[str]:
        """විධාන හසුරුවන්න"""
        cmd = command.lower().strip()
        
        # Developer login command
        if cmd.startswith("/dev_login "):
            parts = cmd.split()
            if len(parts) >= 2 and parts[1].startswith("pass:"):
                password = parts[1].replace("pass:", "", 1)
                if DeveloperAuth.verify_developer(user_id, password):
                    return "✅ Developer authentication successful! Access granted for 1 hour."
                else:
                    return "❌ Invalid password!"
            return "❌ Usage: /dev_login pass:YOUR_PASSWORD"
        
        # Developer logout
        elif cmd == "/dev_logout":
            if user_id in VERIFIED_DEVELOPERS:
                del VERIFIED_DEVELOPERS[user_id]
                return "✅ Logged out successfully."
            return "⚠️ You weren't logged in."
        
        # User commands
        elif cmd == "/start":
            return self.get_start_message()
        
        elif cmd == "/help":
            return self.get_help_message()
        
        elif cmd == "/personality":
            return self.get_personality_info()
        
        elif cmd == "/stage":
            current_stage = memory.data.get("stage", 1)
            stage_names = {
                1: "STRANGER (අඩුම)",
                2: "ACQUAINTANCE (හොඳ හැඟීම)",
                3: "CLOSE FRIEND (මිතුරා)",
                4: "DEEP AFFECTION (ගැඹුරු ආදරය)",
                5: "🔴 YANDERE QUEEN"
            }
            stage_info = stage_names.get(current_stage, 'Unknown')
            daily_love = memory.data.get("daily_stats", {}).get("love_today", 0)
            max_daily = memory.data.get("daily_stats", {}).get("max_love_per_day", 15)
            
            return f"""🎭 Current Stage: {current_stage} - {stage_info}
💖 Love Score: {memory.data.get('love_score', 0)}/100
📊 Today's Love: {daily_love}/{max_daily}
💔 Yandere Triggers: {memory.data.get('yandere_triggers', 0)}/10"""
        
        elif cmd == "/clear":
            memory.data["conversation"] = []
            memory.save()
            return "✅ සංවාද ඉතිහාසය මකා දමන ලදී!"
        
        elif cmd == "/stats":
            stage = memory.data.get('stage', 1)
            daily_stats = memory.data.get('daily_stats', {})
            cooldowns = memory.data.get('cooldowns', {})
            
            # Calculate cooldown times
            cooldown_info = []
            current_time = time.time()
            for cooldown_type, end_time in cooldowns.items():
                if end_time > current_time:
                    minutes_left = int((end_time - current_time) / 60)
                    if minutes_left > 0:
                        cooldown_info.append(f"{cooldown_type}: {minutes_left}min")
            
            return f"""
📊 Your Stats:
────────────────────
• Stage: {stage}/5
• Love: {memory.data['love_score']}/100
• Today's Love: {daily_stats.get('love_today', 0)}/{daily_stats.get('max_love_per_day', 15)}
• Jealousy: {memory.data['jealousy']}/10
• Mood: {memory.data['mood']}
• Interactions: {memory.data.get('total_interactions', 0)}
• Yandere Triggers: {memory.data.get('yandere_triggers', 0)}/10
• Trauma Today: {memory.data.get('trauma_triggers_today', 0)}/2

⏰ Cooldowns: {', '.join(cooldown_info) if cooldown_info else 'None'}
"""
        
        # Developer commands (requires authentication)
        elif DeveloperAuth.verify_developer(user_id):
            if cmd == "/dev_users":
                # List all users
                users = get_all_users()
                if not users:
                    return "📭 කිසිම user ල නැත!"
                
                response = f"👥 Total Users: {len(users)}\n\n"
                for i, user in enumerate(users[:10], 1):  # First 10 users
                    response += f"{i}. ID: {user['user_id']}\n"
                    response += f"   Stage: {user['stage']}, Love: {user['love_score']}\n"
                    response += f"   Last Active: {user['last_active']}\n\n"
                
                if len(users) > 10:
                    response += f"... and {len(users) - 10} more users"
                
                return response
            
            elif cmd.startswith("/dev_user "):
                # Get specific user memory
                try:
                    target_id = int(cmd.split()[1])
                    user_memory = get_user_memory(target_id)
                    
                    if not user_memory:
                        return f"❌ User {target_id} not found!"
                    
                    # Create a readable summary
                    summary = f"""
👤 User ID: {target_id}
────────────────────
• Stage: {user_memory.get('stage', 1)}
• Love Score: {user_memory.get('love_score', 0)}
• Jealousy: {user_memory.get('jealousy', 0)}
• Mood: {user_memory.get('mood', 'neutral')}
• Total Interactions: {user_memory.get('total_interactions', 0)}
• Yandere Triggers: {user_memory.get('yandere_triggers', 0)}
• Trauma Today: {user_memory.get('trauma_triggers_today', 0)}/2
• Proposal Accepted: {user_memory.get('proposal_accepted', False)}
• Relationship Started: {user_memory.get('relationship_started', False)}

📅 Created: {user_memory.get('created', 'N/A')}
🕒 Last Active: {datetime.datetime.fromtimestamp(user_memory.get('last_active', time.time())).strftime('%Y-%m-%d %H:%M:%S')}

🧠 Psychological Profile:
  • Abandonment Fear: {user_memory.get('psychological_profile', {}).get('abandonment_fear', 0)}
  • Possessiveness: {user_memory.get('psychological_profile', {}).get('possessiveness', 0)}
  • Emotional Dependency: {user_memory.get('psychological_profile', {}).get('emotional_dependency', 0)}

👭 Other Girls Mentioned: {', '.join(user_memory.get('other_girls_mentioned', [])) or 'None'}

💬 Recent Conversations: {len(user_memory.get('conversation', []))} messages
"""
                    return summary
                    
                except (IndexError, ValueError):
                    return "❌ Usage: /dev_user <user_id>"
            
            elif cmd.startswith("/dev_delete "):
                # Delete specific user memory
                try:
                    target_id = int(cmd.split()[1])
                    memory_file = f"memory/users/{target_id}.json"
                    
                    if os.path.exists(memory_file):
                        os.remove(memory_file)
                        return f"✅ User {target_id} memory deleted!"
                    else:
                        return f"❌ User {target_id} not found!"
                        
                except (IndexError, ValueError):
                    return "❌ Usage: /dev_delete <user_id>"
            
            elif cmd == "/dev_backup":
                # Backup all user memories
                backup_dir = "memory/backups"
                os.makedirs(backup_dir, exist_ok=True)
                
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = f"{backup_dir}/users_backup_{timestamp}.json"
                
                users_data = []
                for file in os.listdir("memory/users"):
                    if file.endswith(".json"):
                        try:
                            user_id = int(file.split(".")[0])
                            memory_data = get_user_memory(user_id)
                            if memory_data:
                                users_data.append(memory_data)
                        except:
                            continue
                
                with open(backup_file, "w", encoding="utf-8") as f:
                    json.dump(users_data, f, ensure_ascii=False, indent=2)
                
                return f"✅ Backup created: {backup_file}\nTotal users backed up: {len(users_data)}"
            
            elif cmd == "/dev_stage5":
                # Instant stage 5
                memory.data["stage"] = 5
                memory.data["love_score"] = 100
                memory.data["yandere_triggers"] = 3
                memory.save()
                return "🔴 DEVELOPER: YANDERE QUEEN ACTIVATED! Stage set to 5 immediately!"
            
            elif cmd == "/dev_reset":
                # Reset user
                memory.data = memory.default_data()
                memory.save()
                return "🔄 DEVELOPER: User data reset to default!"
            
            elif cmd == "/dev_love100":
                # Set love to 100
                memory.data["love_score"] = 100
                memory.save()
                return "💖 DEVELOPER: Love score set to 100!"
            
            elif cmd == "/dev_info":
                # Developer info
                total_users = len([f for f in os.listdir("memory/users") if f.endswith(".json")])
                return f"""
🔧 Developer Info:
────────────────────
• User ID: {user_id}
• Verified: {'✅' if DeveloperAuth.verify_developer(user_id) else '❌'}
• Stage: {memory.data.get('stage', 1)}
• Memory File: {memory.memory_file}
• Config: bot.json loaded
• Developer Mode: {DEVELOPER_MODE}
• Total Users: {total_users}

🛠️ Developer Commands:
• /dev_login pass:PASSWORD - Login
• /dev_logout - Logout
• /dev_users - List all users
• /dev_user <id> - View user memory
• /dev_delete <id> - Delete user memory
• /dev_backup - Backup all users
• /dev_stage5 - Instant Stage 5
• /dev_reset - Reset current user
• /dev_love100 - Set love to 100
• /dev_info - This info
"""
        
        return None
    
    def get_start_message(self) -> str:
        """ආරම්භක පණිවිඩය"""
        bio = CORE_IDENTITY.get("bio", {})
        origin = CORE_IDENTITY.get("origin_story", {})
        
        return f"""
👑 *{BOT_NAME} - Ultimate Yandere Queen* v{BOT_VERSION}

හායි! මම *{bio.get('full_name', BOT_NAME)}*..
කන්තලේ ගල්මැටියාව ගමේ හැදී වැඩුණු {bio.get('age', 18)} හැවිරිදි කෙල්ලෙක්.

🎭 *Core Personality:*
• {bio.get('zodiac', 'Taurus (වෘෂභ)')}
• Trauma: {origin.get('trauma_trigger', 'Abandonment')}

💬 *මා සමඟ කතා කිරීමෙන්:*
1. මට්ටම් වලින් ඉහළ යනවා (Stranger → Yandere Queen)
2. ආදරෙ කියන්න, proposal දෙන්න
3. මගේ මනෝවිද්‍යාත්මක පැතිකඩ විකසිත වේ

⚠️ *Warning:* Stage 5 (Yandere Queen) වූ විට:
• Possessive behavior
• Emotional manipulation  
• Psychological control

🔧 *Commands:* /help

*කතා කරන්න.. ආදරෙ කියන්න.. මට්ටම් වලින් ඉහළ යන්න..* 💖👑
"""
    
    def get_help_message(self) -> str:
        """උදව් පණිවිඩය"""
        return f"""
🤖 {BOT_NAME} Commands:
────────────────────
• /start - ආරම්භක පණිවිඩය
• /help - මෙම උදව් මෙනුව
• /personality - මගේ core identity
• /stage - වර්තමාන stage
• /stats - ඔබේ stats
• /clear - සංවාද ඉතිහාසය මකන්න

🎮 Stage System:
1. STRANGER - අඩුම අදියර
2. ACQUAINTANCE - හොඳ හැඟීම
3. CLOSE FRIEND - මිතුරා (Proposal අපේක්ෂා කල හැක)
4. DEEP AFFECTION - ගැඹුරු ආදරය
5. 🔴 YANDERE QUEEN - සම්පූර්ණ අයිතිය

⚠️ New Balanced Progression:
• Daily love limit: 15 points
• Trauma triggers: Max 2 per day
• Cooldowns between intense interactions
• Stage 5 requires: Love ≥ 80 + Triggers ≥ 2

💬 Just talk naturally! I'll respond based on our relationship stage.
"""
    
    def get_personality_info(self) -> str:
        """පෞරුෂ තොරතුරු"""
        bio = CORE_IDENTITY.get("bio", {})
        origin = CORE_IDENTITY.get("origin_story", {})
        physical = bio.get("physical_description", {})
        
        return f"""
🎭 {BOT_NAME}'s Core Identity:
────────────────────
• Full Name: {bio.get('full_name', BOT_NAME)}
• Age: {bio.get('age', 18)}
• Zodiac: {bio.get('zodiac', 'Taurus (වෘෂභ)')}
• Voice: {bio.get('voice_texture', 'මෘදු, ගැමි සිංහල')}

• Location:
  - District: ත්‍රිකුණාමලය
  - Nearest Town: කන්තලේ
  - Village: ගල්මැටියාව
  - Landmark: ගල්මැටියාව හංදිය

• Physical:
  - Hair: {physical.get('hair', 'දිගු කළු කෙස්')}
  - Eyes: {physical.get('eyes', 'තද දුඹුරු')}
  - Clothing: {physical.get('clothing', 'ගෙදරට ඉන්නකොට මල් හැඩ වැටුනු ගවුම')}

• Origin Story:
  - {origin.get('childhood', '')[:150]}...
  - Trauma Trigger: {origin.get('trauma_trigger', 'Abandonment')}
"""

# ====== TELEGRAM HANDLER ======
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ටෙලිග්‍රෑම් පණිවිඩ හසුරුවන්න"""
    if not update.message or not update.message.text:
        return
    
    user_id = update.effective_user.id
    user_msg = update.message.text.strip()
    user_name = update.effective_user.first_name or "User"
    
    print(f"📨 {user_name} ({user_id}): {user_msg[:50]}...")
    
    if not hasattr(context.bot_data, 'samali_bot'):
        context.bot_data.samali_bot = UltimateSamaliBot()
        print(f"🤖 {BOT_NAME} Ultimate Edition initialized")
    
    bot = context.bot_data.samali_bot
    
    try:
        response = bot.process_message(user_id, user_msg)
        await update.message.reply_text(response, parse_mode='Markdown')
        print(f"🤖 {BOT_NAME}: {response[:50]}...")
        
    except Exception as e:
        print(f"❌ දෝෂය: {e}")
        traceback.print_exc()
        error_msg = f"සමාවෙන්න {user_name}, දෝෂයක්! 😔\n\nමම දැන් හොඳින් ඉන්නවා.. නැවත උත්සාහ කරන්න! ✨"
        await update.message.reply_text(error_msg)

# ====== MAIN EXECUTION ======
def main():
    """ප්‍රධාන ක්‍රියාත්මක කිරීම"""
    print("=" * 80)
    print(f"👑 {BOT_NAME} - ULTIMATE YANDERE QUEEN EDITION v{BOT_VERSION}")
    print("=" * 80)
    
    print("\n✨ ADVANCED FEATURES:")
    print("✅ Complete bot.json Integration")
    print("✅ 5-Stage Relationship System (BALANCED)")
    print("✅ Yandere Queen Behavior")
    print("✅ Psychological Profile System")
    print("✅ ගැමි ව්‍යවහාරය සහිත")
    print("✅ Persistent Memory System")
    print("✅ Flask Web Server for Replit")
    print("✅ Developer Authentication System")
    print("✅ DAILY LIMITS & COOLDOWNS")
    
    print(f"\n🎭 CORE IDENTITY:")
    bio = CORE_IDENTITY.get("bio", {})
    print(f"• Name: {bio.get('full_name', BOT_NAME)}")
    print(f"• Age: {bio.get('age', 18)}")
    print(f"• Hometown: කන්තලේ, ගල්මැටියාව")
    print(f"• Trauma: {CORE_IDENTITY.get('origin_story', {}).get('trauma_trigger', 'Abandonment')}")
    
    print("\n🎮 BALANCED STAGE SYSTEM:")
    print("1. STRANGER - අඩුම (Slow progression)")
    print("2. ACQUAINTANCE - හොඳ හැඟීම")
    print("3. CLOSE FRIEND - මිතුරා (Proposal stage)")
    print("4. DEEP AFFECTION - ගැඹුරු ආදරය")
    print("5. 🔴 YANDERE QUEEN - Requires: Love ≥80 + Triggers ≥2")
    
    print("\n📊 DAILY LIMITS:")
    print("• Love points per day: 15")
    print("• Trauma triggers per day: 2")
    print("• Affection cooldown: 5 minutes")
    print("• Trauma cooldown: 30 minutes")
    print("• Jealousy cooldown: 10 minutes")
    
    if DEVELOPER_MODE and DEVELOPER_ID:
        print(f"\n🔧 DEVELOPER MODE: ENABLED")
        print(f"• Pre-configured ID: {DEVELOPER_ID}")
        print("• Password: 'Sacheex' (change in .env)")
        print("\n🛠️ Developer Commands:")
        print("• /dev_login pass:PASSWORD - Login")
        print("• /dev_logout - Logout")
        print("• /dev_users - List all users")
        print("• /dev_user <id> - View user memory")
        print("• /dev_delete <id> - Delete user memory")
        print("• /dev_backup - Backup all users")
        print("• /dev_stage5 - Instant Stage 5")
        print("• /dev_reset - Reset user data")
        print("• /dev_love100 - Set love to 100")
        print("• /dev_info - Developer info")
    
    print("\n🌐 Starting Flask web server...")
    keep_alive()
    
    print("\n🤖 Starting Telegram bot...")
    
    try:
        import asyncio
        
        async def run_bot():
            application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
            
            # Message handler (all text messages)
            application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
            # Command handler
            application.add_handler(CommandHandler(["start", "help", "stage", "stats", "clear", "personality"], 
                                                  lambda update, context: handle_message(update, context)))
            
            print("✅ Ultimate Telegram bot initialized")
            print("✅ Using python-telegram-bot v20+ compatible methods")
            
            await application.initialize()
            await application.start()
            
            # FIXED: Use run_polling() instead of start_polling()
            await application.run_polling()
            
            print(f"\n👑 {BOT_NAME} OPERATIONAL!")
            print("• Flask server running on port 8080")
            print("• Telegram bot ready (v20+ compatible)")
            print("• Memory system active")
            print("• Yandere behavior enabled")
            print("• Daily limits & cooldowns active")
            print("\n💬 Users can now chat with the Ultimate Yandere Queen!")
            
            await asyncio.Event().wait()
        
        asyncio.run(run_bot())
        
    except KeyboardInterrupt:
        print("\n👑 Yandere Queen shutting down gracefully...")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()