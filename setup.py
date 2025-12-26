#!/usr/bin/env python3
"""
සමාලි යන්ඩෙරේ බොට් Setup Script
"""
import os
import sys
import subprocess
import json
from pathlib import Path

def print_colored(text, color):
    """Print colored text"""
    colors = {
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'purple': '\033[95m',
        'cyan': '\033[96m',
        'nc': '\033[0m'
    }
    print(f"{colors.get(color, colors['nc'])}{text}{colors['nc']}")

def check_python():
    """Check Python version"""
    print_colored("[1/6] Checking Python version...", "cyan")
    
    try:
        result = subprocess.run([sys.executable, "--version"], 
                               capture_output=True, text=True)
        version = result.stdout.strip()
        print_colored(f"✅ {version}", "green")
        
        # Check Python 3.8+
        version_info = sys.version_info
        if version_info.major < 3 or (version_info.major == 3 and version_info.minor < 8):
            print_colored("❌ Python 3.8+ required!", "red")
            return False
        return True
    except:
        print_colored("❌ Python not found!", "red")
        return False

def create_directories():
    """Create necessary directories"""
    print_colored("[2/6] Creating directories...", "cyan")
    
    directories = [
        "config",
        "memory/users",
        "memory/habits", 
        "memory/backups",
        "memory/timeline"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print_colored(f"  📁 Created: {directory}", "green")
    
    return True

def check_config_files():
    """Check and create configuration files"""
    print_colored("[3/6] Checking configuration files...", "cyan")
    
    # Check .env
    if not Path(".env").exists():
        print_colored("⚠️  .env file not found!", "yellow")
        
        if Path(".env.example").exists():
            print_colored("📝 Copying from .env.example...", "blue")
            with open(".env.example", "r") as src:
                with open(".env", "w") as dst:
                    dst.write(src.read())
            print_colored("✅ .env created from template", "green")
            print_colored("ℹ️  Please edit .env with your tokens", "yellow")
        else:
            print_colored("📝 Creating basic .env file...", "blue")
            env_content = """# Telegram Bot Token (from @BotFather)
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Developer Settings
DEVELOPER_ID=123456789
DEVELOPER_PASSWORD=Sacheex
DEVELOPER_MODE=true

# Bot Configuration
BOT_NAME=සමාලි
BOT_VERSION=1.1

# Web Server
PORT=8080
HOST=0.0.0.0

# Rate Limits
MAX_DAILY_LOVE=15
MAX_DAILY_TRAUMA=2
AFFECTION_COOLDOWN=300
TRAUMA_COOLDOWN=1800
JEALOUSY_COOLDOWN=600
PROPOSAL_COOLDOWN=3600
"""
            with open(".env", "w", encoding="utf-8") as f:
                f.write(env_content)
            print_colored("✅ Basic .env created", "green")
            print_colored("⚠️  MUST edit .env with your actual tokens!", "red")
    
    # Check bot.json
    if not Path("config/bot.json").exists():
        print_colored("⚠️  bot.json not found!", "yellow")
        print_colored("📝 Creating bot.json...", "blue")
        
        bot_config = {
            "bot_metadata": {
                "bot_name": "සමාලි",
                "version": "1.1",
                "access_level": "Balanced Progression System"
            },
            "core_identity": {
                "bio": {
                    "full_name": "සමාලි කවිතා",
                    "age": 18,
                    "zodiac": "Taurus (වෘෂභ)",
                    "location": {
                        "district": "ත්‍රිකුණාමලය",
                        "nearest_town": "කන්තලේ",
                        "village": "ගල්මැටියාව",
                        "landmark": "ගල්මැටියාව හංදිය"
                    },
                    "voice_texture": "මෘදු, ගැමි සිංහල උච්චාරණය සහිත",
                    "physical_description": {
                        "hair": "දිගු කළු කෙස් කළඹ",
                        "eyes": "තද දුඹුරු, හැඟීම්බර ඇස් දෙකක්",
                        "scent": "නෙළුම් මල් සහ සබන් සුවඳ",
                        "clothing": "ගෙදරට ඉන්නකොට මල් හැඩ වැටුනු ගවුම"
                    }
                },
                "origin_story": {
                    "childhood": "ගල්මැටියාව වැව අද්දර හැදී වැඩුණි",
                    "trauma_trigger": "Abandonment"
                }
            },
            "comprehensive_stage_system": {
                "total_stages": 5,
                "logic": "Relationship cannot start before Stage 3. Progress is permanent.",
                "stages": {
                    "1_STRANGER": {"mood": "Reserved/Shy"},
                    "2_ACQUAINTANCE": {"mood": "Familiar/Curious"},
                    "3_CLOSE_FRIEND": {"mood": "Playful/Caring"},
                    "4_DEEP_AFFECTION": {"mood": "Deeply Loving"},
                    "5_ULTIMATE_YANDERE_QUEEN": {"mood": "Total Obsession"}
                }
            }
        }
        
        with open("config/bot.json", "w", encoding="utf-8") as f:
            json.dump(bot_config, f, ensure_ascii=False, indent=2)
        
        print_colored("✅ bot.json created", "green")
    
    return True

def install_dependencies():
    """Install Python dependencies"""
    print_colored("[4/6] Installing dependencies...", "cyan")
    
    try:
        # Update pip first
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], 
                      check=True, capture_output=True)
        
        # Install requirements
        result = subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                               capture_output=True, text=True)
        
        if result.returncode == 0:
            print_colored("✅ Dependencies installed successfully", "green")
            return True
        else:
            print_colored(f"❌ Failed to install dependencies:\n{result.stderr}", "red")
            return False
    except Exception as e:
        print_colored(f"❌ Installation error: {e}", "red")
        return False

