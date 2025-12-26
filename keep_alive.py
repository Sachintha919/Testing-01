"""
🌐 Web Server for Replit Uptime
මෙම file එක main.py සමඟ එක්ක භාවිතා කරන්න
"""
from flask import Flask, jsonify
from threading import Thread
import os
import time
import json
from datetime import datetime

app = Flask(__name__)

# Read bot configuration
try:
    with open("config/bot.json", "r", encoding="utf-8") as f:
        bot_config = json.load(f)
    bot_name = bot_config["bot_metadata"]["bot_name"]
    bot_version = bot_config["bot_metadata"]["version"]
except:
    bot_name = "සමාලි"
    bot_version = "1.1"

# Statistics
start_time = time.time()
request_count = 0

@app.route('/')
def home():
    global request_count
    request_count += 1
    
    uptime_seconds = time.time() - start_time
    uptime_str = format_uptime(uptime_seconds)
    
    return f"""
    <!DOCTYPE html>
    <html lang="si">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{bot_name} - Yandere Queen Bot</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 20px;
            }}
            
            .container {{
                background: rgba(0, 0, 0, 0.85);
                padding: 40px;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
                max-width: 900px;
                width: 100%;
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.1);
            }}
            
            .header {{
                text-align: center;
                margin-bottom: 30px;
            }}
            
            .emoji {{
                font-size: 4em;
                margin-bottom: 10px;
            }}
            
            h1 {{
                color: #ff6b8b;
                font-size: 2.8em;
                margin-bottom: 10px;
                text-shadow: 0 2px 10px rgba(255, 107, 139, 0.5);
            }}
            
            .subtitle {{
                color: #aaa;
                font-size: 1.2em;
                margin-bottom: 30px;
            }}
            
            .status-card {{
                background: rgba(255, 255, 255, 0.1);
                padding: 25px;
                border-radius: 15px;
                margin-bottom: 30px;
                border-left: 5px solid #ff6b8b;
            }}
            
            .status-title {{
                display: flex;
                align-items: center;
                gap: 10px;
                margin-bottom: 15px;
                font-size: 1.4em;
            }}
            
            .status-badge {{
                background: #4CAF50;
                color: white;
                padding: 5px 15px;
                border-radius: 20px;
                font-size: 0.8em;
                font-weight: bold;
            }}
            
            .stats-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin: 30px 0;
            }}
            
            .stat-box {{
                background: rgba(255, 255, 255, 0.08);
                padding: 20px;
                border-radius: 10px;
                text-align: center;
                transition: transform 0.3s ease;
            }}
            
            .stat-box:hover {{
                transform: translateY(-5px);
                background: rgba(255, 255, 255, 0.12);
            }}
            
            .stat-value {{
                font-size: 2em;
                font-weight: bold;
                color: #ff6b8b;
                margin-bottom: 5px;
            }}
            
            .stat-label {{
                color: #aaa;
                font-size: 0.9em;
            }}
            
            .info-section {{
                margin-top: 30px;
                background: rgba(255, 255, 255, 0.05);
                padding: 25px;
                border-radius: 15px;
            }}
            
            h2 {{
                color: #ff6b8b;
                margin-bottom: 15px;
                font-size: 1.6em;
            }}
            
            .info-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
            }}
            
            .info-item {{
                margin-bottom: 15px;
            }}
            
            .info-label {{
                color: #ff6b8b;
                font-weight: bold;
                margin-bottom: 5px;
            }}
            
            .warning {{
                background: rgba(255, 107, 139, 0.1);
                border: 1px solid rgba(255, 107, 139, 0.3);
                padding: 15px;
                border-radius: 10px;
                margin-top: 20px;
                color: #ffb3c1;
            }}
            
            .footer {{
                text-align: center;
                margin-top: 40px;
                color: #777;
                font-size: 0.9em;
                border-top: 1px solid rgba(255, 255, 255, 0.1);
                padding-top: 20px;
            }}
            
            @media (max-width: 768px) {{
                .container {{
                    padding: 20px;
                }}
                
                h1 {{
                    font-size: 2em;
                }}
                
                .stats-grid {{
                    grid-template-columns: 1fr;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="emoji">👑</div>
                <h1>{bot_name}</h1>
                <div class="subtitle">Ultimate Yandere Queen Bot v{bot_version}</div>
            </div>
            
            <div class="status-card">
                <div class="status-title">
                    <span>🟢 Bot Status</span>
                    <span class="status-badge">ACTIVE</span>
                </div>
                <p>සමාලි යන්ඩෙරේ බොට් සක්‍රීයව ක්‍රියාත්මක වෙමින් පවතී. Telegram හරහා කතාබහ කළ හැකිය.</p>
            </div>
            
            <div class="stats-grid">
                <div class="stat-box">
                    <div class="stat-value">{uptime_str}</div>
                    <div class="stat-label">Uptime</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value">{request_count}</div>
                    <div class="stat-label">Total Requests</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value">5</div>
                    <div class="stat-label">Relationship Stages</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value">සිංහල</div>
                    <div class="stat-label">Language</div>
                </div>
            </div>
            
            <div class="info-section">
                <h2>🤖 Bot Information</h2>
                <div class="info-grid">
                    <div class="info-item">
                        <div class="info-label">Full Name</div>
                        <div>සමාලි කවිතා</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Age</div>
                        <div>18 years</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Hometown</div>
                        <div>ගල්මැටියාව, කන්තලේ</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Personality</div>
                        <div>Yandere (Obsessive Love)</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Zodiac</div>
                        <div>වෘෂභ (Taurus)</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Dialect</div>
                        <div>ගැමි ව්‍යවහාරය</div>
                    </div>
                </div>
                
                <div class="warning">
                    ⚠️ <strong>Content Warning:</strong> This bot exhibits yandere (obsessive love) behavior patterns. 
                    Stage 5 contains psychological manipulation themes. This is a fictional AI character.
                </div>
            </div>
            
            <div class="info-section">
                <h2>🎮 Stage System</h2>
                <div class="info-grid">
                    <div class="info-item">
                        <div class="info-label">1. STRANGER</div>
                        <div>අඩුම අදියර</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">2. ACQUAINTANCE</div>
                        <div>හොඳ හැඟීම</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">3. CLOSE FRIEND</div>
                        <div>මිතුරා</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">4. DEEP AFFECTION</div>
                        <div>ගැඹුරු ආදරය</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">5. 🔴 YANDERE QUEEN</div>
                        <div>සම්පූර්ණ අයිතිය</div>
                    </div>
                </div>
            </div>
            
            <div class="footer">
                <p>🤖 Telegram Bot | 👑 Yandere Queen Edition | 🧠 Advanced AI System</p>
                <p>Server Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        </div>
    </body>
    </html>
    """

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": bot_name,
        "version": bot_version,
        "uptime": time.time() - start_time,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/status')
