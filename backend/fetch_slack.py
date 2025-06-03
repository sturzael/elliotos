"""
Slack Integration for ElliotOS
Fetches messages, mentions, and activity from multiple Slack workspaces
"""

import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import Counter

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from config.settings import settings
from utils.logger import get_logger

logger = get_logger("fetch_slack")

class SlackFetcher:
    """Fetches data from Slack API"""
    
    def __init__(self):
        self.clients = []
        self._setup_clients()
        
    def _setup_clients(self):
        """Setup Slack clients for all configured tokens"""
        
        # Bot tokens
        for token in settings.SLACK_BOT_TOKENS:
            if token:
                client = WebClient(token=token)
                try:
                    # Test the connection
                    response = client.auth_test()
                    self.clients.append({
                        "client": client,
                        "type": "bot",
                        "team": response.get("team", "Unknown"),
                        "user": response.get("user", "Unknown"),
                        "user_id": response.get("user_id", ""),
                        "team_id": response.get("team_id", "")
                    })
                    logger.success(f"Connected to Slack team: {response.get('team', 'Unknown')}")
                except SlackApiError as e:
                    logger.error(f"Failed to connect with bot token: {e}")
        
        # User tokens
        for token in settings.SLACK_USER_TOKENS:
            if token:
                client = WebClient(token=token)
                try:
                    response = client.auth_test()
                    self.clients.append({
                        "client": client,
                        "type": "user",
                        "team": response.get("team", "Unknown"),
                        "user": response.get("user", "Unknown"),
                        "user_id": response.get("user_id", ""),
                        "team_id": response.get("team_id", "")
                    })
                    logger.success(f"Connected to Slack team: {response.get('team', 'Unknown')} (user token)")
                except SlackApiError as e:
                    logger.error(f"Failed to connect with user token: {e}")
    
    def fetch_slack_data(self) -> Dict[str, Any]:
        """Fetch comprehensive Slack data from all workspaces"""
        
        if not self.clients:
            logger.feature_disabled("Slack", "No valid tokens configured")
            return {"error": "No valid Slack tokens", "workspaces": []}
        
        all_workspaces = []
        
        for client_info in self.clients:
            client = client_info["client"]
            
            try:
                workspace_data = self._fetch_workspace_data(client, client_info)
                workspace_data["team_name"] = client_info["team"]
                workspace_data["connection_type"] = client_info["type"]
                all_workspaces.append(workspace_data)
                
            except Exception as e:
                logger.error(f"Failed to fetch data from {client_info['team']}: {e}")
                continue
        
        # Aggregate data across workspaces
        aggregated = self._aggregate_workspace_data(all_workspaces)
        
        result = {
            "workspaces": all_workspaces,
            "total_workspaces": len(all_workspaces),
            "aggregated": aggregated,
            "fetched_at": datetime.now().isoformat()
        }
        
        logger.data_fetched("Slack", len(all_workspaces))
        return result
    
    def _fetch_workspace_data(self, client: WebClient, client_info: Dict) -> Dict[str, Any]:
        """Fetch data from a single Slack workspace"""
        
        # Get recent mentions
        mentions = self._get_mentions(client, client_info["user_id"])
        
        # Get unread messages
        unread_messages = self._get_unread_messages(client)
        
        # Get recent DMs
        direct_messages = self._get_recent_dms(client)
        
        # Get channel activity
        channel_activity = self._get_channel_activity(client)
        
        # Get user presence
        presence = self._get_user_presence(client, client_info["user_id"])
        
        return {
            "mentions": mentions,
            "unread_messages": unread_messages,
            "direct_messages": direct_messages,
            "channel_activity": channel_activity,
            "presence": presence,
            "user_info": {
                "user_id": client_info["user_id"],
                "username": client_info["user"]
            }
        }
    
    def _get_mentions(self, client: WebClient, user_id: str) -> List[Dict]:
        """Get recent mentions of the user"""
        
        try:
            # Calculate 24 hours ago
            yesterday = datetime.now() - timedelta(days=1)
            oldest_timestamp = str(int(yesterday.timestamp()))
            
            # Search for mentions
            response = client.search_messages(
                query=f"<@{user_id}>",
                sort="timestamp",
                sort_dir="desc",
                count=20
            )
            
            mentions = []
            if response.get("ok") and response.get("messages"):
                for match in response["messages"]["matches"]:
                    mentions.append({
                        "text": match.get("text", ""),
                        "user": match.get("user", ""),
                        "username": match.get("username", ""),
                        "channel_name": match.get("channel", {}).get("name", ""),
                        "channel_id": match.get("channel", {}).get("id", ""),
                        "timestamp": match.get("ts", ""),
                        "permalink": match.get("permalink", "")
                    })
            
            return mentions
            
        except SlackApiError as e:
            logger.error(f"Failed to get mentions: {e}")
            return []
    
    def _get_unread_messages(self, client: WebClient) -> Dict[str, Any]:
        """Get unread message counts"""
        
        try:
            # Get conversations with unread counts
            response = client.conversations_list(
                exclude_archived=True,
                limit=100
            )
            
            unread_channels = []
            total_unread = 0
            
            if response.get("ok"):
                for channel in response["channels"]:
                    if channel.get("unread_count", 0) > 0:
                        unread_channels.append({
                            "name": channel.get("name", ""),
                            "id": channel.get("id", ""),
                            "unread_count": channel.get("unread_count", 0),
                            "is_channel": channel.get("is_channel", False),
                            "is_group": channel.get("is_group", False),
                            "is_im": channel.get("is_im", False)
                        })
                        total_unread += channel.get("unread_count", 0)
            
            return {
                "total_unread": total_unread,
                "unread_channels": unread_channels[:10]  # Limit to top 10
            }
            
        except SlackApiError as e:
            logger.error(f"Failed to get unread messages: {e}")
            return {"total_unread": 0, "unread_channels": []}
    
    def _get_recent_dms(self, client: WebClient) -> List[Dict]:
        """Get recent direct messages"""
        
        try:
            # Get IM list
            response = client.conversations_list(
                types="im",
                limit=50
            )
            
            recent_dms = []
            
            if response.get("ok"):
                for im in response["channels"][:10]:  # Check last 10 DM channels
                    # Get recent messages from this DM
                    try:
                        history = client.conversations_history(
                            channel=im["id"],
                            limit=5
                        )
                        
                        if history.get("ok") and history.get("messages"):
                            latest_message = history["messages"][0]
                            
                            # Get user info
                            user_info = client.users_info(user=im["user"])
                            user_name = "Unknown"
                            if user_info.get("ok"):
                                user_name = user_info["user"].get("real_name", 
                                    user_info["user"].get("name", "Unknown"))
                            
                            recent_dms.append({
                                "user_id": im["user"],
                                "user_name": user_name,
                                "latest_message": latest_message.get("text", ""),
                                "timestamp": latest_message.get("ts", ""),
                                "message_count": len(history["messages"])
                            })
                            
                    except SlackApiError:
                        continue
            
            # Sort by timestamp
            recent_dms.sort(key=lambda x: float(x["timestamp"]), reverse=True)
            
            return recent_dms[:5]  # Return top 5
            
        except SlackApiError as e:
            logger.error(f"Failed to get recent DMs: {e}")
            return []
    
    def _get_channel_activity(self, client: WebClient) -> List[Dict]:
        """Get activity from top channels"""
        
        try:
            # Get public channels
            response = client.conversations_list(
                types="public_channel",
                exclude_archived=True,
                limit=20
            )
            
            channel_activity = []
            
            if response.get("ok"):
                for channel in response["channels"][:10]:  # Check top 10 channels
                    try:
                        # Get recent messages
                        history = client.conversations_history(
                            channel=channel["id"],
                            limit=10
                        )
                        
                        if history.get("ok") and history.get("messages"):
                            messages = history["messages"]
                            
                            # Count unique users
                            users = set()
                            for msg in messages:
                                if msg.get("user"):
                                    users.add(msg["user"])
                            
                            channel_activity.append({
                                "name": channel.get("name", ""),
                                "id": channel.get("id", ""),
                                "member_count": channel.get("num_members", 0),
                                "recent_messages": len(messages),
                                "active_users": len(users),
                                "latest_activity": messages[0].get("ts", "") if messages else ""
                            })
                            
                    except SlackApiError:
                        continue
            
            # Sort by recent activity
            channel_activity.sort(key=lambda x: float(x["latest_activity"]) if x["latest_activity"] else 0, reverse=True)
            
            return channel_activity
            
        except SlackApiError as e:
            logger.error(f"Failed to get channel activity: {e}")
            return []
    
    def _get_user_presence(self, client: WebClient, user_id: str) -> Dict[str, Any]:
        """Get user presence information"""
        
        try:
            response = client.users_getPresence(user=user_id)
            
            if response.get("ok"):
                return {
                    "presence": response.get("presence", "unknown"),
                    "online": response.get("online", False),
                    "auto_away": response.get("auto_away", False),
                    "manual_away": response.get("manual_away", False),
                    "connection_count": response.get("connection_count", 0),
                    "last_activity": response.get("last_activity", 0)
                }
            
            return {"presence": "unknown"}
            
        except SlackApiError as e:
            logger.error(f"Failed to get user presence: {e}")
            return {"presence": "unknown"}
    
    def _aggregate_workspace_data(self, workspaces: List[Dict]) -> Dict[str, Any]:
        """Aggregate data across all workspaces"""
        
        total_mentions = 0
        total_unread = 0
        total_dms = 0
        all_channel_activity = []
        
        for workspace in workspaces:
            total_mentions += len(workspace.get("mentions", []))
            total_unread += workspace.get("unread_messages", {}).get("total_unread", 0)
            total_dms += len(workspace.get("direct_messages", []))
            all_channel_activity.extend(workspace.get("channel_activity", []))
        
        # Find most active channels across workspaces
        most_active_channels = sorted(
            all_channel_activity, 
            key=lambda x: x.get("recent_messages", 0), 
            reverse=True
        )[:5]
        
        return {
            "total_mentions": total_mentions,
            "total_unread": total_unread,
            "total_recent_dms": total_dms,
            "most_active_channels": most_active_channels,
            "workspace_count": len(workspaces)
        }
    
    def get_trending_topics(self, hours: int = 24) -> List[Dict]:
        """Get trending topics/keywords from recent messages"""
        
        # This would require analyzing message content
        # For now, return placeholder
        return []

