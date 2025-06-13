import pytest
from src.evaluation import calculate_response_likelihood
from src.personas import load_journalist


def test_calculate_response_likelihood_with_multipliers():
    journalist_data = {
        "base_response_rate": 0.1,
        "response_factors": {
            "timing": {"exclusive": 2.0, "breaking_news": 3.0},
            "relevance": {"exact_beat": 2.0, "off_beat": 0.2},
            "quality": {"data_driven": 1.5, "generic_pitch": 0.3}
        },
        "keyword_triggers": ["security", "data breach"]
    }
    
    # Test basic calculation
    pitch = "Here's some breaking news about a security issue"
    likelihood = calculate_response_likelihood(pitch, journalist_data)
    
    # Should apply breaking_news (3.0) and keyword trigger
    # Base: 0.1 * 3.0 = 0.3, plus keyword bonus
    assert likelihood > 0.3
    assert likelihood < 1.0


def test_likelihood_caps_at_85_percent():
    journalist_data = {
        "base_response_rate": 0.5,
        "response_factors": {
            "timing": {"exclusive": 10.0},  # Intentionally high multiplier
            "relevance": {"exact_beat": 10.0}
        },
        "keyword_triggers": ["test"]
    }
    
    pitch = "Exclusive test story with perfect beat match"
    likelihood = calculate_response_likelihood(pitch, journalist_data)
    
    # Should cap at 0.85 regardless of high multipliers
    assert likelihood <= 0.85


def test_handles_missing_factors_gracefully():
    # Minimal journalist data with missing factors
    journalist_data = {
        "base_response_rate": 0.2,
        "response_factors": {},
        "keyword_triggers": []
    }
    
    pitch = "Regular pitch with no special factors"
    likelihood = calculate_response_likelihood(pitch, journalist_data)
    
    # Should return base rate when no factors apply
    assert likelihood == 0.2


def test_keyword_triggers_boost_likelihood():
    journalist_data = {
        "base_response_rate": 0.1,
        "response_factors": {
            "timing": {},
            "relevance": {}
        },
        "keyword_triggers": ["data breach", "cybersecurity"]
    }
    
    # Pitch without keywords
    basic_pitch = "We have a new product launch"
    basic_likelihood = calculate_response_likelihood(basic_pitch, journalist_data)
    
    # Pitch with keywords
    keyword_pitch = "Major data breach affects cybersecurity landscape"
    keyword_likelihood = calculate_response_likelihood(keyword_pitch, journalist_data)
    
    assert keyword_likelihood > basic_likelihood


def test_multiple_factors_compound():
    journalist_data = {
        "base_response_rate": 0.1,
        "response_factors": {
            "timing": {"exclusive": 2.0, "breaking_news": 1.5},
            "relevance": {"exact_beat": 1.8},
            "quality": {"data_driven": 1.3}
        },
        "keyword_triggers": ["enterprise"]
    }
    
    # Pitch hitting multiple factors
    pitch = "Exclusive breaking news: Enterprise data shows unprecedented growth"
    likelihood = calculate_response_likelihood(pitch, journalist_data)
    
    # Should compound multiple multipliers
    # Base (0.1) * exclusive (2.0) * breaking_news (1.5) * exact_beat (1.8) * data_driven (1.3) + keyword
    expected_min = 0.1 * 2.0 * 1.5 * 1.8 * 1.3  # = 0.702
    assert likelihood >= expected_min * 0.8  # Allow some variance for keyword logic


def test_off_beat_reduces_likelihood():
    journalist_data = {
        "base_response_rate": 0.2,
        "response_factors": {
            "relevance": {"off_beat": 0.3}
        },
        "keyword_triggers": []
    }
    
    pitch = "Sports news story completely unrelated to tech"
    likelihood = calculate_response_likelihood(pitch, journalist_data)
    
    # Should be reduced by off_beat factor
    expected = 0.2 * 0.3  # = 0.06
    assert likelihood == expected


def test_real_journalist_integration():
    """Test with actual Jane Smith journalist data"""
    journalist = load_journalist("jane_smith_techcrunch")
    
    # Enterprise software pitch (on beat)
    enterprise_pitch = "Exclusive: Major enterprise security breach affects 50,000+ businesses"
    likelihood = calculate_response_likelihood(enterprise_pitch, journalist)
    
    # Should be moderately high due to beat match, exclusive, and keywords
    assert likelihood > 0.3
    assert likelihood <= 0.85
    
    # Off-beat pitch
    sports_pitch = "New sports app launches with basic features"
    off_beat_likelihood = calculate_response_likelihood(sports_pitch, journalist)
    
    # Should be much lower
    assert off_beat_likelihood < likelihood
    assert off_beat_likelihood < 0.1