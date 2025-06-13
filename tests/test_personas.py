import pytest
import json
import os
from pathlib import Path
from src.personas import load_journalist, save_journalist, list_journalists


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