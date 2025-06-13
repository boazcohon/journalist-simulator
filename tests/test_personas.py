import pytest
import json
import os
from pathlib import Path
from src.personas import load_journalist, save_journalist, list_journalists, generate_journalist_persona


def test_load_journalist_from_json():
    journalist = load_journalist("jane_smith_techcrunch")
    
    assert journalist is not None
    assert isinstance(journalist, dict)


def test_journalist_has_required_fields():
    journalist = load_journalist("jane_smith_techcrunch")
    
    # Core identity fields
    assert "name" in journalist
    assert "publication" in journalist
    assert "beat" in journalist
    
    # Response behavior fields
    assert "base_response_rate" in journalist
    assert "response_factors" in journalist
    assert "keyword_triggers" in journalist
    assert "system_prompt" in journalist
    
    # Validate types
    assert isinstance(journalist["base_response_rate"], (int, float))
    assert isinstance(journalist["response_factors"], dict)
    assert isinstance(journalist["keyword_triggers"], list)
    assert isinstance(journalist["system_prompt"], str)


def test_journalist_response_factors_structure():
    journalist = load_journalist("jane_smith_techcrunch")
    factors = journalist["response_factors"]
    
    # Should have timing and relevance factors
    assert "timing" in factors
    assert "relevance" in factors
    
    # Timing factors should include key multipliers
    timing = factors["timing"]
    assert "breaking_news" in timing
    assert "exclusive" in timing
    
    # Relevance factors should include beat matching
    relevance = factors["relevance"]
    assert "exact_beat" in relevance
    assert "off_beat" in relevance


def test_load_nonexistent_journalist():
    with pytest.raises(FileNotFoundError):
        load_journalist("nonexistent_journalist")


def test_save_journalist():
    test_journalist = {
        "name": "Test Reporter",
        "publication": "Test Daily",
        "beat": "Testing",
        "base_response_rate": 0.2,
        "response_factors": {
            "timing": {"breaking_news": 2.0},
            "relevance": {"exact_beat": 1.5}
        },
        "keyword_triggers": ["test", "qa"],
        "system_prompt": "You are a test journalist."
    }
    
    # Save the journalist
    save_journalist("test_reporter", test_journalist)
    
    # Verify it was saved correctly
    loaded = load_journalist("test_reporter")
    assert loaded["name"] == "Test Reporter"
    assert loaded["publication"] == "Test Daily"
    
    # Clean up
    os.remove("journalists/test_reporter.json")


def test_list_journalists():
    journalists = list_journalists()
    
    assert isinstance(journalists, list)
    assert len(journalists) > 0
    assert "jane_smith_techcrunch" in journalists


def test_generate_journalist_persona_tech():
    """Test generating a tech journalist persona."""
    journalist = generate_journalist_persona(
        journalist_type="tech",
        publication="The Verge"
    )
    
    assert journalist is not None
    assert isinstance(journalist, dict)
    
    # Check required fields exist
    assert "name" in journalist
    assert "publication" in journalist
    assert "beat" in journalist
    assert "base_response_rate" in journalist
    assert "response_factors" in journalist
    assert "keyword_triggers" in journalist
    assert "system_prompt" in journalist
    
    # Verify publication matches
    assert journalist["publication"] == "The Verge"
    
    # Verify tech journalist characteristics (more flexible matching)
    beat_lower = journalist["beat"].lower()
    tech_terms = ["tech", "technology", "ai", "software", "startup", "digital"]
    assert any(term in beat_lower for term in tech_terms), f"Beat '{journalist['beat']}' should contain tech-related terms"
    assert len(journalist["keyword_triggers"]) >= 3
    assert len(journalist["system_prompt"]) > 100  # Should be detailed


def test_generate_journalist_persona_business():
    """Test generating a business journalist persona.""" 
    journalist = generate_journalist_persona(
        journalist_type="business",
        publication="Wall Street Journal"
    )
    
    assert journalist is not None
    assert journalist["publication"] == "Wall Street Journal"
    
    # Business journalists should have different characteristics
    business_keywords = ["business", "finance", "corporate", "market", "economy"]
    beat_lower = journalist["beat"].lower()
    assert any(keyword in beat_lower for keyword in business_keywords)


def test_generate_journalist_persona_investigative():
    """Test generating an investigative journalist persona."""
    journalist = generate_journalist_persona(
        journalist_type="investigative",
        publication="ProPublica"
    )
    
    assert journalist is not None
    assert journalist["publication"] == "ProPublica"
    
    # Investigative journalists should have lower base response rates
    assert journalist["base_response_rate"] <= 0.15
    
    # Should have specific response factors for quality
    factors = journalist["response_factors"]
    assert "quality" in factors
    assert "data_driven" in factors.get("quality", {})


def test_generate_named_journalist():
    """Test generating a specific named journalist."""
    journalist = generate_journalist_persona(
        named_journalist="Kara Swisher",
        publication="Recode"
    )
    
    assert journalist is not None
    assert "Kara Swisher" in journalist["name"]
    assert journalist["publication"] == "Recode"
    
    # Named journalists should have more specific system prompts
    assert "Kara Swisher" in journalist["system_prompt"]


def test_generate_journalist_default_values():
    """Test that generated journalists have sensible default values."""
    journalist = generate_journalist_persona(
        journalist_type="tech"
    )
    
    # Should have reasonable base response rate
    assert 0.05 <= journalist["base_response_rate"] <= 0.3
    
    # Should have standard response factor categories
    factors = journalist["response_factors"]
    assert "timing" in factors
    assert "relevance" in factors
    
    # Timing factors should include common multipliers
    timing = factors["timing"]
    assert "exclusive" in timing
    assert timing["exclusive"] >= 1.5  # Should boost likelihood


def test_generate_journalist_cost_tracking():
    """Test that generation tracks costs properly."""
    journalist, cost = generate_journalist_persona(
        journalist_type="tech",
        return_cost=True
    )
    
    assert journalist is not None
    assert isinstance(cost, float)
    assert cost >= 0  # Should be non-negative