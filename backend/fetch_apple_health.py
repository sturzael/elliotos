"""
Apple Health Integration for ElliotOS
Fetches steps and walking distance data from Apple HealthKit
"""

import subprocess
import json
from typing import Dict, Any, List
from datetime import datetime, timedelta

from config.settings import settings
from utils.logger import get_logger

logger = get_logger("fetch_apple_health")

def get_steps_data() -> List[Dict[str, Any]]:
    """Get daily step count for the last 7 days"""
    
    try:
        # Use shortcuts or osascript to get HealthKit data
        script = '''
        tell application "Health"
            -- This is a placeholder - actual implementation would use HealthKit API
        end tell
        '''
        
        # For now, return mock data - in production this would use HealthKit
        steps_data = []
        for i in range(7):
            date = datetime.now() - timedelta(days=i)
            steps_data.append({
                "date": date.strftime("%Y-%m-%d"),
                "value": 8000 + (i * 500),  # Mock data
                "unit": "steps"
            })
        
        return steps_data
        
    except Exception as e:
        logger.error(f"Failed to get steps data: {e}")
        return []

def get_walking_distance_data() -> List[Dict[str, Any]]:
    """Get daily walking distance for the last 7 days"""
    
    try:
        # For now, return mock data - in production this would use HealthKit
        distance_data = []
        for i in range(7):
            date = datetime.now() - timedelta(days=i)
            distance_data.append({
                "date": date.strftime("%Y-%m-%d"),
                "value": 5.2 + (i * 0.3),  # Mock data in km
                "unit": "km"
            })
        
        return distance_data
        
    except Exception as e:
        logger.error(f"Failed to get walking distance data: {e}")
        return []

def fetch_apple_health_data() -> Dict[str, Any]:
    """Fetch Apple Health data using HealthKit"""
    
    logger.module_start("Apple Health")
    
    if not settings.APPLE_HEALTH_ENABLED:
        logger.feature_disabled("Apple Health", "Disabled in settings")
        return {"error": "Apple Health disabled", "data": []}
    
    try:
        # Only fetch steps and walking distance
        health_data = {
            "steps": get_steps_data(),
            "walking_distance": get_walking_distance_data(),
            "fetched_at": datetime.now().isoformat()
        }
        
        # Calculate totals and averages
        total_steps = sum(day.get("value", 0) for day in health_data["steps"])
        total_distance = sum(day.get("value", 0) for day in health_data["walking_distance"])
        
        # Add summary
        health_data["summary"] = {
            "total_steps_7_days": total_steps,
            "avg_steps_per_day": total_steps / 7 if total_steps > 0 else 0,
            "total_distance_7_days_km": round(total_distance, 2),
            "avg_distance_per_day_km": round(total_distance / 7, 2) if total_distance > 0 else 0,
            "most_active_day": max(health_data["steps"], key=lambda x: x.get("value", 0), default={}).get("date", "N/A"),
            "least_active_day": min(health_data["steps"], key=lambda x: x.get("value", 0), default={}).get("date", "N/A")
        }
        
        total_items = len(health_data["steps"]) + len(health_data["walking_distance"])
        logger.data_fetched("Apple Health", total_items)
        
        return health_data
        
    except Exception as e:
        logger.error(f"Failed to fetch Apple Health data: {e}")
        return {"error": str(e), "data": []}

if __name__ == "__main__":
    # Test the module
    import pprint
    data = fetch_apple_health_data()
    pprint.pprint(data) 