def fetch_slack_data() -> Dict[str, Any]:
    """Main function to fetch Slack data"""
    
    logger.module_start("Slack")
    
    if not settings.SLACK_BOT_TOKENS and not settings.SLACK_USER_TOKENS:
        logger.feature_disabled("Slack", "No tokens configured")
        return {"error": "No Slack tokens configured", "workspaces": []}
    
    fetcher = SlackFetcher()
    data = fetcher.fetch_slack_data()
    
    # Add analysis
    if "workspaces" in data and data["workspaces"]:
        workspaces = data["workspaces"]
        
        # Calculate engagement score
        engagement_score = 0
        for workspace in workspaces:
            mentions = len(workspace.get("mentions", []))
            unread = workspace.get("unread_messages", {}).get("total_unread", 0)
            dms = len(workspace.get("direct_messages", []))
            
            # Simple engagement calculation
            engagement_score += (mentions * 3) + (unread * 1) + (dms * 2)
        
        # Find most active workspace
        most_active_workspace = None
        max_activity = 0
        
        for workspace in workspaces:
            activity = (
                len(workspace.get("mentions", [])) +
                workspace.get("unread_messages", {}).get("total_unread", 0) +
                len(workspace.get("direct_messages", []))
            )
            if activity > max_activity:
                max_activity = activity
                most_active_workspace = workspace.get("team_name", "Unknown")
        
        data["analysis"] = {
            "engagement_score": engagement_score,
            "most_active_workspace": most_active_workspace,
            "requires_attention": engagement_score > 20,
            "summary": _generate_slack_summary(data["aggregated"])
        }
    
    logger.module_complete("Slack")
    return data

def _generate_slack_summary(aggregated: Dict[str, Any]) -> str:
    """Generate a text summary of Slack activity"""
    
    mentions = aggregated.get("total_mentions", 0)
    unread = aggregated.get("total_unread", 0)
    workspaces = aggregated.get("workspace_count", 0)
    
    if mentions == 0 and unread == 0:
        return "All caught up! No mentions or unread messages."
    
    parts = []
    
    if mentions > 0:
        parts.append(f"{mentions} mention{'s' if mentions != 1 else ''}")
    
    if unread > 0:
        parts.append(f"{unread} unread message{'s' if unread != 1 else ''}")
    
    summary = f"You have {' and '.join(parts)}"
    
    if workspaces > 1:
        summary += f" across {workspaces} workspaces"
    
    return summary + "."

if __name__ == "__main__":
    # Test the module
    import pprint
    data = fetch_slack_data()
    pprint.pprint(data) 