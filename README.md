# ElliotOS 🤖

**Your Personal AI Assistant powered by Ollama**

ElliotOS is a comprehensive local AI assistant that integrates with multiple data sources to provide intelligent morning and evening summaries via Slack. It combines data from your calendar, emails, health metrics, productivity stats, news, and more to give you personalized insights and recommendations.

## ✨ Features

### 🌅 Morning Digest

- **Calendar Overview**: Today's events, conflicts, and meeting URLs
- **Health Check**: Sleep quality, activity goals, and wellness insights
- **Communication Summary**: Unread emails, Slack mentions, and priority messages
- **News Briefing**: Top headlines, tech news, and trending topics
- **Sports Updates**: Chelsea FC fixtures, results, and team news
- **Productivity Focus**: Daily goals and motivational insights

### 🌙 Evening Digest

- **Daily Accomplishments**: What you achieved today
- **Health Summary**: Steps, activity rings, nutrition tracking
- **Productivity Review**: Focus score, app usage, and screen time
- **Tomorrow's Preview**: Upcoming events and preparation needed
- **Wellness Check**: Stress levels and rest recommendations
- **Reflection**: Positive insights to end the day

### 📊 Data Sources

- **Google Calendar & Gmail**: Events, emails, and scheduling
- **Slack Workspaces**: Messages, mentions, and team activity
- **Apple Health/HealthKit**: Steps, sleep, heart rate, and activity rings
- **macOS System Stats**: App usage, productivity metrics, and system health
- **MyFitnessPal**: Nutrition tracking, calories, and meal logging
- **News APIs**: World headlines, tech news, and trending topics
- **Chelsea FC**: Match results, fixtures, and team updates

## 🚀 Quick Start

### Prerequisites

- **macOS** (for full functionality)
- **Python 3.8+**
- **Ollama** installed and running locally
- **Slack workspace** with bot permissions

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd elliotos

# Install dependencies
pip install -r requirements.txt

# Create your environment file
cp env.example .env
```

### 2. Configuration

Edit your `.env` file with your credentials:

```bash
# Essential Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b

# Slack (choose one method)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
# OR
SLACK_BOT_TOKENS=xoxb-your-bot-token

SLACK_SUMMARY_CHANNEL=#elliot-daily

# Schedule
MORNING_DIGEST_TIME=07:00
EVENING_DIGEST_TIME=21:00
```

### 3. Setup Ollama

```bash
# Install Ollama (if not already installed)
curl -fsSL https://ollama.ai/install.sh | sh

# Pull the recommended model
ollama pull llama3.1:8b

# Start Ollama (if not running)
ollama serve
```

### 4. Test the System

```bash
# Test data aggregation
python main.py --test-data

# Test Slack connection
python main.py --test-slack

# Test morning digest
python main.py --test-morning

# Check system status
python main.py --status
```

### 5. Run ElliotOS

```bash
# Start the scheduler (runs continuously)
python main.py

# Or run in background
nohup python main.py > elliotos.log 2>&1 &
```

## ⚙️ Advanced Configuration

### Google Services (Calendar & Gmail)

1. **Create Google Cloud Project**:

   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing
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

### Slack Integration

#### Option 1: Webhook (Easiest)

1. Go to your Slack workspace settings
2. Create a new webhook for your channel
3. Add the webhook URL to your `.env` file

#### Option 2: Bot Token (More Features)

1. Create a Slack app at [api.slack.com](https://api.slack.com/apps)
2. Add bot token scopes: `chat:write`, `channels:read`, `users:read`
3. Install the app to your workspace
4. Add the bot token to your `.env` file

### Health Data (macOS)

ElliotOS automatically integrates with:

- **Apple Health** (via HealthKit framework)
- **macOS Screen Time** (via system APIs)
- **Activity Monitor** (for app usage tracking)

No additional setup required on macOS.

### News & Sports

```bash
# Get NewsAPI key (free tier available)
NEWS_API_KEY=your_newsapi_key

# Optional: Football API for detailed Chelsea stats
FOOTBALL_API_KEY=your_football_api_key

# Enable/disable features
CHELSEA_FC_ENABLED=true
```

### MyFitnessPal Integration

```bash
MYFITNESSPAL_EMAIL=your_email
MYFITNESSPAL_PASSWORD=your_password
```

**Note**: This uses web scraping. Consider using official APIs when available.

## 🔧 Usage

### Command Line Options

```bash
# Run scheduled digests
python main.py

# Test individual components
python main.py --test-morning     # Test morning digest
python main.py --test-evening     # Test evening digest
python main.py --test-data        # Test data aggregation
python main.py --test-slack       # Test Slack connection

# System information
python main.py --status           # Show system status
```

### Manual Testing

```bash
# Test individual modules
python backend/fetch_calendar.py
python backend/fetch_health.py
python backend/fetch_slack.py

# Test data aggregation
python data_aggregator.py

# Test Slack bot
python -c "from slack_bot.bot import slack_bot; slack_bot.post_custom_message('Test message')"
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
├── requirements.txt        # Python dependencies
└── env.example            # Environment template
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
ollama pull llama3.1:8b
```

**2. Slack Messages Not Posting**

```bash
# Test Slack connection
python main.py --test-slack

# Check webhook URL or bot token
# Verify channel permissions
```

**3. Google APIs Not Working**

```bash
# Check credentials in .env file
# Verify APIs are enabled in Google Cloud Console
# Check OAuth consent screen configuration
```

**4. Health Data Not Available**

```bash
# Ensure running on macOS
# Check privacy permissions in System Preferences
# Verify HealthKit access if using Apple Health
```

### Debug Mode

Enable detailed logging:

```bash
LOG_LEVEL=DEBUG python main.py
```

Check log files:

```bash
tail -f logs/elliotos_$(date +%Y%m%d).log
```

## 🛡️ Privacy & Security

- **Local Processing**: All AI processing happens locally via Ollama
- **Secure Storage**: Credentials stored in environment variables
- **Data Retention**: Configurable data retention policies
- **Privacy First**: Health and personal data never leaves your machine
- **Optional Cloud**: Only uses cloud APIs you explicitly configure

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
