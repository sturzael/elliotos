"""
Google Calendar Integration for ElliotOS
Fetches today's and tomorrow's events from all connected calendars
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config.settings import settings
from utils.logger import get_logger

logger = get_logger("fetch_calendar")

class GoogleCalendarFetcher:
    """Fetches calendar events from Google Calendar API"""
    
    SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
    TOKEN_FILE = settings.DATA_DIR / "calendar_token.json"
    
    def __init__(self):
        self.service = None
        self.credentials = None
        
    def authenticate(self) -> bool:
        """Authenticate with Google Calendar API"""
        
        if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
            logger.feature_disabled("Google Calendar", "Missing client credentials")
            return False
        
        # Load existing credentials
        if self.TOKEN_FILE.exists():
            self.credentials = Credentials.from_authorized_user_file(
                str(self.TOKEN_FILE), self.SCOPES
            )
        
        # Refresh or get new credentials
        if not self.credentials or not self.credentials.valid:
            if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                try:
                    self.credentials.refresh(Request())
                    logger.success("Refreshed Google Calendar credentials")
                except Exception as e:
                    logger.error(f"Failed to refresh credentials: {e}")
                    return self._get_new_credentials()
            else:
                return self._get_new_credentials()
        
        # Save credentials
        self._save_credentials()
        
        # Build service
        try:
            self.service = build('calendar', 'v3', credentials=self.credentials)
            logger.success("Google Calendar service initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to build calendar service: {e}")
            return False
    
    def _get_new_credentials(self) -> bool:
        """Get new credentials through OAuth flow"""
        try:
            # Create credentials info
            client_config = {
                "installed": {
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [settings.GOOGLE_REDIRECT_URI]
                }
            }
            
            flow = InstalledAppFlow.from_client_config(client_config, self.SCOPES)
            self.credentials = flow.run_local_server(port=8080)
            logger.success("Obtained new Google Calendar credentials")
            return True
            
        except Exception as e:
            logger.error(f"OAuth flow failed: {e}")
            return False
    
    def _save_credentials(self):
        """Save credentials to file"""
        try:
            with open(self.TOKEN_FILE, 'w') as token_file:
                token_file.write(self.credentials.to_json())
        except Exception as e:
            logger.error(f"Failed to save credentials: {e}")
    
    def fetch_events(self) -> Dict[str, Any]:
        """Fetch today's and tomorrow's calendar events"""
        
        if not self.authenticate():
            return {"error": "Authentication failed", "events": []}
        
        try:
            # Get time range (today and tomorrow)
            now = datetime.now()
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            tomorrow_end = (today_start + timedelta(days=2)).replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Format for API
            time_min = today_start.isoformat() + 'Z'
            time_max = tomorrow_end.isoformat() + 'Z'
            
            # Fetch events from primary calendar
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=time_min,
                timeMax=time_max,
                maxResults=50,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Process events
            processed_events = []
            for event in events:
                processed_event = self._process_event(event, today_start)
                if processed_event:
                    processed_events.append(processed_event)
            
            # Get calendar list for additional calendars
            additional_events = self._fetch_additional_calendars(time_min, time_max, today_start)
            processed_events.extend(additional_events)
            
            # Sort by start time
            processed_events.sort(key=lambda x: x['start_datetime'])
            
            result = {
                "total_events": len(processed_events),
                "today_events": [e for e in processed_events if e['is_today']],
                "tomorrow_events": [e for e in processed_events if not e['is_today']],
                "events": processed_events,
                "fetched_at": datetime.now().isoformat()
            }
            
            logger.data_fetched("Google Calendar", len(processed_events))
            return result
            
        except HttpError as e:
            logger.api_error("Google Calendar", str(e))
            return {"error": str(e), "events": []}
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {"error": str(e), "events": []}
    
    def _fetch_additional_calendars(self, time_min: str, time_max: str, today_start: datetime) -> List[Dict]:
        """Fetch events from additional calendars"""
        
        additional_events = []
        
        try:
            # Get calendar list
            calendar_list = self.service.calendarList().list().execute()
            
            for calendar in calendar_list.get('items', []):
                calendar_id = calendar['id']
                
                # Skip primary calendar (already fetched)
                if calendar_id == 'primary':
                    continue
                
                # Skip if calendar is hidden
                if calendar.get('selected', True) is False:
                    continue
                
                try:
                    events_result = self.service.events().list(
                        calendarId=calendar_id,
                        timeMin=time_min,
                        timeMax=time_max,
                        maxResults=20,
                        singleEvents=True,
                        orderBy='startTime'
                    ).execute()
                    
                    events = events_result.get('items', [])
                    
                    for event in events:
                        processed_event = self._process_event(event, today_start, calendar['summary'])
                        if processed_event:
                            additional_events.append(processed_event)
                            
                except HttpError as e:
                    logger.warning(f"Failed to fetch from calendar {calendar['summary']}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Failed to fetch additional calendars: {e}")
        
        return additional_events
    
    def _process_event(self, event: Dict, today_start: datetime, calendar_name: str = "Primary") -> Optional[Dict]:
        """Process a single calendar event"""
        
        try:
            # Get event details
            summary = event.get('summary', 'Untitled Event')
            description = event.get('description', '')
            location = event.get('location', '')
            
            # Handle start/end times
            start = event['start']
            end = event['end']
            
            # All-day events
            if 'date' in start:
                start_dt = datetime.fromisoformat(start['date']).replace(hour=0, minute=0)
                end_dt = datetime.fromisoformat(end['date']).replace(hour=23, minute=59)
                is_all_day = True
            else:
                # Timed events
                start_dt = datetime.fromisoformat(start['dateTime'].replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end['dateTime'].replace('Z', '+00:00'))
                is_all_day = False
            
            # Determine if event is today
            is_today = start_dt.date() == today_start.date()
            
            # Calculate duration
            duration_minutes = int((end_dt - start_dt).total_seconds() / 60)
            
            return {
                "id": event['id'],
                "title": summary,
                "description": description,
                "location": location,
                "calendar": calendar_name,
                "start_datetime": start_dt,
                "end_datetime": end_dt,
                "start_time": start_dt.strftime('%I:%M %p') if not is_all_day else 'All Day',
                "end_time": end_dt.strftime('%I:%M %p') if not is_all_day else 'All Day',
                "is_all_day": is_all_day,
                "duration_minutes": duration_minutes,
                "is_today": is_today,
                "day": "Today" if is_today else "Tomorrow",
                "attendees": len(event.get('attendees', [])),
                "link": event.get('htmlLink', ''),
                "meeting_url": self._extract_meeting_url(description),
                "status": event.get('status', 'confirmed'),
                "created": event.get('created', ''),
                "updated": event.get('updated', '')
            }
            
        except Exception as e:
            logger.error(f"Failed to process event: {e}")
            return None
    
    def _extract_meeting_url(self, description: str) -> Optional[str]:
        """Extract meeting URL from event description"""
        
        if not description:
            return None
        
        # Common meeting URL patterns
        patterns = [
            r'https://[a-zA-Z0-9.-]+\.zoom\.us/[a-zA-Z0-9/?=&-]+',
            r'https://teams\.microsoft\.com/[a-zA-Z0-9/?=&-]+',
            r'https://meet\.google\.com/[a-zA-Z0-9-]+',
            r'https://[a-zA-Z0-9.-]+\.webex\.com/[a-zA-Z0-9/?=&-]+',
        ]
        
        import re
        for pattern in patterns:
            match = re.search(pattern, description)
            if match:
                return match.group(0)
        
        return None
    
    def get_next_event(self) -> Optional[Dict]:
        """Get the next upcoming event"""
        
        events_data = self.fetch_events()
        events = events_data.get("events", [])
        
        now = datetime.now()
        
        for event in events:
            if event["start_datetime"] > now:
                return event
        
        return None
    
    def get_conflicts(self) -> List[Dict]:
        """Detect scheduling conflicts"""
        
        events_data = self.fetch_events()
        events = events_data.get("events", [])
        
        conflicts = []
        
        for i, event1 in enumerate(events):
            for event2 in events[i+1:]:
                # Check for overlap
                if (event1["start_datetime"] < event2["end_datetime"] and 
                    event1["end_datetime"] > event2["start_datetime"]):
                    
                    conflicts.append({
                        "event1": event1["title"],
                        "event2": event2["title"],
                        "overlap_start": max(event1["start_datetime"], event2["start_datetime"]),
                        "overlap_end": min(event1["end_datetime"], event2["end_datetime"])
                    })
        
        return conflicts

def fetch_calendar_data() -> Dict[str, Any]:
    """Main function to fetch calendar data"""
    
    logger.module_start("Google Calendar")
    
    fetcher = GoogleCalendarFetcher()
    data = fetcher.fetch_events()
    
    # Add analysis
    if "events" in data:
        events = data["events"]
        
        # Calculate busy time
        total_busy_minutes = sum(e["duration_minutes"] for e in events if not e["is_all_day"])
        
        # Find conflicts
        conflicts = fetcher.get_conflicts()
        
        # Next event
        next_event = fetcher.get_next_event()
        
        data.update({
            "analysis": {
                "total_busy_hours": round(total_busy_minutes / 60, 1),
                "conflicts": conflicts,
                "next_event": next_event,
                "meeting_count": len([e for e in events if e["attendees"] > 1]),
                "all_day_count": len([e for e in events if e["is_all_day"]])
            }
        })
    
    logger.module_complete("Google Calendar")
    return data

if __name__ == "__main__":
    # Test the module
    import pprint
    data = fetch_calendar_data()
    pprint.pprint(data) 