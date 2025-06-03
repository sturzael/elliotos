"""
Gmail Integration for ElliotOS
Fetches unread and important emails from multiple Gmail accounts
"""

import base64
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from email.mime.text import MIMEText

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config.settings import settings
from utils.logger import get_logger

logger = get_logger("fetch_gmail")

class GmailFetcher:
    """Fetches emails from Gmail API"""
    
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.modify'
    ]
    TOKEN_FILE = settings.DATA_DIR / "gmail_token.json"
    
    def __init__(self):
        self.service = None
        self.credentials = None
        
    def authenticate(self) -> bool:
        """Authenticate with Gmail API"""
        
        if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
            logger.feature_disabled("Gmail", "Missing client credentials")
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
                    logger.success("Refreshed Gmail credentials")
                except Exception as e:
                    logger.error(f"Failed to refresh credentials: {e}")
                    return self._get_new_credentials()
            else:
                return self._get_new_credentials()
        
        # Save credentials
        self._save_credentials()
        
        # Build service
        try:
            self.service = build('gmail', 'v1', credentials=self.credentials)
            logger.success("Gmail service initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to build Gmail service: {e}")
            return False
    
    def _get_new_credentials(self) -> bool:
        """Get new credentials through OAuth flow"""
        try:
            # Ensure redirect URI has trailing slash for OAuth library
            redirect_uri = settings.GOOGLE_REDIRECT_URI
            if not redirect_uri.endswith('/'):
                redirect_uri += '/'
                
            client_config = {
                "installed": {
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [redirect_uri]
                }
            }
            
            flow = InstalledAppFlow.from_client_config(client_config, self.SCOPES)
            # Force consent to get refresh token
            flow.redirect_uri = redirect_uri
            self.credentials = flow.run_local_server(port=8083, prompt='consent')
            logger.success("Obtained new Gmail credentials")
            
            # Save credentials immediately
            self._save_credentials()
            
            # Build service with new credentials
            try:
                self.service = build('gmail', 'v1', credentials=self.credentials)
                logger.success("Gmail service initialized with new credentials")
                return True
            except Exception as e:
                logger.error(f"Failed to build Gmail service with new credentials: {e}")
                return False
            
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
    
    def fetch_emails(self) -> Dict[str, Any]:
        """Fetch recent unread and important emails"""
        
        if not self.authenticate():
            return {"error": "Authentication failed", "emails": []}
        
        try:
            # Fetch unread emails
            unread_emails = self._fetch_unread_emails()
            
            # Fetch important/starred emails
            important_emails = self._fetch_important_emails()
            
            # Fetch recent sent emails
            sent_emails = self._fetch_recent_sent()
            
            # Combine and deduplicate
            all_emails = []
            email_ids = set()
            
            for email_list in [unread_emails, important_emails, sent_emails]:
                for email in email_list:
                    if email['id'] not in email_ids:
                        all_emails.append(email)
                        email_ids.add(email['id'])
            
            # Sort by date
            all_emails.sort(key=lambda x: x['timestamp'], reverse=True)
            
            # Extract project correlations
            all_emails = self._add_project_correlations(all_emails)
            
            # Generate email summaries
            email_summaries = self._generate_email_summaries(all_emails[:10])  # Top 10 emails
            
            # Get account info
            profile = self.service.users().getProfile(userId='me').execute()
            
            result = {
                "account": profile.get('emailAddress', 'Unknown'),
                "total_emails": len(all_emails),
                "unread_count": len(unread_emails),
                "important_count": len(important_emails),
                "sent_count": len(sent_emails),
                "emails": all_emails[:20],  # Limit to 20 most recent
                "email_summaries": email_summaries,
                "fetched_at": datetime.now().isoformat()
            }
            
            logger.data_fetched("Gmail", len(all_emails))
            return result
            
        except HttpError as e:
            logger.api_error("Gmail", str(e))
            return {"error": str(e), "emails": []}
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {"error": str(e), "emails": []}
    
    def _fetch_unread_emails(self) -> List[Dict]:
        """Fetch unread emails from last 24 hours"""
        
        # Calculate time filter (last 24 hours)
        yesterday = datetime.now() - timedelta(days=1)
        query = f'is:unread after:{yesterday.strftime("%Y/%m/%d")}'
        
        return self._fetch_emails_by_query(query, max_results=10)
    
    def _fetch_important_emails(self) -> List[Dict]:
        """Fetch important/starred emails from last week"""
        
        last_week = datetime.now() - timedelta(days=7)
        query = f'(is:starred OR is:important) after:{last_week.strftime("%Y/%m/%d")}'
        
        return self._fetch_emails_by_query(query, max_results=5)
    
    def _fetch_recent_sent(self) -> List[Dict]:
        """Fetch recent sent emails"""
        
        today = datetime.now()
        query = f'in:sent after:{today.strftime("%Y/%m/%d")}'
        
        return self._fetch_emails_by_query(query, max_results=3)
    
    def _fetch_emails_by_query(self, query: str, max_results: int = 10) -> List[Dict]:
        """Fetch emails by Gmail search query"""
        
        try:
            # Search for messages
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            
            emails = []
            for message in messages:
                email_data = self._get_email_details(message['id'])
                if email_data:
                    emails.append(email_data)
            
            return emails
            
        except Exception as e:
            logger.error(f"Failed to fetch emails with query '{query}': {e}")
            return []
    
    def _get_email_details(self, message_id: str) -> Optional[Dict]:
        """Get detailed information about a specific email"""
        
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            headers = message['payload'].get('headers', [])
            header_dict = {h['name']: h['value'] for h in headers}
            
            # Extract body
            body = self._extract_email_body(message['payload'])
            
            # Get labels
            labels = message.get('labelIds', [])
            
            # Parse date
            date_str = header_dict.get('Date', '')
            timestamp = self._parse_email_date(date_str)
            
            return {
                "id": message_id,
                "thread_id": message.get('threadId', ''),
                "subject": header_dict.get('Subject', 'No Subject'),
                "from": header_dict.get('From', 'Unknown Sender'),
                "to": header_dict.get('To', ''),
                "cc": header_dict.get('Cc', ''),
                "date": date_str,
                "timestamp": timestamp,
                "body_preview": body[:200] + "..." if len(body) > 200 else body,
                "body": body,
                "labels": labels,
                "is_unread": 'UNREAD' in labels,
                "is_important": 'IMPORTANT' in labels,
                "is_starred": 'STARRED' in labels,
                "is_sent": 'SENT' in labels,
                "snippet": message.get('snippet', ''),
                "size_estimate": message.get('sizeEstimate', 0),
                "has_attachments": self._has_attachments(message['payload'])
            }
            
        except Exception as e:
            logger.error(f"Failed to get email details for {message_id}: {e}")
            return None
    
    def _extract_email_body(self, payload: Dict) -> str:
        """Extract email body from payload"""
        
        body = ""
        
        # Handle multipart messages
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    if 'data' in part['body']:
                        body += base64.urlsafe_b64decode(
                            part['body']['data']
                        ).decode('utf-8', errors='ignore')
                elif part['mimeType'] == 'text/html' and not body:
                    if 'data' in part['body']:
                        html_body = base64.urlsafe_b64decode(
                            part['body']['data']
                        ).decode('utf-8', errors='ignore')
                        body = self._html_to_text(html_body)
        else:
            # Single part message
            if payload['mimeType'] == 'text/plain':
                if 'data' in payload['body']:
                    body = base64.urlsafe_b64decode(
                        payload['body']['data']
                    ).decode('utf-8', errors='ignore')
            elif payload['mimeType'] == 'text/html':
                if 'data' in payload['body']:
                    html_body = base64.urlsafe_b64decode(
                        payload['body']['data']
                    ).decode('utf-8', errors='ignore')
                    body = self._html_to_text(html_body)
        
        return body.strip()
    
    def _html_to_text(self, html: str) -> str:
        """Convert HTML to plain text"""
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', html)
        
        # Decode HTML entities
        import html as html_module
        text = html_module.unescape(text)
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def _has_attachments(self, payload: Dict) -> bool:
        """Check if email has attachments"""
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part.get('filename'):
                    return True
                # Check nested parts
                if 'parts' in part:
                    if self._has_attachments(part):
                        return True
        
        return False
    
    def _parse_email_date(self, date_str: str) -> datetime:
        """Parse email date string to datetime"""
        
        try:
            from email.utils import parsedate_to_datetime
            dt = parsedate_to_datetime(date_str)
            # Convert to naive datetime for consistent comparison
            if dt.tzinfo is not None:
                dt = dt.replace(tzinfo=None)
            return dt
        except Exception:
            return datetime.now()
    
    def get_email_stats(self) -> Dict[str, Any]:
        """Get email statistics"""
        
        try:
            # Get label list
            labels_result = self.service.users().labels().list(userId='me').execute()
            labels = labels_result.get('labels', [])
            
            stats = {}
            
            for label in labels:
                if label['name'] in ['INBOX', 'UNREAD', 'STARRED', 'IMPORTANT', 'SENT']:
                    stats[label['name'].lower()] = {
                        'messages_total': label.get('messagesTotal', 0),
                        'messages_unread': label.get('messagesUnread', 0)
                    }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get email stats: {e}")
            return {}
    
    def _add_project_correlations(self, emails: List[Dict]) -> List[Dict]:
        """Add project correlations to emails by analyzing content"""
        
        try:
            # Try to get ClickUp project names
            from backend.fetch_clickup import ClickUpFetcher
            clickup_fetcher = ClickUpFetcher()
            project_names = clickup_fetcher.get_project_names()
        except Exception as e:
            logger.warning(f"Could not fetch ClickUp projects for correlation: {e}")
            project_names = []
        
        # Common project-related keywords to look for
        project_keywords = [
            "project", "task", "milestone", "deadline", "deliverable",
            "sprint", "epic", "feature", "bug", "issue", "ticket",
            "development", "design", "testing", "deployment", "release"
        ]
        
        for email in emails:
            email_content = (
                email.get("subject", "") + " " + 
                email.get("body", "") + " " + 
                email.get("from", "")
            ).lower()
            
            # Look for ClickUp project matches
            matched_projects = []
            for project_name in project_names:
                if project_name.lower() in email_content:
                    matched_projects.append(project_name)
            
            # Extract potential project names using patterns
            extracted_projects = self._extract_project_names(email_content)
            
            # Look for project-related keywords
            found_keywords = [kw for kw in project_keywords if kw in email_content]
            
            # Add correlation data to email
            email["project_correlation"] = {
                "clickup_projects": matched_projects,
                "extracted_projects": extracted_projects,
                "project_keywords": found_keywords,
                "is_project_related": len(matched_projects) > 0 or len(extracted_projects) > 0 or len(found_keywords) > 0
            }
        
        return emails
    
    def _extract_project_names(self, content: str) -> List[str]:
        """Extract potential project names from email content using patterns"""
        
        project_patterns = [
            # "Project X", "Project Name"
            r'project\s+([a-zA-Z0-9\s\-_]+?)(?:\s|$|[.,!?])',
            # "X project", "Name project"  
            r'([a-zA-Z0-9\s\-_]+?)\s+project(?:\s|$|[.,!?])',
            # "Working on X", "Update on Y"
            r'(?:working on|update on|regarding|about)\s+([a-zA-Z0-9\s\-_]+?)(?:\s|$|[.,!?])',
            # "[PROJECT]", "(PROJECT)"
            r'[\[\(]([a-zA-Z0-9\s\-_]+?)[\]\)]',
            # "Task: X", "Issue: Y"
            r'(?:task|issue|ticket|feature):\s*([a-zA-Z0-9\s\-_]+?)(?:\s|$|[.,!?])',
        ]
        
        extracted = []
        
        for pattern in project_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                # Clean up the match
                clean_match = match.strip().title()
                # Filter out common words and short matches
                if (len(clean_match) > 3 and 
                    clean_match.lower() not in ['the', 'and', 'for', 'with', 'this', 'that', 'from', 'your', 'our']):
                    extracted.append(clean_match)
        
        # Remove duplicates and limit
        return list(set(extracted))[:5]

    def _generate_email_summaries(self, emails: List[Dict]) -> List[Dict]:
        """Generate brief summaries of important emails"""
        
        summaries = []
        
        for email in emails:
            summary = {
                "subject": email.get("subject", "No Subject"),
                "from": email.get("from", "Unknown Sender"),
                "date": email.get("date", "Unknown Date"),
                "body_preview": email.get("body_preview", "No body content")
            }
            summaries.append(summary)
        
        return summaries

