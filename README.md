# ElliotOS 🤖

**Your Personal AI Assistant powered by Ollama**

ElliotOS is a comprehensive local AI assistant that integrates with multiple data sources to provide intelligent morning and evening summaries via Slack. It combines data from your calendar, emails, health metrics, productivity stats, news, and more to give you personalized insights and recommendations.

![ElliotOS Demo](https://img.shields.io/badge/Status-Fully%20Functional-brightgreen) ![Python](https://img.shields.io/badge/Python-3.8+-blue) ![Ollama](https://img.shields.io/badge/AI-Ollama%20Local-orange) ![Slack](https://img.shields.io/badge/Output-Slack-purple)

## 🌟 What ElliotOS Does

ElliotOS automatically generates **personalized daily summaries** by:

1. **🔄 Collecting Data** from 8+ sources (health, productivity, news, sports, etc.)
2. **🧠 AI Processing** with local Ollama (privacy-first) or cloud AI fallbacks
3. **📱 Slack Delivery** of beautiful morning and evening digests
4. **📊 Smart Insights** based on your actual usage patterns and data

### 🌅 Morning Digest Example

- Current time and personalized greeting
- Today's calendar events (if configured)
- Health check (sleep quality, fitness goals)
- Current productivity status
- Chelsea FC updates
- World news headlines
- Daily focus recommendations
- Motivational insights

### 🌙 Evening Digest Example

- Reflection on the day's activities
- Productivity and health summary
- Tomorrow's preview
- Wellness check and rest recommendations
- Sports and news recap
- Positive insights to end the day

## ✨ Key Features

### 🔒 **Privacy-First Design**

- **Local AI processing** with Ollama (no data leaves your machine)
- **Optional cloud fallbacks** (OpenAI/Anthropic) only if you configure them
- **Secure credential storage** in environment variables
- **No tracking or analytics** unless you enable them

### 📊 **Data Sources**

- **🍎 Apple Health/HealthKit**: Steps, sleep, activity rings, workouts
- **💻 macOS System Stats**: App usage, productivity metrics, system health
- **📅 Google Calendar**: Events, meetings, scheduling conflicts
- **📧 Gmail**: Unread emails, important messages, mentions
- **💬 Slack**: Messages, mentions, team activity across workspaces
- **🥗 MyFitnessPal**: Nutrition tracking, calories, meal logging
- **📰 News APIs**: World headlines, tech news, trending topics
- **⚽ Chelsea FC**: Match results, fixtures, team news, league position

### 🤖 **AI Integration**

- **Primary**: Ollama (local, private, fast)
- **Fallback 1**: OpenAI GPT (if configured)
- **Fallback 2**: Anthropic Claude (if configured)
- **Fallback 3**: Template responses (always works)

## 🚀 Quick Start

### Prerequisites

- **macOS** (for full functionality - some features work on other platforms)
- **Python 3.8+**
- **Ollama** installed and running locally
- **Slack workspace** with webhook or bot permissions

### 1. Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd elliotos

# Run the setup script (installs dependencies and creates directories)
python3 setup.py

# Or install manually:
pip3 install -r requirements.txt
```

### 2. Install and Setup Ollama

```bash
# Install Ollama (if not already installed)
curl -fsSL https://ollama.ai/install.sh | sh

# Pull a recommended model
ollama pull mistral:latest
# OR
ollama pull llama3.1:8b

# Start Ollama (keep running in background)
ollama serve
```

### 3. Configure Environment Variables

Copy the example environment file and edit it:

```bash
cp env.example .env
nano .env  # or use your preferred editor
```

**Minimum required configuration:**

```bash
# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral:latest

# Slack Configuration (choose one method)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
# OR
SLACK_BOT_TOKENS=xoxb-your-bot-token

SLACK_SUMMARY_CHANNEL=#elliot-daily

# Schedule
MORNING_DIGEST_TIME=07:00
EVENING_DIGEST_TIME=21:00
```

### 4. Test the System

```bash
# Test data collection
python3 main.py --test-data

# Test Slack connection
python3 main.py --test-slack

# Test morning digest
python3 main.py --test-morning

# Check system status
python3 main.py --status
```

### 5. Run ElliotOS

```bash
# Start the scheduler (runs continuously)
python3 main.py

# Or run in background
nohup python3 main.py > elliotos.log 2>&1 &
```

## ⚙️ Configuration Guide

### 📁 Configuration Files

| File                 | Purpose             | Location       |
| -------------------- | ------------------- | -------------- |
| `.env`               | Main configuration  | Root directory |
| `config/settings.py` | Settings validation | Auto-loaded    |
| `logs/`              | Daily log files     | Auto-created   |
| `data/`              | Cached tokens/data  | Auto-created   |

### 🔧 Environment Variables

#### **Essential Settings**

```bash
# Ollama (Required)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral:latest  # or llama3.1:8b

# Slack (Required - choose one)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T.../B.../...
SLACK_BOT_TOKENS=xoxb-your-bot-token
SLACK_SUMMARY_CHANNEL=#elliot-daily

# Schedule (Required)
MORNING_DIGEST_TIME=07:00
EVENING_DIGEST_TIME=21:00
TIMEZONE=America/New_York
```

#### **Optional Integrations**

```bash
# Google Services
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GMAIL_ACCOUNTS=your-email@gmail.com,second@gmail.com

# Health & Fitness
MYFITNESSPAL_EMAIL=your_email@example.com
MYFITNESSPAL_PASSWORD=your_password
APPLE_HEALTH_ENABLED=true

# News & Sports
NEWS_API_KEY=your_newsapi_key
CHELSEA_FC_ENABLED=true
FOOTBALL_API_KEY=your_football_api_key

# Backup AI Services
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# Advanced Features
GITHUB_TOKEN=your_github_token
READWISE_TOKEN=your_readwise_token
NOTION_TOKEN=your_notion_token
```

#### **System Settings**

```bash
# Application Settings
LOG_LEVEL=INFO
DATA_RETENTION_DAYS=30
ENABLE_ANALYTICS=true
ENABLE_WEB_DASHBOARD=false

# macOS Features
MACOS_SCREEN_TIME_ENABLED=true
MACOS_APP_USAGE_ENABLED=true
```

## 🔗 Integration Setup

### 📱 Slack Integration

#### Option 1: Webhook (Easiest)

1. Go to your Slack workspace settings
2. Create a new webhook for your channel
3. Add `SLACK_WEBHOOK_URL` to `.env`

#### Option 2: Bot Token (More Features)

1. Create a Slack app at [api.slack.com](https://api.slack.com/apps)
2. Add bot token scopes: `chat:write`, `channels:read`, `users:read`
3. Install the app to your workspace
4. Add `SLACK_BOT_TOKENS` to `.env`

### 📅 Google Calendar & Gmail

1. **Create Google Cloud Project**:

   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project
   - Enable Calendar API and Gmail API

2. **Create OAuth Credentials**:

   - Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client IDs"
   - Application type: "Desktop application"
   - Download the JSON file

3. **Configure Environment**:
   ```bash
   GOOGLE_CLIENT_ID=your_client_id
   GOOGLE_CLIENT_SECRET=your_client_secret
   GMAIL_ACCOUNTS=your-email@gmail.com
   ```

### 📰 News Integration

1. Get a free API key from [NewsAPI.org](https://newsapi.org)
2. Add to `.env`:
   ```bash
   NEWS_API_KEY=your_newsapi_key
   ```

### 🍎 Health Data (macOS)

ElliotOS automatically integrates with:

- **Apple Health** (via HealthKit framework)
- **macOS Screen Time** (via system APIs)
- **Activity Monitor** (for app usage tracking)

No additional setup required on macOS.

## 🎮 Usage

### Command Line Options

```bash
# Run scheduled digests
python3 main.py

# Test individual components
python3 main.py --test-morning     # Test morning digest
python3 main.py --test-evening     # Test evening digest
python3 main.py --test-data        # Test data aggregation
python3 main.py --test-slack       # Test Slack connection

# System information
python3 main.py --status           # Show system status
```

### Manual Testing

```bash
# Test individual modules
python3 backend/fetch_calendar.py
python3 backend/fetch_health.py
python3 backend/fetch_slack.py

# Test data aggregation
python3 data_aggregator.py

# Test Slack bot
python3 -c "from slack_bot.bot import slack_bot; slack_bot.post_custom_message('Test message')"
```

## 📁 Project Structure

```
elliotos/
├── backend/                 # Data fetching modules
│   ├── fetch_calendar.py   # Google Calendar integration
│   ├── fetch_gmail.py      # Gmail integration
│   ├── fetch_slack.py      # Slack integration
│   ├── fetch_health.py     # Apple Health integration
│   ├── fetch_mac_stats.py  # macOS system stats
│   ├── fetch_nutrition.py  # MyFitnessPal integration
│   ├── fetch_news.py       # News aggregation
│   ├── fetch_chelsea.py    # Chelsea FC data
│   └── ollama_client.py    # AI integration
├── slack_bot/              # Slack integration
│   └── bot.py             # Slack bot implementation
├── config/                 # Configuration management
│   └── settings.py        # Settings and validation
├── utils/                  # Utilities
│   └── logger.py          # Logging system
├── logs/                   # Daily log files
├── data/                   # Cached data and tokens
├── data_aggregator.py      # Data aggregation engine
├── main.py                # Main orchestrator
├── setup.py               # Setup script
├── requirements.txt        # Python dependencies
├── .env                   # Your configuration (create from env.example)
└── README.md              # This file
```

## 🔍 Troubleshooting

### Common Issues

**1. Ollama Connection Failed**

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama if needed
ollama serve

# Pull the model if missing
ollama pull mistral:latest
```

**2. Slack Messages Not Posting**

```bash
# Test Slack connection
python3 main.py --test-slack

# Check webhook URL or bot token in .env
# Verify channel permissions
```

**3. Environment Variables Not Loading**

```bash
# Ensure .env file exists (not env)
ls -la .env

# Check file format (one variable per line)
cat .env | head -5

# Verify no extra spaces or characters
```

**4. Google APIs Not Working**

```bash
# Check credentials in .env file
# Verify APIs are enabled in Google Cloud Console
# Check OAuth consent screen configuration
```

**5. Health Data Not Available**

```bash
# Ensure running on macOS
# Check privacy permissions in System Preferences
# Verify HealthKit access if using Apple Health
```

### Debug Mode

Enable detailed logging:

```bash
LOG_LEVEL=DEBUG python3 main.py
```

Check log files:

```bash
tail -f logs/elliotos_$(date +%Y%m%d).log
```

## 🔄 Automation

### Run as Service (macOS)

Create a LaunchAgent:

```bash
# Create service file
cat > ~/Library/LaunchAgents/com.elliotos.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.elliotos</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/path/to/elliotos/main.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/path/to/elliotos</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
EOF

# Load the service
launchctl load ~/Library/LaunchAgents/com.elliotos.plist
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

## 🛡️ Privacy & Security

- **Local Processing**: All AI processing happens locally via Ollama
- **Secure Storage**: Credentials stored in environment variables
- **Data Retention**: Configurable data retention policies
- **Privacy First**: Health and personal data never leaves your machine
- **Optional Cloud**: Only uses cloud APIs you explicitly configure

## 📊 Feature Status

| Feature              | Status       | Configuration Required    |
| -------------------- | ------------ | ------------------------- |
| 🤖 AI Processing     | ✅ Working   | Ollama setup              |
| 📱 Slack Integration | ✅ Working   | Webhook or bot token      |
| 💻 macOS Stats       | ✅ Working   | None (automatic)          |
| 🍎 Apple Health      | ✅ Working   | None (automatic on macOS) |
| ⚽ Chelsea FC        | ✅ Working   | None (uses mock data)     |
| 📰 News              | ⚠️ Mock Data | NewsAPI key for real data |
| 📅 Google Calendar   | ⚠️ Optional  | Google API credentials    |
| 📧 Gmail             | ⚠️ Optional  | Google API credentials    |
| 🥗 MyFitnessPal      | ⚠️ Optional  | Login credentials         |
| 💬 Slack Messages    | ⚠️ Limited   | Proper bot tokens         |

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

### Development Setup

```bash
# Install development dependencies
pip install -r requirements.txt
pip install pytest black flake8

# Run tests
pytest tests/

# Format code
black .

# Lint code
flake8 .
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Ollama** for local AI inference
- **Slack** for communication platform
- **Google** for Calendar and Gmail APIs
- **Apple** for HealthKit and macOS integration
- **NewsAPI** for news aggregation
- **Football-Data.org** for sports data

---

**ElliotOS** - Your personal AI assistant that respects your privacy while keeping you informed and productive. 🚀

## 📞 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review the logs in `logs/elliotos_YYYYMMDD.log`
3. Test individual components with `--test-*` flags
4. Ensure all required environment variables are set

For questions or feature requests, please open an issue in the repository.