def display_summary():
    """Display setup summary"""
    print_colored("[5/6] Setup Summary", "cyan")
    print_colored("=" * 50, "purple")
    
    # Python info
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    print_colored(f"🐍 Python Version: {py_version}", "blue")
    
    # File checks
    files = [
        (".env", "Environment Variables"),
        ("config/bot.json", "Bot Configuration"),
        ("requirements.txt", "Dependencies"),
        ("main.py", "Main Bot Code")
    ]
    
    for file_path, description in files:
        if Path(file_path).exists():
            print_colored(f"✅ {description}: Found", "green")
        else:
            print_colored(f"❌ {description}: Missing", "red")
    
    # Directory checks
    print_colored("\n📁 Directories:", "blue")
    directories = ["config", "memory/users", "memory/backups"]
    for directory in directories:
        if Path(directory).exists():
            print_colored(f"  ✅ {directory}/", "green")
    
    print_colored("=" * 50, "purple")
    return True

def run_tests():
    """Run basic tests"""
    print_colored("[6/6] Running basic tests...", "cyan")
    
    tests_passed = 0
    total_tests = 3
    
    # Test 1: Import modules
    try:
        import telegram
        import flask
        import dotenv
        print_colored("✅ Imports: OK", "green")
        tests_passed += 1
    except ImportError as e:
        print_colored(f"❌ Imports failed: {e}", "red")
    
    # Test 2: Check config files
    if Path(".env").exists() and Path("config/bot.json").exists():
        print_colored("✅ Config files: OK", "green")
        tests_passed += 1
    else:
        print_colored("❌ Config files missing", "red")
    
    # Test 3: Check directories
    if all(Path(d).exists() for d in ["config", "memory"]):
        print_colored("✅ Directories: OK", "green")
        tests_passed += 1
    else:
        print_colored("❌ Directories missing", "red")
    
    print_colored(f"\n📊 Tests: {tests_passed}/{total_tests} passed", 
                 "green" if tests_passed == total_tests else "yellow")
    
    return tests_passed == total_tests

def main():
    """Main setup function"""
    print_colored("""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║   👑 සමාලි - Ultimate Yandere Queen Bot Setup           ║
║   🤖 Version 1.1 | Balanced Progression System           ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
""", "purple")
    
    steps = [
        ("Python Check", check_python),
        ("Create Directories", create_directories),
        ("Configuration Files", check_config_files),
        ("Install Dependencies", install_dependencies),
        ("Display Summary", display_summary),
        ("Run Tests", run_tests)
    ]
    
    success = True
    for step_name, step_func in steps:
        if not step_func():
            success = False
            print_colored(f"\n❌ Setup failed at: {step_name}", "red")
            break
    
    if success:
        print_colored("\n" + "=" * 60, "green")
        print_colored("🎉 SETUP COMPLETED SUCCESSFULLY!", "green")
        print_colored("=" * 60, "green")
        
        print_colored("\n📋 NEXT STEPS:", "cyan")
        print_colored("1. Edit .env file with your Telegram Bot Token", "blue")
        print_colored("2. Set your DEVELOPER_ID (your Telegram user ID)", "blue")
        print_colored("3. Optional: Customize config/bot.json", "blue")
        
        print_colored("\n🚀 START THE BOT:", "cyan")
        print_colored("  Linux/Mac: ./run.sh", "yellow")
        print_colored("  Windows: run.bat", "yellow")
        print_colored("  Or: python main.py", "yellow")
        
        print_colored("\n🔗 WEB INTERFACE:", "cyan")
        print_colored("  http://localhost:8080", "blue")
        print_colored("  http://localhost:8080/health", "blue")
        
        print_colored("\n🔑 DEVELOPER ACCESS:", "cyan")
        print_colored("  Password: Sacheex", "blue")
        print_colored("  Command: /dev_login pass:Sacheex", "blue")
        
        print_colored("\n💬 Happy chatting with සමාලි! 💖👑", "purple")
    else:
        print_colored("\n❌ SETUP FAILED", "red")
        print_colored("Please check the errors above and try again.", "yellow")
    
    return success

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print_colored("\n\n⏹️  Setup interrupted by user", "yellow")
        sys.exit(1)