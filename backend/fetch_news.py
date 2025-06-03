"""
News Integration for ElliotOS
Fetches world headlines and news from various sources
"""

import requests
import feedparser
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin

from config.settings import settings
from utils.logger import get_logger

logger = get_logger("fetch_news")

class NewsFetcher:
    """Fetches news from various sources"""
    
    def __init__(self):
        self.news_api_key = settings.NEWS_API_KEY
        self.session = requests.Session()
        self.session.timeout = 10
        
    def fetch_news_data(self) -> Dict[str, Any]:
        """Fetch comprehensive news data"""
        
        try:
            news_data = {
                "headlines": self._get_top_headlines(),
                "tech_news": self._get_tech_news(),
                "business_news": self._get_business_news(),
                "world_news": self._get_world_news(),
                "trending_topics": self._get_trending_topics(),
                "rss_feeds": self._get_rss_feeds(),
                "fetched_at": datetime.now().isoformat()
            }
            
            # Count total articles
            total_articles = sum(
                len(news_data[key]) for key in news_data 
                if isinstance(news_data[key], list)
            )
            
            logger.data_fetched("News", total_articles)
            return news_data
            
        except Exception as e:
            logger.error(f"Failed to fetch news data: {e}")
            return {"error": str(e), "news": []}
    
    def _get_top_headlines(self) -> List[Dict[str, Any]]:
        """Get top headlines from NewsAPI"""
        
        if not self.news_api_key:
            logger.warning("No NewsAPI key - using mock headlines")
            return self._get_mock_headlines()
        
        try:
            url = "https://newsapi.org/v2/top-headlines"
            params = {
                "apiKey": self.news_api_key,
                "country": "us",
                "pageSize": 10,
                "category": "general"
            }
            
            response = self.session.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                articles = data.get("articles", [])
                
                return [self._process_article(article, "Top Headlines") for article in articles]
            else:
                logger.error(f"NewsAPI error: {response.status_code}")
                return self._get_mock_headlines()
                
        except Exception as e:
            logger.error(f"Failed to fetch top headlines: {e}")
            return self._get_mock_headlines()
    
    def _get_tech_news(self) -> List[Dict[str, Any]]:
        """Get technology news"""
        
        if not self.news_api_key:
            return self._get_mock_tech_news()
        
        try:
            url = "https://newsapi.org/v2/top-headlines"
            params = {
                "apiKey": self.news_api_key,
                "category": "technology",
                "pageSize": 5
            }
            
            response = self.session.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                articles = data.get("articles", [])
                
                return [self._process_article(article, "Technology") for article in articles]
            else:
                return self._get_mock_tech_news()
                
        except Exception as e:
            logger.error(f"Failed to fetch tech news: {e}")
            return self._get_mock_tech_news()
    
    def _get_business_news(self) -> List[Dict[str, Any]]:
        """Get business news"""
        
        if not self.news_api_key:
            return self._get_mock_business_news()
        
        try:
            url = "https://newsapi.org/v2/top-headlines"
            params = {
                "apiKey": self.news_api_key,
                "category": "business",
                "pageSize": 5
            }
            
            response = self.session.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                articles = data.get("articles", [])
                
                return [self._process_article(article, "Business") for article in articles]
            else:
                return self._get_mock_business_news()
                
        except Exception as e:
            logger.error(f"Failed to fetch business news: {e}")
            return self._get_mock_business_news()
    
    def _get_world_news(self) -> List[Dict[str, Any]]:
        """Get world news from multiple sources"""
        
        # Try BBC RSS feed as backup
        try:
            bbc_feed = feedparser.parse("http://feeds.bbci.co.uk/news/world/rss.xml")
            articles = []
            
            for entry in bbc_feed.entries[:5]:
                articles.append({
                    "title": entry.title,
                    "description": entry.summary if hasattr(entry, 'summary') else "",
                    "url": entry.link,
                    "source": "BBC News",
                    "category": "World",
                    "published_at": entry.published if hasattr(entry, 'published') else "",
                    "author": entry.author if hasattr(entry, 'author') else "BBC News"
                })
            
            return articles
            
        except Exception as e:
            logger.error(f"Failed to fetch world news: {e}")
            return self._get_mock_world_news()
    
    def _get_trending_topics(self) -> List[Dict[str, Any]]:
        """Get trending topics (simplified)"""
        
        # Mock trending topics - in a real implementation, you'd analyze:
        # - Twitter trends
        # - Google Trends
        # - Reddit trending
        # - News headline analysis
        
        return [
            {"topic": "AI Development", "mentions": 1250, "trend": "rising"},
            {"topic": "Climate Change", "mentions": 890, "trend": "stable"},
            {"topic": "Cryptocurrency", "mentions": 750, "trend": "falling"},
            {"topic": "Space Exploration", "mentions": 620, "trend": "rising"},
            {"topic": "Healthcare", "mentions": 580, "trend": "stable"}
        ]
    
    def _get_rss_feeds(self) -> List[Dict[str, Any]]:
        """Get articles from RSS feeds"""
        
        rss_feeds = [
            {"name": "TechCrunch", "url": "https://techcrunch.com/feed/"},
            {"name": "Hacker News", "url": "https://hnrss.org/frontpage"},
            {"name": "Reuters", "url": "https://www.reuters.com/rssFeed/topNews"}
        ]
        
        all_articles = []
        
        for feed_info in rss_feeds:
            try:
                feed = feedparser.parse(feed_info["url"])
                
                for entry in feed.entries[:3]:  # Limit to 3 per feed
                    article = {
                        "title": entry.title,
                        "description": entry.summary if hasattr(entry, 'summary') else "",
                        "url": entry.link,
                        "source": feed_info["name"],
                        "category": "RSS",
                        "published_at": entry.published if hasattr(entry, 'published') else "",
                        "author": entry.author if hasattr(entry, 'author') else feed_info["name"]
                    }
                    all_articles.append(article)
                    
            except Exception as e:
                logger.error(f"Failed to fetch RSS feed {feed_info['name']}: {e}")
                continue
        
        return all_articles
    
    def _process_article(self, article: Dict, category: str) -> Dict[str, Any]:
        """Process a NewsAPI article"""
        
        return {
            "title": article.get("title", ""),
            "description": article.get("description", ""),
            "url": article.get("url", ""),
            "source": article.get("source", {}).get("name", "Unknown"),
            "category": category,
            "published_at": article.get("publishedAt", ""),
            "author": article.get("author", ""),
            "url_to_image": article.get("urlToImage", ""),
            "content": article.get("content", "")
        }
    
    def _get_mock_headlines(self) -> List[Dict[str, Any]]:
        """Mock headlines for testing"""
        
        return [
            {
                "title": "Major Tech Conference Announces AI Breakthroughs",
                "description": "Leading technology companies unveil new artificial intelligence capabilities at industry conference.",
                "url": "https://example.com/tech-ai-breakthroughs",
                "source": "Tech News",
                "category": "Technology",
                "published_at": datetime.now().isoformat(),
                "author": "Tech Reporter"
            },
            {
                "title": "Global Climate Summit Reaches New Agreements",
                "description": "World leaders agree on ambitious new climate targets at international summit.",
                "url": "https://example.com/climate-summit",
                "source": "World News",
                "category": "Environment",
                "published_at": (datetime.now() - timedelta(hours=2)).isoformat(),
                "author": "Environment Reporter"
            },
            {
                "title": "Stock Markets Show Mixed Results",
                "description": "Major indices close with varied performance amid economic uncertainty.",
                "url": "https://example.com/stock-markets",
                "source": "Financial Times",
                "category": "Business",
                "published_at": (datetime.now() - timedelta(hours=4)).isoformat(),
                "author": "Financial Reporter"
            }
        ]
    
    def _get_mock_tech_news(self) -> List[Dict[str, Any]]:
        """Mock tech news"""
        
        return [
            {
                "title": "New Programming Language Gains Developer Interest",
                "description": "Emerging language promises better performance and easier syntax.",
                "url": "https://example.com/new-programming-language",
                "source": "Developer News",
                "category": "Technology",
                "published_at": datetime.now().isoformat(),
                "author": "Dev Reporter"
            }
        ]
    
    def _get_mock_business_news(self) -> List[Dict[str, Any]]:
        """Mock business news"""
        
        return [
            {
                "title": "Major Tech Company Reports Strong Quarterly Earnings",
                "description": "Revenue exceeds expectations driven by cloud and AI services.",
                "url": "https://example.com/quarterly-earnings",
                "source": "Business Weekly",
                "category": "Business",
                "published_at": datetime.now().isoformat(),
                "author": "Business Reporter"
            }
        ]
    
    def _get_mock_world_news(self) -> List[Dict[str, Any]]:
        """Mock world news"""
        
        return [
            {
                "title": "International Space Station Welcomes New Crew",
                "description": "Astronauts from multiple countries begin six-month mission.",
                "url": "https://example.com/space-station-crew",
                "source": "Space News",
                "category": "World",
                "published_at": datetime.now().isoformat(),
                "author": "Space Reporter"
            }
        ]

