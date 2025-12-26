#!/bin/bash

# ==============================================
# සමාලි යන්ඩෙරේ බොට් Startup Script
# ==============================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Banner
echo -e "${PURPLE}"
echo "╔══════════════════════════════════════════════════════════╗"
echo "║                                                          ║"
echo "║   👑 සමාලි - Ultimate Yandere Queen Bot                 ║"
echo "║   🤖 Version 1.1 | Balanced Progression System           ║"
echo "║                                                          ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check Python version
echo -e "${CYAN}[1/5] Checking Python version...${NC}"
python_version=$(python3 --version 2>&1 | awk '{print $2}')
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Python3 not found! Please install Python 3.8+${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python $python_version found${NC}"

# Check .env file
echo -e "${CYAN}[2/5] Checking configuration...${NC}"
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found!${NC}"
    if [ -f ".env.example" ]; then
        echo -e "${BLUE}📝 Creating .env from template...${NC}"
        cp .env.example .env
        echo -e "${YELLOW}⚠️  Please edit .env file with your tokens!${NC}"
        echo -e "${YELLOW}   Required: TELEGRAM_BOT_TOKEN and DEVELOPER_ID${NC}"
        exit 1
    else
        echo -e "${YELLOW}📝 Creating basic .env file...${NC}"
        cat > .env << EOF
TELEGRAM_BOT_TOKEN=your_bot_token_here
DEVELOPER_ID=123456789
DEVELOPER_PASSWORD=Sacheex
DEVELOPER_MODE=true
BOT_NAME=සමාලි
BOT_VERSION=1.1
PORT=8080
EOF
        echo -e "${YELLOW}⚠️  Please edit .env file with your actual tokens!${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ .env configuration found${NC}"
fi

# Check bot.json
echo -e "${CYAN}[3/5] Checking bot configuration...${NC}"
if [ ! -f "config/bot.json" ]; then
    echo -e "${RED}❌ config/bot.json not found!${NC}"
    echo -e "${BLUE}📝 Creating minimal bot.json...${NC}"
    mkdir -p config
    cat > config/bot.json << EOF
{
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
      "voice_texture": "මෘදු, ගැමි සිංහල"
    },
    "origin_story": {
      "trauma_trigger": "Abandonment"
    }
  }
}
EOF
    echo -e "${YELLOW}⚠️  Created minimal bot.json. Consider updating it.${NC}"
fi
echo -e "${GREEN}✅ bot.json configuration found${NC}"

# Install dependencies
echo -e "${CYAN}[4/5] Installing dependencies...${NC}"
pip install -r requirements.txt --upgrade
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to install dependencies${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Dependencies installed${NC}"

# Create necessary directories
echo -e "${CYAN}[5/5] Setting up directories...${NC}"
mkdir -p memory/users memory/habits memory/backups memory/timeline config
echo -e "${GREEN}✅ Directories created${NC}"

# Display configuration
echo -e "\n${PURPLE}══════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}📋 Configuration Summary:${NC}"
echo -e "${PURPLE}══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}• Python:${NC} $python_version"
echo -e "${BLUE}• Bot Name:${NC} සමාලි"
echo -e "${BLUE}• Version:${NC} 1.1"
echo -e "${BLUE}• Features:${NC} Balanced Progression, Daily Limits, Cooldowns"
echo -e "${BLUE}• Developer Password:${NC} Sacheex"
echo -e "${BLUE}• Web Interface:${NC} http://localhost:8080"
echo -e "${PURPLE}══════════════════════════════════════════════════════════${NC}"

# Start the bot
echo -e "\n${GREEN}🚀 Starting සමාලි bot...${NC}"
echo -e "${YELLOW}📱 Connect on Telegram and start chatting!${NC}"
echo -e "${CYAN}🛑 Press Ctrl+C to stop the bot${NC}"
echo -e "${PURPLE}══════════════════════════════════════════════════════════${NC}\n"

# Run the bot
python3 main.py