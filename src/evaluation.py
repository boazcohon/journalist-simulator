import re
import os
from typing import Dict, Any, Tuple
from dotenv import load_dotenv
import anthropic
from .config import get_model_for_task, estimate_cost

# Load environment variables
load_dotenv()


def calculate_response_likelihood(pitch: str, journalist_data: Dict[str, Any]) -> float:
    """
    Calculate the likelihood that a journalist will respond to a pitch.
    
    Args:
        pitch: The pitch text to evaluate
        journalist_data: Journalist persona data with response factors
        
    Returns:
        Float between 0 and 1 representing response likelihood (capped at 0.85)
    """
    likelihood = journalist_data.get("base_response_rate", 0.1)
    
    # Get response factors, default to empty dict if not present
    response_factors = journalist_data.get("response_factors", {})
    
    # Apply timing factors
    timing_factors = response_factors.get("timing", {})
    likelihood = _apply_timing_factors(pitch, likelihood, timing_factors)
    
    # Apply relevance factors
    relevance_factors = response_factors.get("relevance", {})
    likelihood = _apply_relevance_factors(pitch, likelihood, relevance_factors)
    
    # Apply quality factors
    quality_factors = response_factors.get("quality", {})
    likelihood = _apply_quality_factors(pitch, likelihood, quality_factors)
    
    # Apply keyword triggers
    keyword_triggers = journalist_data.get("keyword_triggers", [])
    likelihood = _apply_keyword_boost(pitch, likelihood, keyword_triggers)
    
    # Cap at realistic maximum (85%)
    return min(likelihood, 0.85)


def _apply_timing_factors(pitch: str, likelihood: float, timing_factors: Dict[str, float]) -> float:
    """Apply timing-based multipliers to likelihood."""
    pitch_lower = pitch.lower()
    
    if "exclusive" in pitch_lower and "exclusive" in timing_factors:
        likelihood *= timing_factors["exclusive"]
    
    if "breaking" in pitch_lower and "breaking_news" in timing_factors:
        likelihood *= timing_factors["breaking_news"]
    
    if "embargo" in pitch_lower and "embargo" in timing_factors:
        likelihood *= timing_factors["embargo"]
    
    if "follow" in pitch_lower and "follow_up" in timing_factors:
        likelihood *= timing_factors["follow_up"]
    
    return likelihood


def _apply_relevance_factors(pitch: str, likelihood: float, relevance_factors: Dict[str, float]) -> float:
    """Apply relevance-based multipliers to likelihood."""
    pitch_lower = pitch.lower()
    
    # Check for beat-relevant terms (this is simplified - could be more sophisticated)
    beat_terms = [
        "enterprise", "software", "saas", "b2b", "security", "data", 
        "technology", "startup", "funding", "acquisition"
    ]
    
    # Use word boundaries to avoid partial matches like "tech" in "unrelated to tech"
    has_beat_match = any(re.search(r'\b' + re.escape(term) + r'\b', pitch_lower) for term in beat_terms)
    
    if has_beat_match and "exact_beat" in relevance_factors:
        likelihood *= relevance_factors["exact_beat"]
    elif not has_beat_match and "off_beat" in relevance_factors:
        likelihood *= relevance_factors["off_beat"]
    
    # Check for adjacent beat (partial match)
    adjacent_terms = ["business", "corporate", "digital", "innovation"]
    has_adjacent_match = any(term in pitch_lower for term in adjacent_terms)
    
    if has_adjacent_match and not has_beat_match and "adjacent_beat" in relevance_factors:
        likelihood *= relevance_factors["adjacent_beat"]
    
    return likelihood


def _apply_quality_factors(pitch: str, likelihood: float, quality_factors: Dict[str, float]) -> float:
    """Apply quality-based multipliers to likelihood."""
    pitch_lower = pitch.lower()
    
    # Data-driven indicators
    data_indicators = ["data", "study", "research", "survey", "report", "analysis", "statistics"]
    if any(indicator in pitch_lower for indicator in data_indicators) and "data_driven" in quality_factors:
        likelihood *= quality_factors["data_driven"]
    
    # Executive access indicators
    exec_indicators = ["ceo", "cto", "founder", "executive", "interview", "exclusive access"]
    if any(indicator in pitch_lower for indicator in exec_indicators) and "executive_access" in quality_factors:
        likelihood *= quality_factors["executive_access"]
    
    # Generic pitch penalties
    generic_indicators = ["product launch", "pleased to announce", "exciting news", "revolutionary"]
    if any(indicator in pitch_lower for indicator in generic_indicators) and "generic_pitch" in quality_factors:
        likelihood *= quality_factors["generic_pitch"]
    
    return likelihood


def _apply_keyword_boost(pitch: str, likelihood: float, keyword_triggers: list) -> float:
    """Apply keyword-based boosts to likelihood."""
    if not keyword_triggers:
        return likelihood
    
    pitch_lower = pitch.lower()
    
    # Count keyword matches
    keyword_matches = sum(1 for keyword in keyword_triggers if keyword.lower() in pitch_lower)
    
    # Apply boost based on keyword matches (diminishing returns)
    if keyword_matches > 0:
        # Each keyword adds a 20% boost with diminishing returns
        keyword_multiplier = 1 + (keyword_matches * 0.2) / (1 + keyword_matches * 0.1)
        likelihood *= keyword_multiplier
    
    return likelihood


def evaluate_pitch_with_ai(pitch: str, journalist_data: Dict[str, Any]) -> Tuple[str, float]:
    """
    Evaluate a pitch using Claude and return detailed feedback with cost tracking.
    
    Returns:
        Tuple of (feedback_text, estimated_cost)
    """
    model = get_model_for_task("evaluation")
    
    # Build evaluation prompt
    prompt = f"""You are an expert PR consultant evaluating a pitch to {journalist_data['name']} at {journalist_data['publication']}.

JOURNALIST PROFILE:
- Beat: {journalist_data['beat']}
- Base response rate: {journalist_data['base_response_rate']:.1%}
- Keywords: {', '.join(journalist_data.get('keyword_triggers', []))}
- Personality: {journalist_data.get('system_prompt', 'Professional journalist')}

PITCH TO EVALUATE:
{pitch}

Please provide a detailed evaluation covering:
1. **Relevance** - How well does this match the journalist's beat and interests?
2. **News Value** - What makes this newsworthy? Is there a compelling angle?
3. **Timing** - Are there any timing considerations (exclusivity, breaking news, etc.)?
4. **Presentation** - How is the pitch structured and written?
5. **Likelihood Assessment** - Based on this journalist's profile, how likely are they to respond?

Provide specific, actionable feedback that helps improve the pitch. Be direct but constructive."""

    try:
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        response = client.messages.create(
            model=model,
            max_tokens=1000,
            temperature=0.7,
            system="You are an expert PR consultant with deep knowledge of journalism and media relations.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        feedback = response.content[0].text
        
        # Estimate cost using token usage
        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        cost = estimate_cost(model, input_tokens, output_tokens)
        
        return feedback, cost
        
    except Exception as e:
        error_msg = f"Error generating AI feedback: {str(e)}"
        return error_msg, 0.0