def fetch_news_data() -> Dict[str, Any]:
    """Main function to fetch news data"""
    
    logger.module_start("News")
    
    fetcher = NewsFetcher()
    data = fetcher.fetch_news_data()
    
    # Add analysis
    if "error" not in data:
        analysis = {
            "news_summary": _generate_news_summary(data),
            "top_sources": _get_top_sources(data),
            "categories": _analyze_categories(data),
            "urgency_level": _assess_urgency(data),
            "reading_time": _estimate_reading_time(data)
        }
        
        data["analysis"] = analysis
    
    logger.module_complete("News")
    return data

def _generate_news_summary(news_data: Dict[str, Any]) -> str:
    """Generate a brief news summary"""
    
    total_articles = 0
    categories = set()
    
    for key, articles in news_data.items():
        if isinstance(articles, list) and key != "trending_topics":
            total_articles += len(articles)
            for article in articles:
                categories.add(article.get("category", "General"))
    
    trending = news_data.get("trending_topics", [])
    top_trend = trending[0]["topic"] if trending else "No trends"
    
    return f"{total_articles} articles across {len(categories)} categories. Top trend: {top_trend}"

def _get_top_sources(news_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get top news sources by article count"""
    
    source_counts = {}
    
    for key, articles in news_data.items():
        if isinstance(articles, list) and key != "trending_topics":
            for article in articles:
                source = article.get("source", "Unknown")
                source_counts[source] = source_counts.get(source, 0) + 1
    
    # Sort by count
    top_sources = sorted(source_counts.items(), key=lambda x: x[1], reverse=True)
    
    return [{"source": source, "articles": count} for source, count in top_sources[:5]]

def _analyze_categories(news_data: Dict[str, Any]) -> Dict[str, int]:
    """Analyze article distribution by category"""
    
    categories = {}
    
    for key, articles in news_data.items():
        if isinstance(articles, list) and key != "trending_topics":
            for article in articles:
                category = article.get("category", "General")
                categories[category] = categories.get(category, 0) + 1
    
    return categories

def _assess_urgency(news_data: Dict[str, Any]) -> str:
    """Assess overall news urgency level"""
    
    urgent_keywords = ["breaking", "urgent", "crisis", "emergency", "alert"]
    urgent_count = 0
    total_articles = 0
    
    for key, articles in news_data.items():
        if isinstance(articles, list) and key != "trending_topics":
            for article in articles:
                total_articles += 1
                title = article.get("title", "").lower()
                description = article.get("description", "").lower()
                
                if any(keyword in title or keyword in description for keyword in urgent_keywords):
                    urgent_count += 1
    
    if total_articles == 0:
        return "low"
    
    urgency_ratio = urgent_count / total_articles
    
    if urgency_ratio > 0.3:
        return "high"
    elif urgency_ratio > 0.1:
        return "medium"
    else:
        return "low"

def _estimate_reading_time(news_data: Dict[str, Any]) -> Dict[str, int]:
    """Estimate reading time for news"""
    
    total_articles = 0
    
    for key, articles in news_data.items():
        if isinstance(articles, list) and key != "trending_topics":
            total_articles += len(articles)
    
    # Estimate 2 minutes per article (title + description reading)
    estimated_minutes = total_articles * 2
    
    return {
        "total_articles": total_articles,
        "estimated_minutes": estimated_minutes,
        "quick_scan_minutes": max(1, total_articles // 3)  # Quick scan time
    }

if __name__ == "__main__":
    # Test the module
    import pprint
    data = fetch_news_data()
    pprint.pprint(data) 