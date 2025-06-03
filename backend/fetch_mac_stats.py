"""
macOS Statistics Fetcher for ElliotOS
Tracks app usage, productivity metrics, and system information
"""

import json
import subprocess
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import Counter, defaultdict

from config.settings import settings
from utils.logger import get_logger

logger = get_logger("fetch_mac_stats")

class MacStatsFetcher:
    """Fetches macOS usage statistics and productivity metrics"""
    
    def __init__(self):
        self.is_macos = self._check_macos()
        
    def _check_macos(self) -> bool:
        """Check if running on macOS"""
        try:
            import platform
            return platform.system() == "Darwin"
        except:
            return False
    
    def fetch_mac_stats(self) -> Dict[str, Any]:
        """Fetch comprehensive macOS statistics"""
        
        if not self.is_macos:
            logger.feature_disabled("macOS Stats", "Not running on macOS")
            return {"error": "Not running on macOS", "stats": {}}
        
        if not settings.MACOS_APP_USAGE_ENABLED:
            logger.feature_disabled("macOS Stats", "Feature disabled in settings")
            return {"error": "Feature disabled", "stats": {}}
        
        try:
            # Get various system metrics
            stats = {
                "system_info": self._get_system_info(),
                "current_app": self._get_current_app(),
                "running_apps": self._get_running_apps(),
                "window_info": self._get_window_info(),
                "productivity_metrics": self._get_productivity_metrics(),
                "battery_info": self._get_battery_info(),
                "network_activity": self._get_network_activity(),
                "memory_usage": self._get_memory_usage(),
                "cpu_usage": self._get_cpu_usage(),
                "screen_time": self._estimate_screen_time(),
                "fetched_at": datetime.now().isoformat()
            }
            
            logger.data_fetched("macOS Stats", len(stats))
            return stats
            
        except Exception as e:
            logger.error(f"Failed to fetch macOS stats: {e}")
            return {"error": str(e), "stats": {}}
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Get basic system information"""
        
        try:
            # Get macOS version
            result = subprocess.run(
                ["sw_vers", "-productVersion"], 
                capture_output=True, 
                text=True
            )
            macos_version = result.stdout.strip() if result.returncode == 0 else "Unknown"
            
            # Get uptime
            uptime_result = subprocess.run(
                ["uptime"], 
                capture_output=True, 
                text=True
            )
            uptime = uptime_result.stdout.strip() if uptime_result.returncode == 0 else "Unknown"
            
            return {
                "macos_version": macos_version,
                "uptime": uptime,
                "hostname": subprocess.run(["hostname"], capture_output=True, text=True).stdout.strip(),
                "user": subprocess.run(["whoami"], capture_output=True, text=True).stdout.strip(),
                "architecture": subprocess.run(["uname", "-m"], capture_output=True, text=True).stdout.strip()
            }
            
        except Exception as e:
            logger.error(f"Failed to get system info: {e}")
            return {}
    
    def _get_current_app(self) -> Dict[str, Any]:
        """Get currently active application"""
        
        try:
            # AppleScript to get current app
            script = '''
            tell application "System Events"
                set frontApp to first application process whose frontmost is true
                set appName to name of frontApp
                set appID to bundle identifier of frontApp
                return appName & "|" & appID
            end tell
            '''
            
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                output = result.stdout.strip()
                if "|" in output:
                    app_name, app_id = output.split("|", 1)
                    return {
                        "name": app_name,
                        "bundle_id": app_id,
                        "timestamp": datetime.now().isoformat()
                    }
            
            return {"name": "Unknown", "bundle_id": "", "timestamp": datetime.now().isoformat()}
            
        except Exception as e:
            logger.error(f"Failed to get current app: {e}")
            return {}
    
    def _get_running_apps(self) -> List[Dict[str, Any]]:
        """Get list of currently running applications"""
        
        try:
            # Get running processes
            running_apps = []
            
            for proc in psutil.process_iter(['pid', 'name', 'memory_percent', 'cpu_percent']):
                try:
                    info = proc.info
                    
                    # Filter for GUI applications (heuristic)
                    if (info['name'] and 
                        not info['name'].startswith('.') and 
                        info['memory_percent'] > 0.1):  # Use some memory
                        
                        running_apps.append({
                            "name": info['name'],
                            "pid": info['pid'],
                            "memory_percent": round(info['memory_percent'], 2),
                            "cpu_percent": round(info['cpu_percent'], 2)
                        })
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Sort by memory usage
            running_apps.sort(key=lambda x: x['memory_percent'], reverse=True)
            
            return running_apps[:20]  # Top 20 by memory
            
        except Exception as e:
            logger.error(f"Failed to get running apps: {e}")
            return []
    
    def _get_window_info(self) -> Dict[str, Any]:
        """Get information about current windows"""
        
        try:
            # AppleScript to get window count and titles
            script = '''
            tell application "System Events"
                set frontApp to first application process whose frontmost is true
                set windowCount to count of windows of frontApp
                set windowTitles to {}
                repeat with i from 1 to (count of windows of frontApp)
                    try
                        set windowTitle to title of window i of frontApp
                        if windowTitle is not "" then
                            set end of windowTitles to windowTitle
                        end if
                    end try
                end repeat
                return (windowCount as string) & "|" & (my join(windowTitles, ";;"))
            end tell
            
            on join(lst, delimiter)
                set AppleScript's text item delimiters to delimiter
                set result to lst as string
                set AppleScript's text item delimiters to ""
                return result
            end join
            '''
            
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                output = result.stdout.strip()
                if "|" in output:
                    count_str, titles_str = output.split("|", 1)
                    window_titles = titles_str.split(";;") if titles_str else []
                    
                    return {
                        "window_count": int(count_str) if count_str.isdigit() else 0,
                        "window_titles": [title for title in window_titles if title],
                        "has_multiple_windows": int(count_str) > 1 if count_str.isdigit() else False
                    }
            
            return {"window_count": 0, "window_titles": [], "has_multiple_windows": False}
            
        except Exception as e:
            logger.error(f"Failed to get window info: {e}")
            return {}
    
    def _get_productivity_metrics(self) -> Dict[str, Any]:
        """Calculate productivity metrics based on app usage"""
        
        try:
            current_app = self._get_current_app()
            app_name = current_app.get("name", "").lower()
            
            # Categorize applications
            productivity_apps = {
                "development": ["xcode", "visual studio code", "cursor", "sublime text", "pycharm", "intellij", "atom", "vim", "terminal", "iterm"],
                "communication": ["slack", "discord", "zoom", "teams", "skype", "facetime", "messages"],
                "browsing": ["safari", "chrome", "firefox", "edge", "arc"],
                "design": ["figma", "sketch", "adobe", "photoshop", "illustrator"],
                "productivity": ["notion", "obsidian", "bear", "notes", "pages", "word", "excel", "powerpoint"],
                "entertainment": ["spotify", "music", "netflix", "youtube", "twitch", "steam", "games"],
                "system": ["finder", "system preferences", "activity monitor", "console"]
            }
            
            current_category = "other"
            for category, apps in productivity_apps.items():
                if any(app in app_name for app in apps):
                    current_category = category
                    break
            
            # Calculate focus score (simple heuristic)
            focus_score = self._calculate_focus_score(current_category)
            
            return {
                "current_app_category": current_category,
                "focus_score": focus_score,
                "is_productive": current_category in ["development", "productivity", "design"],
                "productivity_categories": productivity_apps,
                "distraction_level": "low" if focus_score > 7 else "medium" if focus_score > 4 else "high"
            }
            
        except Exception as e:
            logger.error(f"Failed to get productivity metrics: {e}")
            return {}
    
    def _calculate_focus_score(self, category: str) -> int:
        """Calculate focus score (1-10) based on current activity"""
        
        scores = {
            "development": 9,
            "productivity": 8,
            "design": 8,
            "communication": 6,
            "browsing": 4,
            "system": 5,
            "entertainment": 2,
            "other": 5
        }
        
        return scores.get(category, 5)
    
    def _get_battery_info(self) -> Dict[str, Any]:
        """Get battery information for laptops"""
        
        try:
            battery = psutil.sensors_battery()
            
            if battery:
                return {
                    "percent": battery.percent,
                    "charging": battery.power_plugged,
                    "time_left": str(timedelta(seconds=battery.secsleft)) if battery.secsleft != psutil.POWER_TIME_UNLIMITED else "Unknown"
                }
            else:
                return {"percent": None, "charging": None, "time_left": "No battery"}
                
        except Exception as e:
            logger.error(f"Failed to get battery info: {e}")
            return {}
    
    def _get_network_activity(self) -> Dict[str, Any]:
        """Get network usage statistics"""
        
        try:
            net_io = psutil.net_io_counters()
            
            return {
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv,
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv,
                "mb_sent": round(net_io.bytes_sent / (1024 * 1024), 2),
                "mb_recv": round(net_io.bytes_recv / (1024 * 1024), 2)
            }
            
        except Exception as e:
            logger.error(f"Failed to get network activity: {e}")
            return {}
    
    def _get_memory_usage(self) -> Dict[str, Any]:
        """Get memory usage statistics"""
        
        try:
            memory = psutil.virtual_memory()
            
            return {
                "total_gb": round(memory.total / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "used_gb": round(memory.used / (1024**3), 2),
                "percent": memory.percent,
                "free_gb": round(memory.free / (1024**3), 2)
            }
            
        except Exception as e:
            logger.error(f"Failed to get memory usage: {e}")
            return {}
    
    def _get_cpu_usage(self) -> Dict[str, Any]:
        """Get CPU usage statistics"""
        
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            return {
                "cpu_percent": cpu_percent,
                "cpu_count": cpu_count,
                "cpu_freq_current": cpu_freq.current if cpu_freq else None,
                "cpu_freq_max": cpu_freq.max if cpu_freq else None,
                "load_average": list(psutil.getloadavg()) if hasattr(psutil, 'getloadavg') else []
            }
            
        except Exception as e:
            logger.error(f"Failed to get CPU usage: {e}")
            return {}
    
    def _estimate_screen_time(self) -> Dict[str, Any]:
        """Estimate daily screen time (simplified version)"""
        
        try:
            # This is a basic estimation - in a real implementation,
            # you'd track this over time
            current_hour = datetime.now().hour
            
            # Assume user has been active if system uptime > 1 hour
            uptime_result = subprocess.run(
                ["sysctl", "-n", "kern.boottime"], 
                capture_output=True, 
                text=True
            )
            
            estimated_hours = min(current_hour, 12)  # Cap at 12 hours
            
            return {
                "estimated_hours_today": estimated_hours,
                "current_session_active": True,
                "break_recommended": estimated_hours > 8,
                "note": "This is a basic estimation. Enable Screen Time for accurate data."
            }
            
        except Exception as e:
            logger.error(f"Failed to estimate screen time: {e}")
            return {}

def fetch_mac_stats() -> Dict[str, Any]:
    """Main function to fetch macOS statistics"""
    
    logger.module_start("macOS Stats")
    
    fetcher = MacStatsFetcher()
    data = fetcher.fetch_mac_stats()
    
    # Add analysis
    if "stats" not in data or data.get("error"):
        logger.module_complete("macOS Stats")
        return data
    
    stats = data
    
    # Calculate productivity insights
    analysis = {
        "system_health": _analyze_system_health(stats),
        "productivity_insights": _analyze_productivity(stats),
        "resource_usage": _analyze_resource_usage(stats),
        "recommendations": _generate_recommendations(stats)
    }
    
    stats["analysis"] = analysis
    
    logger.module_complete("macOS Stats")
    return stats

def _analyze_system_health(stats: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze overall system health"""
    
    memory = stats.get("memory_usage", {})
    cpu = stats.get("cpu_usage", {})
    battery = stats.get("battery_info", {})
    
    health_score = 10
    issues = []
    
    # Memory check
    if memory.get("percent", 0) > 80:
        health_score -= 3
        issues.append("High memory usage")
    
    # CPU check
    if cpu.get("cpu_percent", 0) > 80:
        health_score -= 2
        issues.append("High CPU usage")
    
    # Battery check
    if battery.get("percent") and battery["percent"] < 20 and not battery.get("charging"):
        health_score -= 2
        issues.append("Low battery")
    
    return {
        "health_score": max(0, health_score),
        "status": "good" if health_score >= 8 else "warning" if health_score >= 5 else "critical",
        "issues": issues
    }

