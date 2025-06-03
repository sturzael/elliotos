#!/usr/bin/env python3
"""
ElliotOS Main Orchestrator
Schedules and runs morning and evening digests
"""

import sys
import time
import signal
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

import schedule
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from data_aggregator import fetch_all_data, fetch_essential_data, data_aggregator
from backend.ollama_client import ollama_client
from slack_bot.bot import slack_bot
from config.settings import settings
from utils.logger import get_logger

logger = get_logger("elliotos_main")

class ElliotOS:
    """Main ElliotOS orchestrator"""
    
    def __init__(self):
        self.scheduler = BlockingScheduler()
        self.running = False
        self.last_morning_digest = None
        self.last_evening_digest = None
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.stop()
    
    def start(self):
        """Start the ElliotOS scheduler"""
        
        logger.info("🚀 Starting ElliotOS...")
        
        # Validate configuration
        if not self._validate_config():
            logger.critical("Configuration validation failed. Please check your settings.")
            return False
        
        # Test connections
        self._test_connections()
        
        # Setup scheduled jobs
        self._setup_schedule()
        
        # Start the scheduler
        try:
            self.running = True
            logger.success("✨ ElliotOS is running! Waiting for scheduled tasks...")
            logger.info(f"Morning digest scheduled for: {settings.MORNING_DIGEST_TIME}")
            logger.info(f"Evening digest scheduled for: {settings.EVENING_DIGEST_TIME}")
            
            self.scheduler.start()
            
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
        finally:
            self.stop()
        
        return True
    
    def stop(self):
        """Stop the ElliotOS scheduler"""
        
        if self.running:
            logger.info("🛑 Stopping ElliotOS...")
            self.running = False
            
            if self.scheduler.running:
                self.scheduler.shutdown(wait=False)
            
            logger.success("✅ ElliotOS stopped successfully")
    
    def _validate_config(self) -> bool:
        """Validate ElliotOS configuration"""
        
        logger.info("Validating configuration...")
        
        missing_config = settings.validate_config()
        
        if missing_config:
            logger.error("Missing required configuration:")
            for item in missing_config:
                logger.error(f"  - {item}")
            return False
        
        # Check feature status
        feature_status = settings.get_feature_status()
        enabled_features = [k for k, v in feature_status.items() if v]
        
        logger.info(f"Enabled features: {', '.join(enabled_features)}")
        
        if len(enabled_features) < 2:
            logger.warning("Very few features enabled - consider configuring more data sources")
        
        return True
    
    def _test_connections(self):
        """Test connections to external services"""
        
        logger.info("Testing service connections...")
        
        # Test Ollama
        if ollama_client.check_availability():
            logger.success("✅ Ollama connection successful")
        else:
            logger.warning("⚠️ Ollama not available - will use fallback AI services")
        
        # Test Slack
        slack_status = slack_bot.test_connection()
        if slack_status["can_post"]:
            logger.success(f"✅ Slack connection successful ({slack_status['bot_clients']} bots, webhook: {slack_status['webhook_configured']})")
        else:
            logger.error("❌ No Slack posting method available")
        
        # Test data modules (quick check)
        try:
            essential_data = fetch_essential_data()
            successful_modules = len([k for k, v in essential_data.items() if not k.startswith("_") and not v.get("error")])
            logger.success(f"✅ Data modules: {successful_modules}/4 essential modules working")
        except Exception as e:
            logger.error(f"❌ Data module test failed: {e}")
    
    def _setup_schedule(self):
        """Setup scheduled jobs"""
        
        # Parse time settings
        morning_hour, morning_minute = map(int, settings.MORNING_DIGEST_TIME.split(":"))
        evening_hour, evening_minute = map(int, settings.EVENING_DIGEST_TIME.split(":"))
        
        # Schedule morning digest
        self.scheduler.add_job(
            func=self.run_morning_digest,
            trigger=CronTrigger(hour=morning_hour, minute=morning_minute),
            id='morning_digest',
            name='Morning Digest',
            misfire_grace_time=300  # 5 minutes grace period
        )
        
        # Schedule evening digest
        self.scheduler.add_job(
            func=self.run_evening_digest,
            trigger=CronTrigger(hour=evening_hour, minute=evening_minute),
            id='evening_digest',
            name='Evening Digest',
            misfire_grace_time=300  # 5 minutes grace period
        )
        
        # Schedule daily health check (noon)
        self.scheduler.add_job(
            func=self.run_health_check,
            trigger=CronTrigger(hour=12, minute=0),
            id='health_check',
            name='Daily Health Check'
        )
        
        logger.success("📅 Scheduled jobs configured")
    
    def run_morning_digest(self):
        """Run the morning digest"""
        
        logger.module_start("Morning Digest")
        
        try:
            # Fetch data
            logger.info("Fetching morning data...")
            context_data = fetch_all_data(parallel=True)
            
            # Generate AI digest
            logger.info("Generating morning digest...")
            digest_content = ollama_client.generate_morning_digest(context_data)
            
            # Post to Slack
            logger.info("Posting morning digest to Slack...")
            success = slack_bot.post_morning_digest(digest_content, context_data)
            
            if success:
                self.last_morning_digest = datetime.now()
                logger.success("✨ Morning digest completed successfully")
            else:
                logger.error("❌ Failed to post morning digest to Slack")
            
            # Log summary
            summary = data_aggregator.get_data_summary(context_data)
            logger.info(f"Data summary: {summary['successful_modules']}/{summary['total_modules']} modules successful")
            
        except Exception as e:
            logger.error(f"Morning digest failed: {e}")
        
        logger.module_complete("Morning Digest")
    
    def run_evening_digest(self):
        """Run the evening digest"""
        
        logger.module_start("Evening Digest")
        
        try:
            # Fetch data
            logger.info("Fetching evening data...")
            context_data = fetch_all_data(parallel=True)
            
            # Generate AI digest
            logger.info("Generating evening digest...")
            digest_content = ollama_client.generate_evening_digest(context_data)
            
            # Post to Slack
            logger.info("Posting evening digest to Slack...")
            success = slack_bot.post_evening_digest(digest_content, context_data)
            
            if success:
                self.last_evening_digest = datetime.now()
                logger.success("✨ Evening digest completed successfully")
            else:
                logger.error("❌ Failed to post evening digest to Slack")
            
            # Log summary
            summary = data_aggregator.get_data_summary(context_data)
            logger.info(f"Data summary: {summary['successful_modules']}/{summary['total_modules']} modules successful")
            
        except Exception as e:
            logger.error(f"Evening digest failed: {e}")
        
        logger.module_complete("Evening Digest")
    
    def run_health_check(self):
        """Run daily health check"""
        
        logger.module_start("Health Check")
        
        try:
            # Quick data fetch
            essential_data = fetch_essential_data()
            
            # Validate data quality
            validation = data_aggregator.validate_data_quality(essential_data)
            
            # Log status
            logger.info(f"System health: {validation['overall_quality']}")
            
            if validation['issues']:
                logger.warning("Health check issues found:")
                for issue in validation['issues']:
                    logger.warning(f"  - {issue}")
                
                # Post warning to Slack if critical
                if validation['overall_quality'] == 'poor':
                    slack_bot.post_custom_message(
                        f"⚠️ ElliotOS Health Check: System health is {validation['overall_quality']}. "
                        f"Issues: {', '.join(validation['issues'][:3])}"
                    )
            else:
                logger.success("✅ All systems healthy")
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
        
        logger.module_complete("Health Check")
    
    def run_manual_digest(self, digest_type: str = "morning"):
        """Run a manual digest for testing"""
        
        logger.info(f"Running manual {digest_type} digest...")
        
        if digest_type == "morning":
            self.run_morning_digest()
        elif digest_type == "evening":
            self.run_evening_digest()
        else:
            logger.error(f"Unknown digest type: {digest_type}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get ElliotOS status"""
        
        return {
            "running": self.running,
            "last_morning_digest": self.last_morning_digest.isoformat() if self.last_morning_digest else None,
            "last_evening_digest": self.last_evening_digest.isoformat() if self.last_evening_digest else None,
            "next_jobs": [
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run": job.next_run_time.isoformat() if job.next_run_time else None
                }
                for job in self.scheduler.get_jobs()
            ],
            "feature_status": settings.get_feature_status(),
            "slack_status": slack_bot.test_connection()
        }

