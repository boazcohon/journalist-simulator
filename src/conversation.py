"""Conversation management for journalist chat interactions."""

import os
from datetime import datetime
from typing import Dict, List, Any, Tuple
from dotenv import load_dotenv
import anthropic
from .config import get_model_for_task, estimate_cost

# Load environment variables
load_dotenv()


class ConversationManager:
    """Manages conversation state and interactions with journalists."""
    
    def __init__(self, journalist_data: Dict[str, Any]):
        """Initialize conversation with journalist data."""
        self.journalist = journalist_data
        self.messages: List[Dict[str, str]] = []
        self.start_time = datetime.now()
        self.total_cost = 0.0
        
    def add_message(self, role: str, content: str) -> None:
        """Add a message to the conversation history."""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_conversation_context(self) -> str:
        """Build conversation context for the AI."""
        context = "Previous conversation:\n"
        for msg in self.messages[-10:]:  # Last 10 messages for context
            role = "You" if msg["role"] == "assistant" else "User"
            context += f"{role}: {msg['content']}\n"
        return context
    
    def generate_response(self, user_message: str) -> Tuple[str, float]:
        """Generate a journalist response based on their personality and context."""
        # Add user message to history
        self.add_message("user", user_message)
        
        # Build the prompt
        conversation_context = self.get_conversation_context() if self.messages else ""
        
        prompt = f"""You are {self.journalist['name']}, a journalist at {self.journalist['publication']} covering {self.journalist['beat']}.

PERSONALITY AND STYLE:
{self.journalist['system_prompt']}

RESPONSE PATTERNS:
- Base response rate: {self.journalist['base_response_rate']:.1%} (affects your enthusiasm)
- Keywords that interest you: {', '.join(self.journalist['keyword_triggers'][:5])}
- You value: exclusive stories, data-driven insights, timely information

{conversation_context}

Current message from PR professional: {user_message}

Respond as this journalist would, maintaining their personality and communication style. Consider:
1. Their beat relevance
2. The quality of information provided
3. Their typical response patterns
4. Previous context in the conversation

Keep responses conversational but professional. If the pitch is off-beat or generic, be politely dismissive. If it's highly relevant with exclusive/breaking news, show appropriate interest."""

        try:
            client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            model = get_model_for_task("conversation")
            
            response = client.messages.create(
                model=model,
                max_tokens=500,
                temperature=0.8,
                system="You are a professional journalist. Respond authentically based on your publication, beat, and personality.",
                messages=[{"role": "user", "content": prompt}]
            )
            
            journalist_response = response.content[0].text
            
            # Calculate cost
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            cost = estimate_cost(model, input_tokens, output_tokens)
            self.total_cost += cost
            
            # Add response to history
            self.add_message("assistant", journalist_response)
            
            return journalist_response, cost
            
        except Exception as e:
            error_msg = f"Error generating response: {str(e)}"
            return error_msg, 0.0
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get a summary of the conversation."""
        return {
            "journalist": self.journalist['name'],
            "publication": self.journalist['publication'],
            "message_count": len(self.messages),
            "duration": (datetime.now() - self.start_time).total_seconds() / 60,  # in minutes
            "total_cost": self.total_cost,
            "messages": self.messages
        }
    
    def assess_engagement_level(self) -> str:
        """Assess how engaged the journalist is based on conversation."""
        if not self.messages:
            return "No engagement yet"
        
        # Look at recent journalist responses
        journalist_responses = [m['content'] for m in self.messages if m['role'] == 'assistant']
        if not journalist_responses:
            return "No responses yet"
        
        last_response = journalist_responses[-1].lower()
        
        # Simple engagement assessment based on response patterns
        # Check low interest first (more specific phrases)
        low_interest_phrases = ["not interested", "doesn't fit", "pass", "no thanks", "busy"]
        if any(phrase in last_response for phrase in low_interest_phrases):
            return "🔴 Low Interest"
        
        # Then check high interest
        high_interest_phrases = ["tell me more", "very interested", "exclusive", "let's talk", "call me", "follow up"]
        if any(phrase in last_response for phrase in high_interest_phrases):
            return "🟢 High Interest"
        
        # Then medium interest
        medium_interest_phrases = ["perhaps", "maybe", "could be", "send me", "more information"]
        if any(phrase in last_response for phrase in medium_interest_phrases):
            return "🟡 Medium Interest"
        
        return "🟡 Neutral"