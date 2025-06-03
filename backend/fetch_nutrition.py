"""
MyFitnessPal Integration for ElliotOS
Fetches nutrition data including meals, calories, and macronutrients
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup

from config.settings import settings
from utils.logger import get_logger

logger = get_logger("fetch_nutrition")

class MyFitnessPalFetcher:
    """Fetches nutrition data from MyFitnessPal"""
    
    def __init__(self):
        self.session = requests.Session()
        self.logged_in = False
        
    def fetch_nutrition_data(self) -> Dict[str, Any]:
        """Fetch comprehensive nutrition data"""
        
        if not settings.MYFITNESSPAL_EMAIL or not settings.MYFITNESSPAL_PASSWORD:
            logger.feature_disabled("MyFitnessPal", "Missing credentials")
            return {"error": "Missing credentials", "nutrition_data": {}}
        
        try:
            # Attempt login
            if not self._login():
                return {"error": "Login failed", "nutrition_data": {}}
            
            # Get nutrition data
            nutrition_data = {
                "daily_summary": self._get_daily_summary(),
                "meals": self._get_meals(),
                "macros": self._get_macros(),
                "water_intake": self._get_water_intake(),
                "exercise": self._get_exercise_log(),
                "weight_log": self._get_weight_log(),
                "goals": self._get_nutrition_goals(),
                "streak": self._get_logging_streak(),
                "fetched_at": datetime.now().isoformat()
            }
            
            logger.data_fetched("MyFitnessPal", len([k for k, v in nutrition_data.items() if v and k != "fetched_at"]))
            return nutrition_data
            
        except Exception as e:
            logger.error(f"Failed to fetch nutrition data: {e}")
            return {"error": str(e), "nutrition_data": {}}
    
    def _login(self) -> bool:
        """Login to MyFitnessPal"""
        
        try:
            # For now, return mock data instead of actual scraping
            # In a real implementation, you would:
            # 1. Use myfitnesspal-python library
            # 2. Or implement proper web scraping with authentication
            # 3. Handle rate limiting and terms of service
            
            logger.warning("Using mock MyFitnessPal data - implement proper API/scraping")
            self.logged_in = True
            return True
            
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False
    
    def _get_daily_summary(self) -> Dict[str, Any]:
        """Get daily calorie and macro summary"""
        
        # Mock data - replace with actual MyFitnessPal data
        return {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "calories": {
                "consumed": 1650,
                "burned_exercise": 320,
                "burned_bmr": 1800,
                "net": 1330,
                "goal": 2000,
                "remaining": 670
            },
            "macros": {
                "carbs": {"consumed": 185, "goal": 250, "percentage": 74},
                "fat": {"consumed": 78, "goal": 89, "percentage": 88},
                "protein": {"consumed": 125, "goal": 150, "percentage": 83},
                "fiber": {"consumed": 28, "goal": 35, "percentage": 80},
                "sugar": {"consumed": 45, "goal": 50, "percentage": 90},
                "sodium": {"consumed": 1950, "goal": 2300, "percentage": 85}
            },
            "calories_remaining_healthy": True,  # Not too low or high
            "macro_balance": "good"  # Balanced macros
        }
    
    def _get_meals(self) -> List[Dict[str, Any]]:
        """Get meals logged today"""
        
        # Mock meal data
        meals = [
            {
                "meal_type": "Breakfast",
                "time": "08:30",
                "foods": [
                    {"name": "Oatmeal with berries", "calories": 280, "serving": "1 bowl"},
                    {"name": "Greek yogurt", "calories": 150, "serving": "1 cup"},
                    {"name": "Coffee with milk", "calories": 35, "serving": "1 cup"}
                ],
                "total_calories": 465,
                "macros": {"carbs": 68, "fat": 12, "protein": 22}
            },
            {
                "meal_type": "Lunch",
                "time": "13:15",
                "foods": [
                    {"name": "Grilled chicken salad", "calories": 420, "serving": "1 large bowl"},
                    {"name": "Olive oil dressing", "calories": 80, "serving": "2 tbsp"},
                    {"name": "Whole grain roll", "calories": 120, "serving": "1 roll"}
                ],
                "total_calories": 620,
                "macros": {"carbs": 45, "fat": 22, "protein": 35}
            },
            {
                "meal_type": "Dinner",
                "time": "19:45",
                "foods": [
                    {"name": "Salmon fillet", "calories": 350, "serving": "6 oz"},
                    {"name": "Quinoa", "calories": 160, "serving": "1 cup"},
                    {"name": "Steamed broccoli", "calories": 55, "serving": "1 cup"}
                ],
                "total_calories": 565,
                "macros": {"carbs": 42, "fat": 18, "protein": 45}
            }
        ]
        
        return meals
    
    def _get_macros(self) -> Dict[str, Any]:
        """Get detailed macro breakdown"""
        
        return {
            "carbs": {
                "total_g": 185,
                "goal_g": 250,
                "calories": 740,
                "percentage_of_calories": 45,
                "sources": ["Oats", "Quinoa", "Vegetables", "Fruits"]
            },
            "fat": {
                "total_g": 78,
                "goal_g": 89,
                "calories": 702,
                "percentage_of_calories": 42,
                "sources": ["Salmon", "Olive oil", "Nuts", "Yogurt"]
            },
            "protein": {
                "total_g": 125,
                "goal_g": 150,
                "calories": 500,
                "percentage_of_calories": 30,
                "sources": ["Chicken", "Salmon", "Greek yogurt", "Quinoa"]
            },
            "fiber": {
                "total_g": 28,
                "goal_g": 35,
                "sources": ["Vegetables", "Fruits", "Whole grains"]
            }
        }
    
    def _get_water_intake(self) -> Dict[str, Any]:
        """Get water intake data"""
        
        return {
            "glasses_today": 6,
            "goal_glasses": 8,
            "ml_today": 1500,
            "goal_ml": 2000,
            "percentage": 75,
            "last_logged": "15:30",
            "reminder_needed": True
        }
    
    def _get_exercise_log(self) -> List[Dict[str, Any]]:
        """Get exercise logged today"""
        
        return [
            {
                "type": "Running",
                "duration_minutes": 35,
                "calories_burned": 320,
                "time": "07:00",
                "notes": "Morning jog in the park"
            }
        ]
    
    def _get_weight_log(self) -> Dict[str, Any]:
        """Get recent weight entries"""
        
        return {
            "current_weight_kg": None,  # Privacy
            "last_weigh_in": (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d"),
            "trend": "stable",  # stable/increasing/decreasing
            "goal_weight_kg": None,
            "progress_toward_goal": None
        }
    
    def _get_nutrition_goals(self) -> Dict[str, Any]:
        """Get user's nutrition goals"""
        
        return {
            "daily_calories": 2000,
            "macro_ratios": {
                "carbs_percent": 50,
                "fat_percent": 30,
                "protein_percent": 20
            },
            "activity_level": "moderately_active",
            "goal_type": "maintain_weight",  # lose_weight/gain_weight/maintain_weight
            "weekly_weight_goal": 0  # kg per week
        }
    
    def _get_logging_streak(self) -> Dict[str, Any]:
        """Get food logging streak"""
        
        return {
            "current_streak_days": 12,
            "longest_streak_days": 45,
            "logged_today": True,
            "consistency_percentage": 85  # last 30 days
        }

