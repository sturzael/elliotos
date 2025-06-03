#!/usr/bin/env python3
"""
Simple Gmail authentication test
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.fetch_gmail import GmailFetcher
from utils.logger import get_logger

logger = get_logger("gmail_test")

def test_gmail_auth():
    """Test Gmail authentication"""
    
    print("🧪 Testing Gmail Authentication...")
    print("=" * 50)
    
    try:
        # Create Gmail fetcher
        fetcher = GmailFetcher()
        
        # Test authentication
        print("📧 Starting Gmail authentication...")
        success = fetcher.authenticate()
        
        if success:
            print("✅ Gmail authentication successful!")
            
            # Try to fetch some basic info
            try:
                profile = fetcher.service.users().getProfile(userId='me').execute()
                email = profile.get('emailAddress', 'Unknown')
                print(f"📬 Connected to: {email}")
                
                # Get basic stats
                stats = fetcher.get_email_stats()
                if stats:
                    print("📊 Email Stats:")
                    for label, data in stats.items():
                        print(f"  - {label}: {data}")
                
            except Exception as e:
                print(f"⚠️  Could not fetch profile: {e}")
            
        else:
            print("❌ Gmail authentication failed")
            
    except Exception as e:
        print(f"💥 Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_gmail_auth() 