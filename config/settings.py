"""
ElliotOS Configuration Settings
Centralized configuration management with environment variable support
"""

import os
from typing import List, Optional
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    """Main configuration class for ElliotOS"""
    
    # Project paths
    BASE_DIR = Path(__file__).parent.parent
    LOGS_DIR = BASE_DIR / "logs"
    DATA_DIR = BASE_DIR / "data"
    
    # Ollama Configuration
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
    
    # Google APIs
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI: str = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8080/callback")
    
    # Gmail accounts (comma-separated)
    @property
    def GMAIL_ACCOUNTS(self) -> List[str]:
        accounts = os.getenv("GMAIL_ACCOUNTS", "")
        return [acc.strip() for acc in accounts.split(",") if acc.strip()]
    
    # Slack Configuration
    @property
    def SLACK_BOT_TOKENS(self) -> List[str]:
        tokens = os.getenv("SLACK_BOT_TOKENS", "")
        return [token.strip() for token in tokens.split(",") if token.strip()]
    
    @property
    def SLACK_USER_TOKENS(self) -> List[str]:
        tokens = os.getenv("SLACK_USER_TOKENS", "")
        return [token.strip() for token in tokens.split(",") if token.strip()]
    
    SLACK_WEBHOOK_URL: str = os.getenv("SLACK_WEBHOOK_URL", "")
    SLACK_SUMMARY_CHANNEL: str = os.getenv("SLACK_SUMMARY_CHANNEL", "#elliot-daily")
    
    # Health & Fitness
    MYFITNESSPAL_EMAIL: str = os.getenv("MYFITNESSPAL_EMAIL", "")
    MYFITNESSPAL_PASSWORD: str = os.getenv("MYFITNESSPAL_PASSWORD", "")
    APPLE_HEALTH_ENABLED: bool = os.getenv("APPLE_HEALTH_ENABLED", "true").lower() == "true"
    
    # News & Sports
    NEWS_API_KEY: str = os.getenv("NEWS_API_KEY", "")
    CHELSEA_FC_ENABLED: bool = os.getenv("CHELSEA_FC_ENABLED", "true").lower() == "true"
    FOOTBALL_API_KEY: str = os.getenv("FOOTBALL_API_KEY", "")
    
    # Backup LLM Options
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    
    # Scheduling
    MORNING_DIGEST_TIME: str = os.getenv("MORNING_DIGEST_TIME", "07:00")
    EVENING_DIGEST_TIME: str = os.getenv("EVENING_DIGEST_TIME", "21:00")
    TIMEZONE: str = os.getenv("TIMEZONE", "America/New_York")
    
    # Advanced Features
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
    GITHUB_USERNAME: str = os.getenv("GITHUB_USERNAME", "")
    READWISE_TOKEN: str = os.getenv("READWISE_TOKEN", "")
    NOTION_TOKEN: str = os.getenv("NOTION_TOKEN", "")
    NOTION_DATABASE_ID: str = os.getenv("NOTION_DATABASE_ID", "")
    
    # Application Settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    DATA_RETENTION_DAYS: int = int(os.getenv("DATA_RETENTION_DAYS", "30"))
    ENABLE_ANALYTICS: bool = os.getenv("ENABLE_ANALYTICS", "true").lower() == "true"
    ENABLE_WEB_DASHBOARD: bool = os.getenv("ENABLE_WEB_DASHBOARD", "false").lower() == "true"
    
    # macOS Features
    MACOS_SCREEN_TIME_ENABLED: bool = os.getenv("MACOS_SCREEN_TIME_ENABLED", "true").lower() == "true"
    MACOS_APP_USAGE_ENABLED: bool = os.getenv("MACOS_APP_USAGE_ENABLED", "true").lower() == "true"
    
    def __init__(self):
        """Initialize settings and create necessary directories"""
        self.LOGS_DIR.mkdir(exist_ok=True)
        self.DATA_DIR.mkdir(exist_ok=True)
        
    def validate_config(self) -> List[str]:
        """Validate required configuration and return list of missing items"""
        missing = []
        
        if not self.OLLAMA_BASE_URL:
            missing.append("OLLAMA_BASE_URL")
            
        if not self.SLACK_WEBHOOK_URL and not self.SLACK_BOT_TOKENS:
            missing.append("SLACK_WEBHOOK_URL or SLACK_BOT_TOKENS")
            
        return missing
    
    def get_feature_status(self) -> dict:
        """Get status of all optional features"""
        return {
            "google_calendar": bool(self.GOOGLE_CLIENT_ID and self.GOOGLE_CLIENT_SECRET),
            "gmail": bool(self.GMAIL_ACCOUNTS),
            "slack": bool(self.SLACK_BOT_TOKENS or self.SLACK_WEBHOOK_URL),
            "myfitnesspal": bool(self.MYFITNESSPAL_EMAIL and self.MYFITNESSPAL_PASSWORD),
            "apple_health": self.APPLE_HEALTH_ENABLED,
            "news": bool(self.NEWS_API_KEY),
            "chelsea_fc": self.CHELSEA_FC_ENABLED,
            "github": bool(self.GITHUB_TOKEN),
            "readwise": bool(self.READWISE_TOKEN),
            "notion": bool(self.NOTION_TOKEN),
            "macos_tracking": self.MACOS_APP_USAGE_ENABLED,
        }

# Global settings instance
settings = Settings() 