@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

:: ==============================================
:: සමාලි යන්ඩෙරේ බොට් Startup Script
:: ==============================================

:: Colors
set "RED=[91m"
set "GREEN=[92m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "PURPLE=[95m"
set "CYAN=[96m"
set "NC=[0m"

:: Banner
echo %PURPLE%
echo ╔══════════════════════════════════════════════════════════╗
echo ║                                                          ║
echo ║   👑 සමාලි - Ultimate Yandere Queen Bot                 ║
echo ║   🤖 Version 1.1 ^| Balanced Progression System           ║
echo ║                                                          ║
echo ╚══════════════════════════════════════════════════════════╝
echo %NC%

:: Check Python
echo %CYAN%[1/5] Checking Python version...%NC%
python --version > nul 2>&1
if errorlevel 1 (
    echo %RED%❌ Python not found! Please install Python 3.8+%NC%
    pause
    exit /b 1
)
python -c "import sys; print('✅ Python {}.{}.{} found'.format(*sys.version_info[:3]))"
if errorlevel 1 (
    echo %RED%❌ Failed to check Python version%NC%
    pause
    exit /b 1
)

:: Check .env file
echo %CYAN%[2/5] Checking configuration...%NC%
if not exist ".env" (
    echo %YELLOW%⚠️  .env file not found!%NC%
    if exist ".env.example" (
        echo %BLUE%📝 Creating .env from template...%NC%
        copy ".env.example" ".env" > nul
        echo %YELLOW%⚠️  Please edit .env file with your tokens!%NC%
        echo %YELLOW%   Required: TELEGRAM_BOT_TOKEN and DEVELOPER_ID%NC%
        pause
        exit /b 1
    ) else (
        echo %YELLOW%📝 Creating basic .env file...%NC%
        (
            echo TELEGRAM_BOT_TOKEN=your_bot_token_here
            echo DEVELOPER_ID=123456789
            echo DEVELOPER_PASSWORD=Sacheex
            echo DEVELOPER_MODE=true
            echo BOT_NAME=සමාලි
            echo BOT_VERSION=1.1
            echo PORT=8080
        ) > .env
        echo %YELLOW%⚠️  Please edit .env file with your actual tokens!%NC%
        pause
        exit /b 1
    )
) else (
    echo %GREEN%✅ .env configuration found%NC%
)

:: Check bot.json
echo %CYAN%[3/5] Checking bot configuration...%NC%
if not exist "config\bot.json" (
    echo %RED%❌ config\bot.json not found!%NC%
    echo %BLUE%📝 Creating minimal bot.json...%NC%
    if not exist "config" mkdir config
    (
        echo {
        echo   "bot_metadata": {
        echo     "bot_name": "සමාලි",
        echo     "version": "1.1",
        echo     "access_level": "Balanced Progression System"
        echo   },
        echo   "core_identity": {
        echo     "bio": {
        echo       "full_name": "සමාලි කවිතා",
        echo       "age": 18,
        echo       "zodiac": "Taurus ^(වෘෂභ^)",
        echo       "voice_texture": "මෘදු, ගැමි සිංහල"
        echo     },
        echo     "origin_story": {
        echo       "trauma_trigger": "Abandonment"
        echo     }
        echo   }
        echo }
    ) > config\bot.json
    echo %YELLOW%⚠️  Created minimal bot.json. Consider updating it.%NC%
)
echo %GREEN%✅ bot.json configuration found%NC%

:: Install dependencies
echo %CYAN%[4/5] Installing dependencies...%NC%
pip install -r requirements.txt --upgrade
if errorlevel 1 (
    echo %RED%❌ Failed to install dependencies%NC%
    pause
    exit /b 1
)
echo %GREEN%✅ Dependencies installed%NC%

:: Create necessary directories
echo %CYAN%[5/5] Setting up directories...%NC%
if not exist "memory\users" mkdir memory\users
if not exist "memory\habits" mkdir memory\habits
if not exist "memory\backups" mkdir memory\backups
if not exist "memory\timeline" mkdir memory\timeline
if not exist "config" mkdir config
echo %GREEN%✅ Directories created%NC%

:: Display configuration
echo.
echo %PURPLE%══════════════════════════════════════════════════════════%NC%
echo %CYAN%📋 Configuration Summary:%NC%
echo %PURPLE%══════════════════════════════════════════════════════════%NC%
for /f "tokens=2 delims= " %%i in ('python -c "import sys; print(sys.version.split()[0])"') do set "PYVER=%%i"
echo %BLUE%• Python:%NC% !PYVER!
echo %BLUE%• Bot Name:%NC% සමාලි
echo %BLUE%• Version:%NC% 1.1
echo %BLUE%• Features:%NC% Balanced Progression, Daily Limits, Cooldowns
echo %BLUE%• Developer Password:%NC% Sacheex
echo %BLUE%• Web Interface:%NC% http://localhost:8080
echo %PURPLE%══════════════════════════════════════════════════════════%NC%

:: Start the bot
echo.
echo %GREEN%🚀 Starting සමාලි bot...%NC%
echo %YELLOW%📱 Connect on Telegram and start chatting!%NC%
echo %CYAN%🛑 Press Ctrl+C to stop the bot%NC%
echo %PURPLE%══════════════════════════════════════════════════════════%NC%
echo.

:: Run the bot
python main.py

:: Keep window open if error
if errorlevel 1 pause