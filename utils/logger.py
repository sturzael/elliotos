"""
ElliotOS Logging Utility
Provides centralized logging with rich formatting and file output
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
from rich.logging import RichHandler
from rich.console import Console
from rich.theme import Theme

from config.settings import settings

# Custom theme for ElliotOS
elliot_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "bold red",
    "critical": "bold white on red",
    "success": "bold green",
    "debug": "dim blue",
})

console = Console(theme=elliot_theme)

class ElliotLogger:
    """Enhanced logger for ElliotOS with file and console output"""
    
    def __init__(self, name: str = "elliotos"):
        self.name = name
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
        
        # Prevent duplicate handlers
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """Set up console and file handlers"""
        
        # Rich console handler
        console_handler = RichHandler(
            console=console,
            show_time=True,
            show_path=False,
            markup=True,
            rich_tracebacks=True
        )
        console_handler.setLevel(logging.INFO)
        
        # File handler - daily log files
        log_file = settings.LOGS_DIR / f"elliotos_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        
        # Formatters
        console_format = logging.Formatter("%(message)s")
        file_format = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        
        console_handler.setFormatter(console_format)
        file_handler.setFormatter(file_format)
        
        # Add handlers
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        self.logger.info(f"[info]{message}[/info]", **kwargs)
    
    def success(self, message: str, **kwargs):
        """Log success message"""
        self.logger.info(f"[success]✅ {message}[/success]", **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self.logger.warning(f"[warning]⚠️  {message}[/warning]", **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message"""
        self.logger.error(f"[error]❌ {message}[/error]", **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message"""
        self.logger.critical(f"[critical]🚨 {message}[/critical]", **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self.logger.debug(f"[debug]🔍 {message}[/debug]", **kwargs)
    
    def module_start(self, module_name: str):
        """Log module start"""
        self.info(f"🚀 Starting {module_name}")
    
    def module_complete(self, module_name: str, duration: Optional[float] = None):
        """Log module completion"""
        duration_str = f" ({duration:.2f}s)" if duration else ""
        self.success(f"✨ Completed {module_name}{duration_str}")
    
    def data_fetched(self, source: str, count: int):
        """Log successful data fetch"""
        self.success(f"📊 Fetched {count} items from {source}")
    
    def api_error(self, service: str, error: str):
        """Log API error"""
        self.error(f"🌐 API Error - {service}: {error}")
    
    def feature_disabled(self, feature: str, reason: str = ""):
        """Log disabled feature"""
        reason_str = f": {reason}" if reason else ""
        self.warning(f"🔒 Feature disabled - {feature}{reason_str}")

# Global logger instance
logger = ElliotLogger()

def get_logger(name: str) -> ElliotLogger:
    """Get a logger instance for a specific module"""
    return ElliotLogger(name) 