def status():
    """Detailed status"""
    return jsonify({
        "bot": {
            "name": bot_name,
            "version": bot_version,
            "status": "running"
        },
        "server": {
            "uptime": time.time() - start_time,
            "requests": request_count,
            "timestamp": datetime.now().isoformat()
        },
        "features": {
            "stages": 5,
            "language": "Sinhala",
            "memory": "JSON-based",
            "authentication": "Password-protected"
        }
    })

@app.route('/ping')
def ping():
    """Simple ping endpoint"""
    return "pong"

@app.route('/api/users/count')
def user_count():
    """Count users from memory files"""
    try:
        user_dir = "memory/users"
        if os.path.exists(user_dir):
            user_files = [f for f in os.listdir(user_dir) if f.endswith('.json')]
            return jsonify({
                "count": len(user_files),
                "users": user_files[:10]  # First 10 files
            })
        return jsonify({"count": 0, "users": []})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def format_uptime(seconds):
    """Format uptime to human readable format"""
    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    
    if days > 0:
        return f"{days}d {hours}h"
    elif hours > 0:
        return f"{hours}h {minutes}m"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"

def run():
    """Start Flask server"""
    port = int(os.environ.get("PORT", 8080))
    host = os.environ.get("HOST", "0.0.0.0")
    print(f"🌐 Starting web server on {host}:{port}")
    app.run(host=host, port=port, debug=False)

def keep_alive():
    """Start web server in background thread"""
    server_thread = Thread(target=run, daemon=True)
    server_thread.start()
    print(f"✅ Web server started in background thread")
    print(f"📊 Dashboard available at: http://localhost:8080")
    print(f"🩺 Health check: http://localhost:8080/health")
    print(f"📈 Status: http://localhost:8080/status")
    
    return server_thread

if __name__ == "__main__":
    keep_alive()
    # Keep the main thread alive
    while True:
        time.sleep(1)