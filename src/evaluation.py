import re
from typing import Dict, Any


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