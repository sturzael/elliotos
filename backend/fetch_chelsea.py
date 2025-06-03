"""
Chelsea FC Integration for ElliotOS
Fetches match results, fixtures, and team news for Chelsea Football Club
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from config.settings import settings
from utils.logger import get_logger

logger = get_logger("fetch_chelsea")

class ChelseaFetcher:
    """Fetches Chelsea FC data from various sources"""
    
    def __init__(self):
        self.football_api_key = settings.FOOTBALL_API_KEY
        self.session = requests.Session()
        self.session.timeout = 10
        self.chelsea_team_id = 49  # Chelsea's team ID in most APIs
        
    def fetch_chelsea_data(self) -> Dict[str, Any]:
        """Fetch comprehensive Chelsea FC data"""
        
        if not settings.CHELSEA_FC_ENABLED:
            logger.feature_disabled("Chelsea FC", "Feature disabled in settings")
            return {"error": "Feature disabled", "chelsea_data": {}}
        
        try:
            chelsea_data = {
                "recent_matches": self._get_recent_matches(),
                "upcoming_fixtures": self._get_upcoming_fixtures(),
                "league_position": self._get_league_position(),
                "team_news": self._get_team_news(),
                "player_stats": self._get_key_player_stats(),
                "next_match": self._get_next_match(),
                "season_stats": self._get_season_stats(),
                "transfer_news": self._get_transfer_news(),
                "fetched_at": datetime.now().isoformat()
            }
            
            logger.data_fetched("Chelsea FC", len([k for k, v in chelsea_data.items() if v and k != "fetched_at"]))
            return chelsea_data
            
        except Exception as e:
            logger.error(f"Failed to fetch Chelsea data: {e}")
            return {"error": str(e), "chelsea_data": {}}
    
    def _get_recent_matches(self) -> List[Dict[str, Any]]:
        """Get recent Chelsea matches"""
        
        if self.football_api_key:
            try:
                # Try Football API first
                return self._get_matches_from_api("recent")
            except Exception as e:
                logger.error(f"API call failed: {e}")
        
        # Fallback to mock data
        return self._get_mock_recent_matches()
    
    def _get_upcoming_fixtures(self) -> List[Dict[str, Any]]:
        """Get upcoming Chelsea fixtures"""
        
        if self.football_api_key:
            try:
                return self._get_matches_from_api("upcoming")
            except Exception as e:
                logger.error(f"API call failed: {e}")
        
        return self._get_mock_upcoming_fixtures()
    
    def _get_matches_from_api(self, match_type: str) -> List[Dict[str, Any]]:
        """Get matches from Football API"""
        
        # Using Football-Data.org API structure
        url = "https://api.football-data.org/v4/teams/61/matches"  # Chelsea team ID
        
        headers = {"X-Auth-Token": self.football_api_key}
        
        # Determine date range
        if match_type == "recent":
            date_from = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            date_to = datetime.now().strftime("%Y-%m-%d")
        else:  # upcoming
            date_from = datetime.now().strftime("%Y-%m-%d")
            date_to = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        
        params = {
            "dateFrom": date_from,
            "dateTo": date_to,
            "limit": 5
        }
        
        response = self.session.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            matches = data.get("matches", [])
            
            return [self._process_match(match) for match in matches]
        else:
            logger.error(f"Football API error: {response.status_code}")
            return []
    
    def _process_match(self, match: Dict) -> Dict[str, Any]:
        """Process a match from the API"""
        
        home_team = match.get("homeTeam", {}).get("name", "")
        away_team = match.get("awayTeam", {}).get("name", "")
        
        # Determine if Chelsea is home or away
        is_home = "Chelsea" in home_team
        opponent = away_team if is_home else home_team
        
        score = match.get("score", {})
        full_time = score.get("fullTime", {})
        
        return {
            "date": match.get("utcDate", ""),
            "competition": match.get("competition", {}).get("name", ""),
            "opponent": opponent,
            "home_team": home_team,
            "away_team": away_team,
            "is_home": is_home,
            "status": match.get("status", ""),
            "chelsea_score": full_time.get("home" if is_home else "away"),
            "opponent_score": full_time.get("away" if is_home else "home"),
            "venue": match.get("venue", ""),
            "result": self._determine_result(match, is_home),
            "match_day": match.get("matchday", ""),
            "referee": match.get("referee", {}).get("name", "") if match.get("referee") else ""
        }
    
    def _determine_result(self, match: Dict, is_home: bool) -> Optional[str]:
        """Determine match result from Chelsea's perspective"""
        
        score = match.get("score", {})
        full_time = score.get("fullTime", {})
        
        home_score = full_time.get("home")
        away_score = full_time.get("away")
        
        if home_score is None or away_score is None:
            return None
        
        chelsea_score = home_score if is_home else away_score
        opponent_score = away_score if is_home else home_score
        
        if chelsea_score > opponent_score:
            return "W"
        elif chelsea_score < opponent_score:
            return "L"
        else:
            return "D"
    
    def _get_league_position(self) -> Dict[str, Any]:
        """Get Chelsea's current league position"""
        
        if self.football_api_key:
            try:
                # Get Premier League table
                url = "https://api.football-data.org/v4/competitions/PL/standings"
                headers = {"X-Auth-Token": self.football_api_key}
                
                response = self.session.get(url, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    standings = data.get("standings", [])
                    
                    if standings:
                        table = standings[0].get("table", [])
                        
                        for team in table:
                            if "Chelsea" in team.get("team", {}).get("name", ""):
                                return {
                                    "position": team.get("position", 0),
                                    "points": team.get("points", 0),
                                    "played": team.get("playedGames", 0),
                                    "won": team.get("won", 0),
                                    "drawn": team.get("draw", 0),
                                    "lost": team.get("lost", 0),
                                    "goals_for": team.get("goalsFor", 0),
                                    "goals_against": team.get("goalsAgainst", 0),
                                    "goal_difference": team.get("goalDifference", 0),
                                    "form": team.get("form", ""),
                                    "competition": "Premier League"
                                }
            except Exception as e:
                logger.error(f"Failed to get league position: {e}")
        
        # Mock data
        return {
            "position": 6,
            "points": 44,
            "played": 25,
            "won": 12,
            "drawn": 8,
            "lost": 5,
            "goals_for": 42,
            "goals_against": 35,
            "goal_difference": 7,
            "form": "WDLWW",
            "competition": "Premier League"
        }
    
    def _get_team_news(self) -> List[Dict[str, Any]]:
        """Get Chelsea team news"""
        
        # Mock team news - in reality, you'd scrape from:
        # - Chelsea's official website
        # - BBC Sport
        # - Sky Sports
        # - ESPN
        
        return [
            {
                "headline": "Pochettino confident ahead of weekend fixture",
                "summary": "Manager expresses optimism about team's recent form and upcoming challenges.",
                "type": "manager_news",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "source": "Chelsea FC Official"
            },
            {
                "headline": "Three players return to training",
                "summary": "Key players back from injury as squad depth improves.",
                "type": "injury_update",
                "date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
                "source": "Chelsea FC Official"
            }
        ]
    
    def _get_key_player_stats(self) -> List[Dict[str, Any]]:
        """Get key player statistics"""
        
        # Mock player stats - in reality, you'd get from:
        # - Official API
        # - Fantasy Premier League API
        # - Sports data providers
        
        return [
            {
                "name": "Cole Palmer",
                "position": "Midfielder",
                "goals": 8,
                "assists": 4,
                "appearances": 20,
                "rating": 7.2,
                "form": "excellent"
            },
            {
                "name": "Nicolas Jackson",
                "position": "Forward",
                "goals": 6,
                "assists": 2,
                "appearances": 18,
                "rating": 6.8,
                "form": "good"
            },
            {
                "name": "Thiago Silva",
                "position": "Defender",
                "goals": 1,
                "assists": 1,
                "appearances": 22,
                "rating": 7.5,
                "form": "excellent"
            }
        ]
    
    def _get_next_match(self) -> Optional[Dict[str, Any]]:
        """Get next Chelsea match"""
        
        upcoming = self._get_upcoming_fixtures()
        
        if upcoming:
            next_match = upcoming[0]
            
            # Calculate days until match
            match_date = datetime.fromisoformat(next_match.get("date", "").replace("Z", "+00:00"))
            days_until = (match_date - datetime.now()).days
            
            next_match["days_until"] = days_until
            next_match["countdown"] = self._format_countdown(match_date)
            
            return next_match
        
        return None
    
    def _format_countdown(self, match_date: datetime) -> str:
        """Format countdown to next match"""
        
        now = datetime.now()
        diff = match_date - now
        
        if diff.days > 0:
            return f"{diff.days} days"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hours"
        else:
            minutes = diff.seconds // 60
            return f"{minutes} minutes"
    
    def _get_season_stats(self) -> Dict[str, Any]:
        """Get Chelsea's season statistics"""
        
        return {
            "premier_league": {
                "position": 6,
                "points": 44,
                "top_scorer": "Cole Palmer (8 goals)",
                "clean_sheets": 8,
                "disciplinary": {"yellow_cards": 45, "red_cards": 2}
            },
            "all_competitions": {
                "total_matches": 35,
                "wins": 18,
                "draws": 10,
                "losses": 7,
                "goals_scored": 58,
                "goals_conceded": 42
            },
            "home_form": "Strong - 8W 3D 1L",
            "away_form": "Mixed - 4W 5D 4L"
        }
    
    def _get_transfer_news(self) -> List[Dict[str, Any]]:
        """Get Chelsea transfer news"""
        
        return [
            {
                "headline": "Chelsea monitoring midfielder situation",
                "type": "rumor",
                "reliability": "medium",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "source": "Sky Sports"
            },
            {
                "headline": "Young player linked with loan move",
                "type": "outgoing_rumor",
                "reliability": "low",
                "date": (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d"),
                "source": "The Athletic"
            }
        ]
    
    def _get_mock_recent_matches(self) -> List[Dict[str, Any]]:
        """Mock recent matches for testing"""
        
        return [
            {
                "date": (datetime.now() - timedelta(days=7)).isoformat(),
                "competition": "Premier League",
                "opponent": "Manchester United",
                "home_team": "Chelsea",
                "away_team": "Manchester United",
                "is_home": True,
                "status": "FINISHED",
                "chelsea_score": 2,
                "opponent_score": 1,
                "venue": "Stamford Bridge",
                "result": "W",
                "match_day": 25
            },
            {
                "date": (datetime.now() - timedelta(days=14)).isoformat(),
                "competition": "Premier League",
                "opponent": "Liverpool",
                "home_team": "Liverpool",
                "away_team": "Chelsea",
                "is_home": False,
                "status": "FINISHED",
                "chelsea_score": 1,
                "opponent_score": 1,
                "venue": "Anfield",
                "result": "D",
                "match_day": 24
            }
        ]
    
    def _get_mock_upcoming_fixtures(self) -> List[Dict[str, Any]]:
        """Mock upcoming fixtures for testing"""
        
        return [
            {
                "date": (datetime.now() + timedelta(days=5)).isoformat(),
                "competition": "Premier League",
                "opponent": "Arsenal",
                "home_team": "Arsenal",
                "away_team": "Chelsea",
                "is_home": False,
                "status": "SCHEDULED",
                "chelsea_score": None,
                "opponent_score": None,
                "venue": "Emirates Stadium",
                "result": None,
                "match_day": 26
            },
            {
                "date": (datetime.now() + timedelta(days=12)).isoformat(),
                "competition": "Premier League",
                "opponent": "Brighton",
                "home_team": "Chelsea",
                "away_team": "Brighton",
                "is_home": True,
                "status": "SCHEDULED",
                "chelsea_score": None,
                "opponent_score": None,
                "venue": "Stamford Bridge",
                "result": None,
                "match_day": 27
            }
        ]

def fetch_chelsea_data() -> Dict[str, Any]:
    """Main function to fetch Chelsea FC data"""
    
    logger.module_start("Chelsea FC")
    
    fetcher = ChelseaFetcher()
    data = fetcher.fetch_chelsea_data()
    
    # Add analysis
    if "chelsea_data" not in data or data.get("error"):
        logger.module_complete("Chelsea FC")
        return data
    
    chelsea_data = data
    
    # Calculate Chelsea insights
    analysis = {
        "form_analysis": _analyze_recent_form(chelsea_data),
        "season_summary": _generate_season_summary(chelsea_data),
        "next_match_preview": _generate_next_match_preview(chelsea_data),
        "key_metrics": _calculate_key_metrics(chelsea_data),
        "fan_sentiment": _assess_fan_sentiment(chelsea_data)
    }
    
    chelsea_data["analysis"] = analysis
    
    logger.module_complete("Chelsea FC")
    return chelsea_data

def _analyze_recent_form(chelsea_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze Chelsea's recent form"""
    
    recent_matches = chelsea_data.get("recent_matches", [])
    
    if not recent_matches:
        return {"form": "unknown", "trend": "unknown"}
    
    results = [match.get("result") for match in recent_matches if match.get("result")]
    
    wins = results.count("W")
    draws = results.count("D")
    losses = results.count("L")
    
    form_string = "".join(results[-5:])  # Last 5 results
    
    # Determine trend
    if len(results) >= 3:
        recent_form = results[-3:]
        if recent_form.count("W") >= 2:
            trend = "improving"
        elif recent_form.count("L") >= 2:
            trend = "declining"
        else:
            trend = "stable"
    else:
        trend = "unknown"
    
    return {
        "form": form_string,
        "wins": wins,
        "draws": draws,
        "losses": losses,
        "trend": trend,
        "win_percentage": round((wins / len(results)) * 100, 1) if results else 0
    }

def _generate_season_summary(chelsea_data: Dict[str, Any]) -> str:
    """Generate a season summary"""
    
    league_pos = chelsea_data.get("league_position", {})
    position = league_pos.get("position", "Unknown")
    points = league_pos.get("points", 0)
    
    season_stats = chelsea_data.get("season_stats", {})
    premier_league = season_stats.get("premier_league", {})
    top_scorer = premier_league.get("top_scorer", "Unknown")
    
    return f"Currently {position}th in Premier League with {points} points. {top_scorer} leading scorer."

def _generate_next_match_preview(chelsea_data: Dict[str, Any]) -> str:
    """Generate next match preview"""
    
    next_match = chelsea_data.get("next_match")
    
    if not next_match:
        return "No upcoming fixtures scheduled"
    
    opponent = next_match.get("opponent", "Unknown")
    is_home = next_match.get("is_home", False)
    days_until = next_match.get("days_until", 0)
    competition = next_match.get("competition", "")
    
    venue = "at Stamford Bridge" if is_home else f"away to {opponent}"
    
    return f"Next: {opponent} {venue} in {days_until} days ({competition})"

def _calculate_key_metrics(chelsea_data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate key performance metrics"""
    
    league_pos = chelsea_data.get("league_position", {})
    recent_matches = chelsea_data.get("recent_matches", [])
    
    # Goals per game
    total_goals = sum(match.get("chelsea_score", 0) for match in recent_matches if match.get("chelsea_score") is not None)
    games_played = len([m for m in recent_matches if m.get("chelsea_score") is not None])
    goals_per_game = round(total_goals / games_played, 1) if games_played > 0 else 0
    
    return {
        "league_position": league_pos.get("position", 0),
        "points": league_pos.get("points", 0),
        "goal_difference": league_pos.get("goal_difference", 0),
        "recent_goals_per_game": goals_per_game,
        "clean_sheets": league_pos.get("clean_sheets", 0) if "clean_sheets" in league_pos else 0
    }

def _assess_fan_sentiment(chelsea_data: Dict[str, Any]) -> str:
    """Assess fan sentiment based on recent performance"""
    
    form_analysis = _analyze_recent_form(chelsea_data)
    league_pos = chelsea_data.get("league_position", {})
    
    position = league_pos.get("position", 10)
    win_percentage = form_analysis.get("win_percentage", 0)
    trend = form_analysis.get("trend", "unknown")
    
    if position <= 4 and win_percentage >= 60:
        return "optimistic"
    elif position <= 6 and trend == "improving":
        return "hopeful"
    elif position > 10 or win_percentage < 30:
        return "concerned"
    else:
        return "cautious"

if __name__ == "__main__":
    # Test the module
    import pprint
    data = fetch_chelsea_data()
    pprint.pprint(data) 