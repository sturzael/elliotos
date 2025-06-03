"""
ElliotOS Data Aggregator
Fetches and combines data from all backend modules
"""

import time
from datetime import datetime
from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed

from backend.fetch_calendar import fetch_calendar_data
from backend.fetch_gmail import fetch_gmail_data
from backend.fetch_slack import fetch_slack_data
from backend.fetch_mac_stats import fetch_mac_stats
from backend.fetch_health import fetch_health_data
from backend.fetch_nutrition import fetch_nutrition_data
from backend.fetch_news import fetch_news_data
from backend.fetch_chelsea import fetch_chelsea_data
from config.settings import settings
from utils.logger import get_logger

logger = get_logger("data_aggregator")

class DataAggregator:
    """Aggregates data from all ElliotOS modules"""
    
    def __init__(self):
        self.modules = {
            "calendar": fetch_calendar_data,
            "gmail": fetch_gmail_data,
            "slack": fetch_slack_data,
            "mac_stats": fetch_mac_stats,
            "health": fetch_health_data,
            "nutrition": fetch_nutrition_data,
            "news": fetch_news_data,
            "chelsea": fetch_chelsea_data
        }
    
    def fetch_all_data(self, parallel: bool = True) -> Dict[str, Any]:
        """Fetch data from all modules"""
        
        logger.module_start("Data Aggregation")
        start_time = time.time()
        
        if parallel:
            data = self._fetch_parallel()
        else:
            data = self._fetch_sequential()
        
        # Add metadata
        data["_metadata"] = {
            "fetched_at": datetime.now().isoformat(),
            "fetch_duration": round(time.time() - start_time, 2),
            "modules_attempted": len(self.modules),
            "modules_successful": len([k for k, v in data.items() if not k.startswith("_") and not v.get("error")]),
            "feature_status": settings.get_feature_status()
        }
        
        logger.module_complete("Data Aggregation", time.time() - start_time)
        return data
    
    def _fetch_parallel(self) -> Dict[str, Any]:
        """Fetch data from all modules in parallel"""
        
        data = {}
        
        with ThreadPoolExecutor(max_workers=8) as executor:
            # Submit all tasks
            future_to_module = {
                executor.submit(func): module_name 
                for module_name, func in self.modules.items()
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_module):
                module_name = future_to_module[future]
                
                try:
                    result = future.result(timeout=30)  # 30 second timeout per module
                    data[module_name] = result
                    
                    if result.get("error"):
                        logger.warning(f"Module {module_name} returned error: {result['error']}")
                    else:
                        logger.success(f"Successfully fetched {module_name} data")
                        
                except Exception as e:
                    logger.error(f"Module {module_name} failed: {e}")
                    data[module_name] = {"error": str(e), "failed_at": datetime.now().isoformat()}
        
        return data
    
    def _fetch_sequential(self) -> Dict[str, Any]:
        """Fetch data from all modules sequentially"""
        
        data = {}
        
        for module_name, func in self.modules.items():
            try:
                logger.info(f"Fetching {module_name} data...")
                result = func()
                data[module_name] = result
                
                if result.get("error"):
                    logger.warning(f"Module {module_name} returned error: {result['error']}")
                else:
                    logger.success(f"Successfully fetched {module_name} data")
                    
            except Exception as e:
                logger.error(f"Module {module_name} failed: {e}")
                data[module_name] = {"error": str(e), "failed_at": datetime.now().isoformat()}
        
        return data
    
    def fetch_essential_data(self) -> Dict[str, Any]:
        """Fetch only essential data for quick summaries"""
        
        essential_modules = ["calendar", "slack", "health", "mac_stats"]
        
        logger.info("Fetching essential data only")
        
        data = {}
        
        for module_name in essential_modules:
            if module_name in self.modules:
                try:
                    func = self.modules[module_name]
                    result = func()
                    data[module_name] = result
                    
                    if not result.get("error"):
                        logger.success(f"Fetched essential {module_name} data")
                        
                except Exception as e:
                    logger.error(f"Essential module {module_name} failed: {e}")
                    data[module_name] = {"error": str(e)}
        
        data["_metadata"] = {
            "fetched_at": datetime.now().isoformat(),
            "mode": "essential_only",
            "modules": essential_modules
        }
        
        return data
    
    def get_data_summary(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a summary of the aggregated data"""
        
        summary = {
            "total_modules": 0,
            "successful_modules": 0,
            "failed_modules": 0,
            "data_points": {},
            "key_insights": []
        }
        
        for module_name, module_data in data.items():
            if module_name.startswith("_"):
                continue
                
            summary["total_modules"] += 1
            
            if module_data.get("error"):
                summary["failed_modules"] += 1
            else:
                summary["successful_modules"] += 1
                
                # Count data points for each module
                summary["data_points"][module_name] = self._count_data_points(module_data)
        
        # Generate key insights
        summary["key_insights"] = self._generate_key_insights(data)
        
        return summary
    
    def _count_data_points(self, module_data: Dict[str, Any]) -> int:
        """Count meaningful data points in a module's data"""
        
        count = 0
        
        for key, value in module_data.items():
            if key in ["error", "fetched_at", "_metadata"]:
                continue
                
            if isinstance(value, list):
                count += len(value)
            elif isinstance(value, dict) and value:
                count += 1
            elif value is not None:
                count += 1
        
        return count
    
    def _generate_key_insights(self, data: Dict[str, Any]) -> List[str]:
        """Generate key insights from the aggregated data"""
        
        insights = []
        
        # Calendar insights
        if "calendar" in data and not data["calendar"].get("error"):
            calendar_data = data["calendar"]
            today_events = len(calendar_data.get("today_events", []))
            if today_events > 0:
                insights.append(f"📅 {today_events} calendar events today")
        
        # Health insights
        if "health" in data and not data["health"].get("error"):
            health_data = data["health"]
            if "analysis" in health_data:
                score = health_data["analysis"].get("overall_score", {})
                if score.get("percentage"):
                    insights.append(f"💪 Health score: {score['percentage']}%")
        
        # Slack insights
        if "slack" in data and not data["slack"].get("error"):
            slack_data = data["slack"]
            if "aggregated" in slack_data:
                mentions = slack_data["aggregated"].get("total_mentions", 0)
                unread = slack_data["aggregated"].get("total_unread", 0)
                if mentions > 0 or unread > 0:
                    insights.append(f"💬 {mentions} mentions, {unread} unread messages")
        
        # Productivity insights
        if "mac_stats" in data and not data["mac_stats"].get("error"):
            mac_data = data["mac_stats"]
            if "productivity_metrics" in mac_data:
                current_app = mac_data.get("current_app", {}).get("name", "")
                if current_app:
                    insights.append(f"💻 Currently using: {current_app}")
        
        # News insights
        if "news" in data and not data["news"].get("error"):
            news_data = data["news"]
            if "analysis" in news_data:
                urgency = news_data["analysis"].get("urgency_level", "low")
                if urgency == "high":
                    insights.append("📰 High urgency news detected")
        
        # Chelsea insights
        if "chelsea" in data and not data["chelsea"].get("error"):
            chelsea_data = data["chelsea"]
            next_match = chelsea_data.get("next_match")
            if next_match:
                opponent = next_match.get("opponent", "")
                days_until = next_match.get("days_until", 0)
                if days_until <= 3:
                    insights.append(f"⚽ Chelsea vs {opponent} in {days_until} days")
        
        return insights
    
    def validate_data_quality(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate the quality and completeness of aggregated data"""
        
        validation = {
            "overall_quality": "good",
            "issues": [],
            "recommendations": [],
            "module_status": {}
        }
        
        critical_modules = ["calendar", "slack"]
        important_modules = ["health", "mac_stats"]
        
        # Check critical modules
        for module in critical_modules:
            if module not in data:
                validation["issues"].append(f"Critical module {module} missing")
                validation["overall_quality"] = "poor"
            elif data[module].get("error"):
                validation["issues"].append(f"Critical module {module} failed: {data[module]['error']}")
                validation["overall_quality"] = "poor"
            else:
                validation["module_status"][module] = "healthy"
        
        # Check important modules
        for module in important_modules:
            if module not in data:
                validation["issues"].append(f"Important module {module} missing")
                if validation["overall_quality"] == "good":
                    validation["overall_quality"] = "fair"
            elif data[module].get("error"):
                validation["issues"].append(f"Important module {module} failed: {data[module]['error']}")
                if validation["overall_quality"] == "good":
                    validation["overall_quality"] = "fair"
            else:
                validation["module_status"][module] = "healthy"
        
        # Generate recommendations
        if validation["issues"]:
            validation["recommendations"].append("Check module configurations and API credentials")
            validation["recommendations"].append("Review logs for detailed error information")
        
        if len(validation["module_status"]) < 4:
            validation["recommendations"].append("Enable more data sources for richer insights")
        
        return validation

# Global aggregator instance
data_aggregator = DataAggregator()

def fetch_all_data(parallel: bool = True) -> Dict[str, Any]:
    """Convenience function to fetch all data"""
    return data_aggregator.fetch_all_data(parallel=parallel)

def fetch_essential_data() -> Dict[str, Any]:
    """Convenience function to fetch essential data only"""
    return data_aggregator.fetch_essential_data()

if __name__ == "__main__":
    # Test the aggregator
    import pprint
    
    print("Testing data aggregation...")
    data = fetch_all_data()
    
    print("\n=== DATA SUMMARY ===")
    summary = data_aggregator.get_data_summary(data)
    pprint.pprint(summary)
    
    print("\n=== DATA VALIDATION ===")
    validation = data_aggregator.validate_data_quality(data)
    pprint.pprint(validation) 