def fetch_nutrition_data() -> Dict[str, Any]:
    """Main function to fetch nutrition data"""
    
    logger.module_start("MyFitnessPal")
    
    fetcher = MyFitnessPalFetcher()
    data = fetcher.fetch_nutrition_data()
    
    # Add analysis
    if "nutrition_data" not in data or data.get("error"):
        logger.module_complete("MyFitnessPal")
        return data
    
    nutrition_data = data
    
    # Calculate nutrition insights
    analysis = {
        "nutrition_score": _calculate_nutrition_score(nutrition_data),
        "daily_summary": _generate_nutrition_summary(nutrition_data),
        "recommendations": _generate_nutrition_recommendations(nutrition_data),
        "trends": _analyze_nutrition_trends(nutrition_data),
        "achievements": _check_nutrition_achievements(nutrition_data)
    }
    
    nutrition_data["analysis"] = analysis
    
    logger.module_complete("MyFitnessPal")
    return nutrition_data

def _calculate_nutrition_score(nutrition_data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate overall nutrition score"""
    
    score = 0
    max_score = 100
    
    # Calorie adherence (30 points)
    daily_summary = nutrition_data.get("daily_summary", {})
    if daily_summary:
        calories = daily_summary.get("calories", {})
        consumed = calories.get("consumed", 0)
        goal = calories.get("goal", 2000)
        
        if goal > 0:
            ratio = consumed / goal
            if 0.9 <= ratio <= 1.1:  # Within 10% of goal
                score += 30
            elif 0.8 <= ratio < 0.9 or 1.1 < ratio <= 1.2:  # Within 20%
                score += 20
            elif 0.7 <= ratio < 0.8 or 1.2 < ratio <= 1.3:  # Within 30%
                score += 10
    
    # Macro balance (30 points)
    macros = nutrition_data.get("macros", {})
    if macros:
        macro_score = 0
        for macro in ["carbs", "fat", "protein"]:
            if macro in macros:
                consumed = macros[macro].get("total_g", 0)
                goal = macros[macro].get("goal_g", 1)
                if goal > 0:
                    ratio = consumed / goal
                    if 0.8 <= ratio <= 1.2:
                        macro_score += 10
                    elif 0.6 <= ratio < 0.8 or 1.2 < ratio <= 1.4:
                        macro_score += 5
        score += macro_score
    
    # Hydration (20 points)
    water = nutrition_data.get("water_intake", {})
    if water:
        water_percentage = water.get("percentage", 0)
        if water_percentage >= 100:
            score += 20
        elif water_percentage >= 75:
            score += 15
        elif water_percentage >= 50:
            score += 10
        elif water_percentage >= 25:
            score += 5
    
    # Logging consistency (20 points)
    streak = nutrition_data.get("streak", {})
    if streak:
        logged_today = streak.get("logged_today", False)
        consistency = streak.get("consistency_percentage", 0)
        
        if logged_today:
            score += 10
        
        if consistency >= 90:
            score += 10
        elif consistency >= 75:
            score += 7
        elif consistency >= 50:
            score += 5
    
    percentage = round((score / max_score) * 100, 1)
    
    return {
        "score": score,
        "max_score": max_score,
        "percentage": percentage,
        "grade": "A" if percentage >= 90 else "B" if percentage >= 80 else "C" if percentage >= 70 else "D"
    }

def _generate_nutrition_summary(nutrition_data: Dict[str, Any]) -> str:
    """Generate a nutrition summary"""
    
    summary_parts = []
    
    # Calories
    daily_summary = nutrition_data.get("daily_summary", {})
    if daily_summary:
        calories = daily_summary.get("calories", {})
        consumed = calories.get("consumed", 0)
        goal = calories.get("goal", 0)
        remaining = calories.get("remaining", 0)
        
        if remaining > 0:
            summary_parts.append(f"🍽️ {consumed} calories consumed, {remaining} remaining")
        else:
            over = abs(remaining)
            summary_parts.append(f"🍽️ {consumed} calories consumed ({over} over goal)")
    
    # Water
    water = nutrition_data.get("water_intake", {})
    if water:
        glasses = water.get("glasses_today", 0)
        goal_glasses = water.get("goal_glasses", 8)
        if glasses >= goal_glasses:
            summary_parts.append(f"💧 Hydration goal met ({glasses}/{goal_glasses} glasses)")
        else:
            summary_parts.append(f"💧 {glasses}/{goal_glasses} glasses of water")
    
    # Logging streak
    streak = nutrition_data.get("streak", {})
    if streak:
        streak_days = streak.get("current_streak_days", 0)
        if streak_days > 0:
            summary_parts.append(f"📝 {streak_days}-day logging streak")
    
    return " • ".join(summary_parts) if summary_parts else "Nutrition data is being tracked"

def _generate_nutrition_recommendations(nutrition_data: Dict[str, Any]) -> List[str]:
    """Generate nutrition recommendations"""
    
    recommendations = []
    
    # Calorie recommendations
    daily_summary = nutrition_data.get("daily_summary", {})
    if daily_summary:
        calories = daily_summary.get("calories", {})
        remaining = calories.get("remaining", 0)
        
        if remaining > 500:
            recommendations.append("🍎 You have calories remaining - consider a healthy snack")
        elif remaining < -200:
            recommendations.append("⚖️ Consider lighter options for your next meal")
    
    # Macro recommendations
    macros = nutrition_data.get("macros", {})
    if macros:
        protein = macros.get("protein", {})
        if protein:
            protein_percentage = protein.get("total_g", 0) / protein.get("goal_g", 1) * 100
            if protein_percentage < 70:
                recommendations.append("🥩 Add more protein to support muscle health")
        
        fiber = macros.get("fiber", {})
        if fiber:
            fiber_total = fiber.get("total_g", 0)
            fiber_goal = fiber.get("goal_g", 35)
            if fiber_total < fiber_goal * 0.7:
                recommendations.append("🥬 Include more fiber-rich foods for digestive health")
    
    # Water recommendations
    water = nutrition_data.get("water_intake", {})
    if water:
        percentage = water.get("percentage", 0)
        if percentage < 75:
            recommendations.append("💧 Increase water intake for better hydration")
    
    # Exercise recommendations
    exercise = nutrition_data.get("exercise", [])
    if not exercise:
        recommendations.append("🏃‍♂️ Log some exercise to balance your nutrition")
    
    return recommendations

def _analyze_nutrition_trends(nutrition_data: Dict[str, Any]) -> Dict[str, str]:
    """Analyze nutrition trends"""
    
    # This would analyze historical data
    # For now, return basic trends based on current data
    
    trends = {}
    
    # Calorie trend
    daily_summary = nutrition_data.get("daily_summary", {})
    if daily_summary:
        calories = daily_summary.get("calories", {})
        consumed = calories.get("consumed", 0)
        goal = calories.get("goal", 2000)
        
        ratio = consumed / goal if goal > 0 else 0
        if ratio > 1.1:
            trends["calories"] = "consistently_over"
        elif ratio < 0.8:
            trends["calories"] = "consistently_under"
        else:
            trends["calories"] = "on_track"
    
    # Logging trend
    streak = nutrition_data.get("streak", {})
    if streak:
        consistency = streak.get("consistency_percentage", 0)
        if consistency >= 90:
            trends["logging"] = "excellent"
        elif consistency >= 75:
            trends["logging"] = "good"
        else:
            trends["logging"] = "needs_improvement"
    
    return trends

def _check_nutrition_achievements(nutrition_data: Dict[str, Any]) -> List[str]:
    """Check for nutrition achievements"""
    
    achievements = []
    
    # Logging streak achievements
    streak = nutrition_data.get("streak", {})
    if streak:
        streak_days = streak.get("current_streak_days", 0)
        
        if streak_days >= 30:
            achievements.append("🏆 Nutrition Champion: 30+ day logging streak!")
        elif streak_days >= 14:
            achievements.append("📝 Consistent Logger: 2+ week streak!")
        elif streak_days >= 7:
            achievements.append("⭐ Week Warrior: 7+ day streak!")
    
    # Hydration achievements
    water = nutrition_data.get("water_intake", {})
    if water:
        percentage = water.get("percentage", 0)
        if percentage >= 100:
            achievements.append("💧 Hydration Hero: Daily water goal achieved!")
    
    # Macro balance achievements
    daily_summary = nutrition_data.get("daily_summary", {})
    if daily_summary:
        macro_balance = daily_summary.get("macro_balance", "")
        if macro_balance == "good":
            achievements.append("⚖️ Macro Master: Well-balanced nutrition today!")
    
    return achievements

if __name__ == "__main__":
    # Test the module
    import pprint
    data = fetch_nutrition_data()
    pprint.pprint(data) 