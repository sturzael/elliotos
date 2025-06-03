"""
Apple Health Integration for ElliotOS
Fetches health data from HealthKit including steps, sleep, heart rate, etc.
"""

import json
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from config.settings import settings
from utils.logger import get_logger

logger = get_logger("fetch_health")

class AppleHealthFetcher:
    """Fetches health data from Apple HealthKit"""
    
    def __init__(self):
        self.is_macos = self._check_macos()
        
    def _check_macos(self) -> bool:
        """Check if running on macOS"""
        try:
            import platform
            return platform.system() == "Darwin"
        except:
            return False
    
    def fetch_health_data(self) -> Dict[str, Any]:
        """Fetch comprehensive health data"""
        
        if not self.is_macos:
            logger.feature_disabled("Apple Health", "Not running on macOS")
            return {"error": "Not running on macOS", "health_data": {}}
        
        if not settings.APPLE_HEALTH_ENABLED:
            logger.feature_disabled("Apple Health", "Feature disabled in settings")
            return {"error": "Feature disabled", "health_data": {}}
        
        try:
            # Get various health metrics
            health_data = {
                "steps": self._get_steps_data(),
                "sleep": self._get_sleep_data(),
                "heart_rate": self._get_heart_rate_data(),
                "activity": self._get_activity_data(),
                "workouts": self._get_recent_workouts(),
                "body_metrics": self._get_body_metrics(),
                "mindfulness": self._get_mindfulness_data(),
                "screen_time": self._get_screen_time_data(),
                "fetched_at": datetime.now().isoformat()
            }
            
            logger.data_fetched("Apple Health", len([k for k, v in health_data.items() if v and k != "fetched_at"]))
            return health_data
            
        except Exception as e:
            logger.error(f"Failed to fetch health data: {e}")
            return {"error": str(e), "health_data": {}}
    
    def _get_steps_data(self) -> Dict[str, Any]:
        """Get steps data for today and recent days"""
        
        try:
            # AppleScript to get step count from Health app
            script = '''
            tell application "System Events"
                try
                    -- This is a simplified approach
                    -- In reality, you'd need HealthKit framework access
                    return "10247"  -- Mock data
                on error
                    return "0"
                end try
            end tell
            '''
            
            # Mock data for now - in a real implementation, you'd use:
            # - HealthKit framework via PyObjC
            # - Export Health data and read XML
            # - Use shortcuts automation
            
            today_steps = self._get_mock_steps()
            
            return {
                "today_steps": today_steps,
                "goal": 10000,
                "goal_progress": round((today_steps / 10000) * 100, 1),
                "weekly_average": self._get_weekly_average_steps(),
                "trend": "increasing" if today_steps > 8000 else "stable",
                "source": "mock_data"  # Would be "HealthKit" in real implementation
            }
            
        except Exception as e:
            logger.error(f"Failed to get steps data: {e}")
            return {}
    
    def _get_sleep_data(self) -> Dict[str, Any]:
        """Get sleep data for last night"""
        
        try:
            # Mock sleep data - in real implementation, use HealthKit
            last_night = {
                "bedtime": "23:30",
                "wake_time": "07:15",
                "total_hours": 7.75,
                "deep_sleep_hours": 2.1,
                "rem_sleep_hours": 1.8,
                "sleep_quality": "good",  # based on consistency and duration
                "sleep_efficiency": 89,  # percentage
                "restfulness": 7.5  # out of 10
            }
            
            return {
                "last_night": last_night,
                "weekly_average": 7.2,
                "sleep_debt": max(0, 8.0 - last_night["total_hours"]),
                "consistency_score": 8.5,  # based on regular bedtime
                "recommendations": self._get_sleep_recommendations(last_night),
                "source": "mock_data"
            }
            
        except Exception as e:
            logger.error(f"Failed to get sleep data: {e}")
            return {}
    
    def _get_heart_rate_data(self) -> Dict[str, Any]:
        """Get heart rate data"""
        
        try:
            # Mock heart rate data
            return {
                "current_hr": None,  # Only available with Apple Watch
                "resting_hr": 62,
                "max_hr_today": 145,
                "avg_hr_today": 78,
                "hrv": 35.2,  # Heart Rate Variability
                "workout_hr_zones": {
                    "fat_burn": "120-140",
                    "cardio": "140-165",
                    "peak": "165+"
                },
                "trend": "stable",
                "source": "mock_data"
            }
            
        except Exception as e:
            logger.error(f"Failed to get heart rate data: {e}")
            return {}
    
    def _get_activity_data(self) -> Dict[str, Any]:
        """Get activity rings data (Move, Exercise, Stand)"""
        
        try:
            # Mock activity rings data
            return {
                "move_ring": {
                    "goal": 630,  # calories
                    "current": 420,
                    "percentage": 66.7
                },
                "exercise_ring": {
                    "goal": 30,  # minutes
                    "current": 22,
                    "percentage": 73.3
                },
                "stand_ring": {
                    "goal": 12,  # hours
                    "current": 8,
                    "percentage": 66.7
                },
                "total_rings_closed": 0,
                "streak_days": 5,
                "weekly_summary": "3 of 7 days with all rings closed",
                "source": "mock_data"
            }
            
        except Exception as e:
            logger.error(f"Failed to get activity data: {e}")
            return {}
    
    def _get_recent_workouts(self) -> List[Dict[str, Any]]:
        """Get recent workout data"""
        
        try:
            # Mock workout data
            workouts = [
                {
                    "type": "Running",
                    "date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
                    "duration_minutes": 35,
                    "calories": 320,
                    "distance_km": 5.2,
                    "avg_heart_rate": 155,
                    "pace": "6:44 /km"
                },
                {
                    "type": "Strength Training",
                    "date": (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d"),
                    "duration_minutes": 45,
                    "calories": 280,
                    "avg_heart_rate": 125
                }
            ]
            
            return workouts
            
        except Exception as e:
            logger.error(f"Failed to get workout data: {e}")
            return []
    
    def _get_body_metrics(self) -> Dict[str, Any]:
        """Get body metrics (weight, BMI, etc.)"""
        
        try:
            # Mock body metrics
            return {
                "weight_kg": None,  # Privacy - only if user shares
                "bmi": None,
                "body_fat_percentage": None,
                "muscle_mass": None,
                "hydration_level": "good",
                "last_weigh_in": None,
                "source": "mock_data"
            }
            
        except Exception as e:
            logger.error(f"Failed to get body metrics: {e}")
            return {}
    
    def _get_mindfulness_data(self) -> Dict[str, Any]:
        """Get mindfulness and mental health data"""
        
        try:
            # Mock mindfulness data
            return {
                "meditation_minutes_today": 0,
                "meditation_streak": 0,
                "weekly_meditation_goal": 70,  # minutes
                "weekly_progress": 0,
                "mood_score": None,  # 1-10 scale
                "stress_level": None,  # low/medium/high
                "breathing_exercises": 0,
                "source": "mock_data"
            }
            
        except Exception as e:
            logger.error(f"Failed to get mindfulness data: {e}")
            return {}
    
    def _get_screen_time_data(self) -> Dict[str, Any]:
        """Get screen time data from macOS"""
        
        try:
            # This would integrate with macOS Screen Time
            return {
                "daily_screen_time_hours": 8.5,
                "most_used_apps": [
                    {"app": "Safari", "time_hours": 2.1},
                    {"app": "Slack", "time_hours": 1.8},
                    {"app": "Cursor", "time_hours": 3.2}
                ],
                "app_limits_exceeded": ["Social Media"],
                "pickup_count": 85,
                "first_pickup": "07:22",
                "last_use": "23:45",
                "source": "mock_data"
            }
            
        except Exception as e:
            logger.error(f"Failed to get screen time data: {e}")
            return {}
    
    def _get_mock_steps(self) -> int:
        """Generate realistic mock step data"""
        import random
        # Base step count with some randomness
        base_steps = 8500
        variation = random.randint(-2000, 3500)
        return max(0, base_steps + variation)
    
    def _get_weekly_average_steps(self) -> int:
        """Get weekly average steps"""
        # Mock weekly average
        return 9200
    
    def _get_sleep_recommendations(self, sleep_data: Dict[str, Any]) -> List[str]:
        """Generate sleep recommendations"""
        
        recommendations = []
        
        total_hours = sleep_data.get("total_hours", 0)
        
        if total_hours < 7:
            recommendations.append("💤 Aim for 7-9 hours of sleep for optimal health")
        
        if total_hours > 9:
            recommendations.append("⏰ You might be oversleeping - consider a consistent sleep schedule")
        
        bedtime = sleep_data.get("bedtime", "")
        if bedtime and ":" in bedtime:
            hour = int(bedtime.split(":")[0])
            if hour > 23 or hour < 6:
                recommendations.append("🌙 Consider an earlier bedtime for better sleep quality")
        
        sleep_efficiency = sleep_data.get("sleep_efficiency", 100)
        if sleep_efficiency < 85:
            recommendations.append("🛏️ Sleep efficiency is low - consider improving sleep environment")
        
        return recommendations

def fetch_health_data() -> Dict[str, Any]:
    """Main function to fetch health data"""
    
    logger.module_start("Apple Health")
    
    fetcher = AppleHealthFetcher()
    data = fetcher.fetch_health_data()
    
    # Add analysis
    if "health_data" not in data or data.get("error"):
        logger.module_complete("Apple Health")
        return data
    
    health_data = data
    
    # Calculate health insights
    analysis = {
        "overall_score": _calculate_health_score(health_data),
        "daily_summary": _generate_daily_summary(health_data),
        "recommendations": _generate_health_recommendations(health_data),
        "wellness_trends": _analyze_wellness_trends(health_data),
        "achievements": _check_achievements(health_data)
    }
    
    health_data["analysis"] = analysis
    
    logger.module_complete("Apple Health")
    return health_data

def _calculate_health_score(health_data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate overall health score"""
    
    score = 0
    max_score = 0
    
    # Steps score (30 points)
    steps = health_data.get("steps", {})
    if steps:
        steps_today = steps.get("today_steps", 0)
        steps_score = min(30, (steps_today / 10000) * 30)
        score += steps_score
    max_score += 30
    
    # Sleep score (25 points)
    sleep = health_data.get("sleep", {})
    if sleep and sleep.get("last_night"):
        sleep_hours = sleep["last_night"].get("total_hours", 0)
        if 7 <= sleep_hours <= 9:
            score += 25
        elif 6 <= sleep_hours < 7 or 9 < sleep_hours <= 10:
            score += 15
        else:
            score += 5
    max_score += 25
    
    # Activity rings score (25 points)
    activity = health_data.get("activity", {})
    if activity:
        rings_score = 0
        for ring in ["move_ring", "exercise_ring", "stand_ring"]:
            if ring in activity:
                percentage = activity[ring].get("percentage", 0)
                if percentage >= 100:
                    rings_score += 8.33
                else:
                    rings_score += (percentage / 100) * 8.33
        score += rings_score
    max_score += 25
    
    # Heart rate score (10 points)
    heart_rate = health_data.get("heart_rate", {})
    if heart_rate and heart_rate.get("resting_hr"):
        resting_hr = heart_rate["resting_hr"]
        if 60 <= resting_hr <= 70:
            score += 10
        elif 50 <= resting_hr < 60 or 70 < resting_hr <= 80:
            score += 7
        else:
            score += 3
    max_score += 10
    
    # Mindfulness score (10 points)
    mindfulness = health_data.get("mindfulness", {})
    if mindfulness:
        meditation_minutes = mindfulness.get("meditation_minutes_today", 0)
        if meditation_minutes >= 10:
            score += 10
        elif meditation_minutes >= 5:
            score += 5
        elif meditation_minutes > 0:
            score += 2
    max_score += 10
    
    percentage = round((score / max_score) * 100, 1) if max_score > 0 else 0
    
    return {
        "score": round(score, 1),
        "max_score": max_score,
        "percentage": percentage,
        "grade": "A" if percentage >= 90 else "B" if percentage >= 80 else "C" if percentage >= 70 else "D"
    }

def _generate_daily_summary(health_data: Dict[str, Any]) -> str:
    """Generate a daily health summary"""
    
    summary_parts = []
    
    # Steps
    steps = health_data.get("steps", {})
    if steps and steps.get("today_steps"):
        steps_today = steps["today_steps"]
        goal = steps.get("goal", 10000)
        if steps_today >= goal:
            summary_parts.append(f"✅ Hit your step goal with {steps_today:,} steps")
        else:
            remaining = goal - steps_today
            summary_parts.append(f"🚶 {steps_today:,} steps today ({remaining:,} to go)")
    
    # Sleep
    sleep = health_data.get("sleep", {})
    if sleep and sleep.get("last_night"):
        sleep_hours = sleep["last_night"]["total_hours"]
        if sleep_hours >= 7:
            summary_parts.append(f"😴 Good sleep: {sleep_hours} hours")
        else:
            summary_parts.append(f"⚠️ Short sleep: {sleep_hours} hours")
    
    # Activity rings
    activity = health_data.get("activity", {})
    if activity:
        rings_closed = activity.get("total_rings_closed", 0)
        if rings_closed == 3:
            summary_parts.append("🎯 All activity rings closed!")
        elif rings_closed > 0:
            summary_parts.append(f"🔥 {rings_closed}/3 activity rings closed")
        else:
            summary_parts.append("💪 Keep moving to close your rings")
    
    return " • ".join(summary_parts) if summary_parts else "Health data is being collected"

def _generate_health_recommendations(health_data: Dict[str, Any]) -> List[str]:
    """Generate health recommendations"""
    
    recommendations = []
    
    # Steps recommendations
    steps = health_data.get("steps", {})
    if steps:
        steps_today = steps.get("today_steps", 0)
        goal = steps.get("goal", 10000)
        if steps_today < goal * 0.5:
            recommendations.append("🚶‍♂️ Take a walk to boost your step count")
        elif steps_today < goal * 0.8:
            recommendations.append("👟 You're close to your step goal - keep moving!")
    
    # Sleep recommendations
    sleep = health_data.get("sleep", {})
    if sleep and sleep.get("recommendations"):
        recommendations.extend(sleep["recommendations"])
    
    # Activity recommendations
    activity = health_data.get("activity", {})
    if activity:
        exercise_ring = activity.get("exercise_ring", {})
        if exercise_ring.get("percentage", 0) < 50:
            recommendations.append("🏃‍♂️ Add some cardio to close your exercise ring")
        
        stand_ring = activity.get("stand_ring", {})
        if stand_ring.get("percentage", 0) < 80:
            recommendations.append("🧍‍♂️ Take hourly stand breaks to improve circulation")
    
    # Screen time recommendations
    screen_time = health_data.get("screen_time", {})
    if screen_time:
        daily_hours = screen_time.get("daily_screen_time_hours", 0)
        if daily_hours > 10:
            recommendations.append("📱 Consider reducing screen time for better eye health")
    
    return recommendations

def _analyze_wellness_trends(health_data: Dict[str, Any]) -> Dict[str, str]:
    """Analyze wellness trends"""
    
    trends = {}
    
    # Steps trend
    steps = health_data.get("steps", {})
    if steps:
        trend = steps.get("trend", "stable")
        trends["steps"] = trend
    
    # Sleep trend
    sleep = health_data.get("sleep", {})
    if sleep:
        weekly_avg = sleep.get("weekly_average", 0)
        last_night = sleep.get("last_night", {}).get("total_hours", 0)
        if last_night > weekly_avg + 0.5:
            trends["sleep"] = "improving"
        elif last_night < weekly_avg - 0.5:
            trends["sleep"] = "declining"
        else:
            trends["sleep"] = "stable"
    
    # Activity trend
    activity = health_data.get("activity", {})
    if activity:
        streak = activity.get("streak_days", 0)
        if streak >= 7:
            trends["activity"] = "excellent_streak"
        elif streak >= 3:
            trends["activity"] = "good_streak"
        else:
            trends["activity"] = "needs_consistency"
    
    return trends

def _check_achievements(health_data: Dict[str, Any]) -> List[str]:
    """Check for health achievements"""
    
    achievements = []
    
    # Step achievements
    steps = health_data.get("steps", {})
    if steps:
        steps_today = steps.get("today_steps", 0)
        if steps_today >= 15000:
            achievements.append("🏆 Super Walker: 15K+ steps today!")
        elif steps_today >= 12000:
            achievements.append("🥇 Active Day: 12K+ steps!")
    
    # Sleep achievements
    sleep = health_data.get("sleep", {})
    if sleep:
        consistency = sleep.get("consistency_score", 0)
        if consistency >= 9:
            achievements.append("😴 Sleep Champion: Excellent consistency!")
    
    # Activity achievements
    activity = health_data.get("activity", {})
    if activity:
        rings_closed = activity.get("total_rings_closed", 0)
        streak = activity.get("streak_days", 0)
        
        if rings_closed == 3:
            achievements.append("🎯 Perfect Day: All rings closed!")
        
        if streak >= 30:
            achievements.append("🔥 Monthly Streak: 30+ days active!")
        elif streak >= 7:
            achievements.append("⭐ Weekly Streak: 7+ days active!")
    
    return achievements

if __name__ == "__main__":
    # Test the module
    import pprint
    data = fetch_health_data()
    pprint.pprint(data) 