def main():
    """Main entry point"""
    
    # Parse command line arguments
    import argparse
    
    parser = argparse.ArgumentParser(description="ElliotOS - Personal AI Assistant")
    parser.add_argument("--test-morning", action="store_true", help="Run morning digest once and exit")
    parser.add_argument("--test-evening", action="store_true", help="Run evening digest once and exit")
    parser.add_argument("--test-data", action="store_true", help="Test data aggregation and exit")
    parser.add_argument("--test-slack", action="store_true", help="Test Slack connection and exit")
    parser.add_argument("--status", action="store_true", help="Show status and exit")
    
    args = parser.parse_args()
    
    # Initialize ElliotOS
    elliot = ElliotOS()
    
    # Handle test commands
    if args.test_morning:
        logger.info("🧪 Testing morning digest...")
        elliot.run_manual_digest("morning")
        return
    
    if args.test_evening:
        logger.info("🧪 Testing evening digest...")
        elliot.run_manual_digest("evening")
        return
    
    if args.test_data:
        logger.info("🧪 Testing data aggregation...")
        data = fetch_all_data()
        summary = data_aggregator.get_data_summary(data)
        validation = data_aggregator.validate_data_quality(data)
        
        print(f"\n📊 Data Summary:")
        print(f"  Successful modules: {summary['successful_modules']}/{summary['total_modules']}")
        print(f"  Key insights: {len(summary['key_insights'])}")
        print(f"  Data quality: {validation['overall_quality']}")
        
        if summary['key_insights']:
            print(f"\n💡 Key Insights:")
            for insight in summary['key_insights']:
                print(f"  - {insight}")
        
        return
    
    if args.test_slack:
        logger.info("🧪 Testing Slack connection...")
        status = slack_bot.test_connection()
        print(f"\n💬 Slack Status:")
        print(f"  Bot clients: {status['bot_clients']}")
        print(f"  Webhook configured: {status['webhook_configured']}")
        print(f"  Can post: {status['can_post']}")
        print(f"  Teams: {', '.join(status['teams'])}")
        
        # Test posting
        if status['can_post']:
            success = slack_bot.post_custom_message("🧪 ElliotOS test message - system is working!")
            print(f"  Test message sent: {success}")
        
        return
    
    if args.status:
        logger.info("📊 Getting ElliotOS status...")
        status = elliot.get_status()
        
        print(f"\n🤖 ElliotOS Status:")
        print(f"  Running: {status['running']}")
        print(f"  Last morning digest: {status['last_morning_digest'] or 'Never'}")
        print(f"  Last evening digest: {status['last_evening_digest'] or 'Never'}")
        
        print(f"\n📅 Scheduled Jobs:")
        for job in status['next_jobs']:
            print(f"  - {job['name']}: {job['next_run'] or 'Not scheduled'}")
        
        print(f"\n🔧 Feature Status:")
        for feature, enabled in status['feature_status'].items():
            status_icon = "✅" if enabled else "❌"
            print(f"  {status_icon} {feature}")
        
        return
    
    # Start the main scheduler
    try:
        elliot.start()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.critical(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 