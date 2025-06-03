"""
ClickUp Integration for ElliotOS
Fetches tasks, projects, and workspace data from ClickUp API
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import re

from config.settings import settings
from utils.logger import get_logger

logger = get_logger("fetch_clickup")

class ClickUpFetcher:
    """Fetches data from ClickUp API"""
    
    BASE_URL = "https://api.clickup.com/api/v2"
    
    def __init__(self):
        self.headers = {
            "Authorization": settings.CLICKUP_API_TOKEN,
            "Content-Type": "application/json"
        }
        self.teams = []
        self.spaces = []
        self.projects = []
    
    def authenticate(self) -> bool:
        """Test ClickUp API authentication"""
        
        if not settings.CLICKUP_API_TOKEN:
            logger.feature_disabled("ClickUp", "Missing API token")
            return False
        
        try:
            response = requests.get(
                f"{self.BASE_URL}/user",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                user_data = response.json()
                logger.success(f"Connected to ClickUp as: {user_data['user']['username']}")
                return True
            else:
                logger.error(f"ClickUp authentication failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"ClickUp connection failed: {e}")
            return False
    
    def fetch_workspace_data(self) -> Dict[str, Any]:
        """Fetch comprehensive workspace data"""
        
        if not self.authenticate():
            return {"error": "Authentication failed"}
        
        try:
            # Get teams (workspaces)
            teams_response = requests.get(
                f"{self.BASE_URL}/team",
                headers=self.headers,
                timeout=10
            )
            
            if teams_response.status_code != 200:
                return {"error": f"Failed to fetch teams: {teams_response.status_code}"}
            
            self.teams = teams_response.json()["teams"]
            
            all_data = {
                "teams": [],
                "recent_tasks": [],
                "project_summary": {},
                "activity_summary": {},
                "fetched_at": datetime.now().isoformat()
            }
            
            # Process each team
            for team in self.teams:
                team_data = self._fetch_team_data(team["id"])
                all_data["teams"].append(team_data)
                
                # Aggregate recent tasks
                all_data["recent_tasks"].extend(team_data.get("recent_tasks", []))
            
            # Sort recent tasks by date
            all_data["recent_tasks"].sort(
                key=lambda x: x.get("date_updated", ""), 
                reverse=True
            )
            all_data["recent_tasks"] = all_data["recent_tasks"][:20]  # Limit to 20 most recent
            
            # Generate project summary
            all_data["project_summary"] = self._generate_project_summary(all_data["teams"])
            
            logger.data_fetched("ClickUp", len(all_data["recent_tasks"]))
            return all_data
            
        except Exception as e:
            logger.error(f"Failed to fetch ClickUp data: {e}")
            return {"error": str(e)}
    
    def _fetch_team_data(self, team_id: str) -> Dict[str, Any]:
        """Fetch data for a specific team"""
        
        try:
            # Get spaces for this team
            spaces_response = requests.get(
                f"{self.BASE_URL}/team/{team_id}/space",
                headers=self.headers,
                timeout=10
            )
            
            team_data = {
                "id": team_id,
                "spaces": [],
                "recent_tasks": [],
                "task_counts": {"total": 0, "open": 0, "in_progress": 0, "completed": 0}
            }
            
            if spaces_response.status_code == 200:
                spaces = spaces_response.json()["spaces"]
                
                for space in spaces:
                    space_data = self._fetch_space_data(space["id"])
                    team_data["spaces"].append(space_data)
                    team_data["recent_tasks"].extend(space_data.get("recent_tasks", []))
                    
                    # Aggregate task counts
                    for status, count in space_data.get("task_counts", {}).items():
                        team_data["task_counts"][status] += count
            
            return team_data
            
        except Exception as e:
            logger.error(f"Failed to fetch team {team_id} data: {e}")
            return {"id": team_id, "error": str(e)}
    
    def _fetch_space_data(self, space_id: str) -> Dict[str, Any]:
        """Fetch data for a specific space"""
        
        try:
            # Get folders/projects in this space
            folders_response = requests.get(
                f"{self.BASE_URL}/space/{space_id}/folder",
                headers=self.headers,
                timeout=10
            )
            
            # Get tasks in this space (last 7 days)
            date_filter = int((datetime.now() - timedelta(days=7)).timestamp() * 1000)
            tasks_response = requests.get(
                f"{self.BASE_URL}/space/{space_id}/task",
                headers=self.headers,
                params={
                    "date_updated_gt": date_filter,
                    "include_closed": "true",
                    "page": 0
                },
                timeout=10
            )
            
            space_data = {
                "id": space_id,
                "folders": [],
                "recent_tasks": [],
                "task_counts": {"total": 0, "open": 0, "in_progress": 0, "completed": 0}
            }
            
            # Process folders
            if folders_response.status_code == 200:
                folders = folders_response.json()["folders"]
                space_data["folders"] = [
                    {"id": f["id"], "name": f["name"]} 
                    for f in folders
                ]
            
            # Process tasks
            if tasks_response.status_code == 200:
                tasks = tasks_response.json()["tasks"]
                
                for task in tasks:
                    task_data = self._process_task(task)
                    space_data["recent_tasks"].append(task_data)
                    
                    # Count task statuses
                    status = task_data["status"].lower()
                    space_data["task_counts"]["total"] += 1
                    
                    if "complete" in status or "done" in status:
                        space_data["task_counts"]["completed"] += 1
                    elif "progress" in status or "doing" in status:
                        space_data["task_counts"]["in_progress"] += 1
                    else:
                        space_data["task_counts"]["open"] += 1
            
            return space_data
            
        except Exception as e:
            logger.error(f"Failed to fetch space {space_id} data: {e}")
            return {"id": space_id, "error": str(e)}
    
    def _process_task(self, task: Dict) -> Dict[str, Any]:
        """Process a single task into standardized format"""
        
        return {
            "id": task["id"],
            "name": task["name"],
            "status": task["status"]["status"],
            "priority": task.get("priority", {}).get("priority", "normal") if task.get("priority") else "normal",
            "assignees": [a["username"] for a in task.get("assignees", [])],
            "due_date": task.get("due_date"),
            "date_created": task.get("date_created"),
            "date_updated": task.get("date_updated"),
            "url": task["url"],
            "folder_name": task.get("folder", {}).get("name", "No Folder"),
            "space_name": task.get("space", {}).get("name", "No Space"),
            "tags": [tag["name"] for tag in task.get("tags", [])],
            "description": task.get("description", "")[:200] + "..." if len(task.get("description", "")) > 200 else task.get("description", "")
        }
    
    def _generate_project_summary(self, teams: List[Dict]) -> Dict[str, Any]:
        """Generate summary of projects and their status"""
        
        summary = {
            "total_projects": 0,
            "active_projects": 0,
            "total_tasks": 0,
            "completed_tasks": 0,
            "overdue_tasks": 0,
            "high_priority_tasks": 0,
            "project_list": []
        }
        
        for team in teams:
            for space in team.get("spaces", []):
                for folder in space.get("folders", []):
                    summary["total_projects"] += 1
                    summary["project_list"].append({
                        "name": folder["name"],
                        "id": folder["id"],
                        "team": team["id"]
                    })
                
                # Aggregate task statistics
                task_counts = space.get("task_counts", {})
                summary["total_tasks"] += task_counts.get("total", 0)
                summary["completed_tasks"] += task_counts.get("completed", 0)
                
                # Count high priority and overdue tasks
                for task in space.get("recent_tasks", []):
                    if task.get("priority") == "high":
                        summary["high_priority_tasks"] += 1
                    
                    if task.get("due_date"):
                        due_date = datetime.fromtimestamp(int(task["due_date"]) / 1000)
                        if due_date < datetime.now() and task["status"].lower() not in ["complete", "done"]:
                            summary["overdue_tasks"] += 1
        
        return summary
    
    def get_project_names(self) -> List[str]:
        """Get list of all project names for email correlation"""
        
        project_names = []
        
        try:
            data = self.fetch_workspace_data()
            
            for team in data.get("teams", []):
                for space in team.get("spaces", []):
                    for folder in space.get("folders", []):
                        project_names.append(folder["name"])
            
            return project_names
            
        except Exception as e:
            logger.error(f"Failed to get project names: {e}")
            return []

def fetch_clickup_data() -> Dict[str, Any]:
    """Main function to fetch ClickUp data"""
    
    logger.module_start("ClickUp")
    
    fetcher = ClickUpFetcher()
    data = fetcher.fetch_workspace_data()
    
    logger.module_complete("ClickUp")
    return data

if __name__ == "__main__":
    # Test the module
    import pprint
    data = fetch_clickup_data()
    pprint.pprint(data) 