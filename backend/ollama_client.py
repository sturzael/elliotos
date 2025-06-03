"""
Ollama Client for ElliotOS
Interface to local Ollama models with fallback to cloud providers
"""

import requests
import json
from typing import Dict, Any, Optional, List
from datetime import datetime

from config.settings import settings
from utils.logger import get_logger

logger = get_logger("ollama_client")

class OllamaClient:
    """Client for interacting with local Ollama models"""
    
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
        self.session = requests.Session()
        self.session.timeout = 30
        
    def check_availability(self) -> bool:
        """Check if Ollama is running and accessible"""
        try:
            response = self.session.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama not accessible: {e}")
            return False
    
    def check_model(self) -> bool:
        """Check if the specified model is available"""
        try:
            response = self.session.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [model["name"] for model in models]
                return self.model in model_names
            return False
        except requests.exceptions.RequestException:
            return False
    
    def generate_response(self, prompt: str, context_data: Dict[str, Any] = None) -> str:
        """Generate AI response using Ollama"""
        
        if not self.check_availability():
            logger.error("Ollama is not available")
            return self._fallback_response(prompt, context_data)
        
        if not self.check_model():
            logger.warning(f"Model {self.model} not found, trying to pull...")
            if not self._pull_model():
                return self._fallback_response(prompt, context_data)
        
        # Construct the full prompt with context
        full_prompt = self._build_prompt(prompt, context_data)
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "max_tokens": 2000,
                    }
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "No response generated")
            else:
                logger.error(f"Ollama API error: {response.status_code}")
                return self._fallback_response(prompt, context_data)
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            return self._fallback_response(prompt, context_data)
    
    def _build_prompt(self, base_prompt: str, context_data: Dict[str, Any] = None) -> str:
        """Build comprehensive prompt with context data"""
        
        current_time = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")
        
        prompt_parts = [
            f"You are ElliotOS, Elliot's personal AI assistant. Current time: {current_time}",
            "",
            "Your personality: Helpful, insightful, slightly witty, and motivational. Use emojis appropriately.",
            "",
            "CONTEXT DATA:"
        ]
        
        if context_data:
            prompt_parts.append(json.dumps(context_data, indent=2, default=str))
        else:
            prompt_parts.append("No context data available")
        
        prompt_parts.extend([
            "",
            "INSTRUCTIONS:",
            base_prompt,
            "",
            "Format your response for Slack with:",
            "- Clear sections with emojis",
            "- Bullet points for lists",
            "- Bold text for emphasis (*bold*)",
            "- Keep it concise but informative",
            "- Include actionable insights when possible"
        ])
        
        return "\n".join(prompt_parts)
    
    def _pull_model(self) -> bool:
        """Attempt to pull the specified model"""
        try:
            logger.info(f"Pulling model: {self.model}")
            response = self.session.post(
                f"{self.base_url}/api/pull",
                json={"name": self.model}
            )
            return response.status_code == 200
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to pull model: {e}")
            return False
    
    def _fallback_response(self, prompt: str, context_data: Dict[str, Any] = None) -> str:
        """Generate fallback response when Ollama is unavailable"""
        
        # Try OpenAI fallback
        if settings.OPENAI_API_KEY:
            return self._openai_fallback(prompt, context_data)
        
        # Try Anthropic fallback
        if settings.ANTHROPIC_API_KEY:
            return self._anthropic_fallback(prompt, context_data)
        
        # Basic template response
        return self._template_response(context_data)
    
    def _openai_fallback(self, prompt: str, context_data: Dict[str, Any] = None) -> str:
        """Fallback to OpenAI API"""
        try:
            import openai
            openai.api_key = settings.OPENAI_API_KEY
            
            full_prompt = self._build_prompt(prompt, context_data)
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": full_prompt}],
                max_tokens=1500,
                temperature=0.7
            )
            
            logger.success("Used OpenAI fallback")
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI fallback failed: {e}")
            return self._template_response(context_data)
    
    def _anthropic_fallback(self, prompt: str, context_data: Dict[str, Any] = None) -> str:
        """Fallback to Anthropic API"""
        try:
            import anthropic
            
            client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            full_prompt = self._build_prompt(prompt, context_data)
            
            response = client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1500,
                messages=[{"role": "user", "content": full_prompt}]
            )
            
            logger.success("Used Anthropic fallback")
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Anthropic fallback failed: {e}")
            return self._template_response(context_data)
    
    def _template_response(self, context_data: Dict[str, Any] = None) -> str:
        """Generate basic template response when all AI options fail"""
        
        current_time = datetime.now().strftime("%I:%M %p")
        
        response_parts = [
            f"🤖 *ElliotOS Daily Summary* - {current_time}",
            "",
            "⚠️ *AI services temporarily unavailable - using basic summary*",
            ""
        ]
        
        if context_data:
            # Basic data summary
            if "calendar" in context_data:
                events = context_data["calendar"]
                if events:
                    response_parts.extend([
                        "📅 *Today's Schedule:*",
                        f"• {len(events)} events scheduled"
                    ])
            
            if "health" in context_data:
                health = context_data["health"]
                if health.get("steps"):
                    response_parts.append(f"👟 Steps: {health['steps']}")
                if health.get("sleep_hours"):
                    response_parts.append(f"😴 Sleep: {health['sleep_hours']} hours")
            
            if "slack" in context_data:
                slack = context_data["slack"]
                if slack.get("unread_count"):
                    response_parts.append(f"💬 Unread messages: {slack['unread_count']}")
        
        response_parts.extend([
            "",
            "✨ *Focus for today:* Make progress on your priorities",
            "🎯 *Remember:* Small consistent steps lead to big results"
        ])
        
        return "\n".join(response_parts)
    
    def generate_morning_digest(self, context_data: Dict[str, Any]) -> str:
        """Generate morning digest with specific prompt"""
        
        prompt = """
        Generate a personalized morning digest for Elliot based ONLY on the actual data provided in the context.
        
        IMPORTANT: Do NOT make up or invent any information. Only use data that exists in the context.
        
        Structure:
        1. 🌅 *Good Morning* greeting with current time
        2. 📅 *Today's Agenda* - ONLY if calendar data exists, otherwise say "No calendar events configured"
        3. 📧 *Messages* - ONLY if email/Slack data exists, otherwise skip this section
        4. 💪 *Health Check* - Use actual health data from context (steps, sleep, activity)
        5. 💻 *Current Activity* - Use actual macOS stats (current app, productivity metrics)
        6. ⚽ *Chelsea FC* - Use actual Chelsea data from context
        7. 🌍 *News* - Use actual news headlines from context
        8. 🎯 *Daily Focus* - Based on actual productivity data and current activity
        9. 💡 *Motivation* - One encouraging insight based on actual data
        
        If a data source is missing or has errors, acknowledge it honestly rather than making up content.
        Keep it energizing but truthful!
        """
        
        return self.generate_response(prompt, context_data)
    
    def generate_evening_digest(self, context_data: Dict[str, Any]) -> str:
        """Generate evening digest with specific prompt"""
        
        prompt = """
        Generate a personalized evening digest for Elliot based ONLY on the actual data provided in the context.
        
        IMPORTANT: Do NOT make up or invent any information. Only use data that exists in the context.
        
        Structure:
        1. 🌙 *Good Evening* greeting with current time
        2. ✅ *Today's Activity* - Based on actual macOS usage and productivity data
        3. 📊 *Health Summary* - Use actual health data (steps, activity, sleep patterns)
        4. 💻 *Productivity Review* - Based on actual app usage and focus metrics
        5. 🔄 *Tomorrow Preview* - ONLY if calendar data exists, otherwise skip
        6. ⚽ *Chelsea Update* - Use actual Chelsea data from context
        7. 🌍 *News Recap* - Use actual news headlines from context
        8. 🧘 *Wellness Check* - Based on actual productivity and health metrics
        9. 🌟 *Reflection* - Positive insight based on actual data from the day
        
        If a data source is missing or has errors, acknowledge it honestly rather than making up content.
        Keep it reflective and encouraging based on real achievements!
        """
        
        return self.generate_response(prompt, context_data)

# Global client instance
ollama_client = OllamaClient() 