def fetch_gmail_data() -> Dict[str, Any]:
    """Main function to fetch Gmail data"""
    
    logger.module_start("Gmail")
    
    if not settings.GMAIL_ACCOUNTS:
        logger.feature_disabled("Gmail", "No accounts configured")
        return {"error": "No Gmail accounts configured", "emails": []}
    
    # For now, fetch from primary account
    # TODO: Implement multi-account support
    fetcher = GmailFetcher()
    data = fetcher.fetch_emails()
    
    # Add stats
    if "emails" in data:
        stats = fetcher.get_email_stats()
        data["stats"] = stats
        
        # Analyze email content
        emails = data["emails"]
        
        # Count email types
        analysis = {
            "total_unread": len([e for e in emails if e["is_unread"]]),
            "total_important": len([e for e in emails if e["is_important"]]),
            "total_starred": len([e for e in emails if e["is_starred"]]),
            "with_attachments": len([e for e in emails if e["has_attachments"]]),
            "average_size": sum(e["size_estimate"] for e in emails) / len(emails) if emails else 0,
            "top_senders": _get_top_senders(emails),
            "keyword_mentions": _find_keywords(emails)
        }
        
        data["analysis"] = analysis
    
    logger.module_complete("Gmail")
    return data

def _get_top_senders(emails: List[Dict]) -> List[Dict]:
    """Get top email senders"""
    
    sender_counts = {}
    
    for email in emails:
        sender = email.get("from", "Unknown")
        # Extract email address from "Name <email>" format
        import re
        match = re.search(r'<([^>]+)>', sender)
        if match:
            sender = match.group(1)
        
        sender_counts[sender] = sender_counts.get(sender, 0) + 1
    
    # Sort by count
    top_senders = sorted(sender_counts.items(), key=lambda x: x[1], reverse=True)
    
    return [{"sender": sender, "count": count} for sender, count in top_senders[:5]]

def _find_keywords(emails: List[Dict]) -> Dict[str, int]:
    """Find important keywords in emails"""
    
    keywords = {
        "meeting": 0,
        "deadline": 0,
        "urgent": 0,
        "asap": 0,
        "follow up": 0,
        "action required": 0,
        "schedule": 0,
        "proposal": 0,
        "invoice": 0,
        "payment": 0
    }
    
    for email in emails:
        content = (email.get("subject", "") + " " + email.get("body", "")).lower()
        
        for keyword in keywords:
            if keyword in content:
                keywords[keyword] += 1
    
    # Return only keywords that were found
    return {k: v for k, v in keywords.items() if v > 0}

if __name__ == "__main__":
    # Test the module
    import pprint
    data = fetch_gmail_data()
    pprint.pprint(data) 