def _analyze_productivity(stats: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze productivity patterns"""
    
    productivity = stats.get("productivity_metrics", {})
    windows = stats.get("window_info", {})
    
    insights = []
    
    if productivity.get("is_productive"):
        insights.append("Currently in a productive application")
    
    if windows.get("has_multiple_windows"):
        insights.append(f"Managing {windows.get('window_count', 0)} windows - consider focusing on fewer tasks")
    
    focus_score = productivity.get("focus_score", 5)
    if focus_score >= 8:
        insights.append("High focus activity detected")
    elif focus_score <= 3:
        insights.append("Potentially distracting activity")
    
    return {
        "current_focus_score": focus_score,
        "insights": insights,
        "distraction_level": productivity.get("distraction_level", "medium")
    }

def _analyze_resource_usage(stats: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze system resource usage"""
    
    memory = stats.get("memory_usage", {})
    cpu = stats.get("cpu_usage", {})
    running_apps = stats.get("running_apps", [])
    
    # Find top resource consumers
    top_memory_apps = sorted(running_apps, key=lambda x: x.get("memory_percent", 0), reverse=True)[:3]
    top_cpu_apps = sorted(running_apps, key=lambda x: x.get("cpu_percent", 0), reverse=True)[:3]
    
    return {
        "memory_status": "high" if memory.get("percent", 0) > 80 else "normal",
        "cpu_status": "high" if cpu.get("cpu_percent", 0) > 80 else "normal",
        "top_memory_apps": [app["name"] for app in top_memory_apps],
        "top_cpu_apps": [app["name"] for app in top_cpu_apps],
        "total_running_apps": len(running_apps)
    }

def _generate_recommendations(stats: Dict[str, Any]) -> List[str]:
    """Generate actionable recommendations"""
    
    recommendations = []
    
    # Memory recommendations
    memory = stats.get("memory_usage", {})
    if memory.get("percent", 0) > 85:
        recommendations.append("💾 Consider closing unused applications to free up memory")
    
    # Battery recommendations
    battery = stats.get("battery_info", {})
    if battery.get("percent") and battery["percent"] < 15:
        recommendations.append("🔋 Battery is low - consider plugging in your charger")
    
    # Productivity recommendations
    screen_time = stats.get("screen_time", {})
    if screen_time.get("break_recommended"):
        recommendations.append("🧘 You've been active for a while - consider taking a break")
    
    # Window management
    windows = stats.get("window_info", {})
    if windows.get("window_count", 0) > 10:
        recommendations.append("🪟 Many windows open - consider organizing your workspace")
    
    return recommendations

if __name__ == "__main__":
    # Test the module
    import pprint
    data = fetch_mac_stats()
    pprint.pprint(data) 