import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
try:
    from openai import OpenAI  # v1.0+
    OPENAI_V1 = True
except ImportError:
    import openai  # v0.x
    OPENAI_V1 = False
from .config import get_model_for_task, estimate_cost


# Journalist type templates for generation
JOURNALIST_TEMPLATES = {
    "tech": {
        "base_response_rate": 0.15,
        "beat_keywords": ["technology", "software", "AI", "startup", "tech"],
        "response_factors": {
            "timing": {"exclusive": 2.5, "breaking_news": 3.0, "embargo": 1.8},
            "relevance": {"exact_beat": 2.0, "adjacent_beat": 1.3, "off_beat": 0.2},
            "quality": {"data_driven": 1.8, "executive_access": 2.2, "generic_pitch": 0.3}
        },
        "common_keywords": ["AI", "startup", "funding", "product launch", "innovation", "disruption"],
        "personality_traits": "curious about emerging technologies, values data and evidence, prefers concrete examples"
    },
    "business": {
        "base_response_rate": 0.12,
        "beat_keywords": ["business", "finance", "corporate", "market", "economy"],
        "response_factors": {
            "timing": {"exclusive": 2.0, "breaking_news": 2.5, "embargo": 2.0},
            "relevance": {"exact_beat": 1.8, "adjacent_beat": 1.2, "off_beat": 0.3},
            "quality": {"data_driven": 2.0, "executive_access": 2.5, "generic_pitch": 0.2}
        },
        "common_keywords": ["earnings", "IPO", "merger", "acquisition", "revenue", "market share"],
        "personality_traits": "focused on financial impact, skeptical of hype, values hard numbers and business metrics"
    },
    "investigative": {
        "base_response_rate": 0.08,
        "beat_keywords": ["investigation", "accountability", "transparency", "corruption"],
        "response_factors": {
            "timing": {"exclusive": 3.0, "breaking_news": 2.0, "embargo": 2.5},
            "relevance": {"exact_beat": 2.5, "adjacent_beat": 1.0, "off_beat": 0.1},
            "quality": {"data_driven": 3.0, "executive_access": 1.8, "generic_pitch": 0.1}
        },
        "common_keywords": ["documents", "whistleblower", "investigation", "misconduct", "transparency"],
        "personality_traits": "highly skeptical, requires extensive documentation, patient with long-term stories"
    },
    "health": {
        "base_response_rate": 0.14,
        "beat_keywords": ["health", "medical", "healthcare", "pharma", "biotech"],
        "response_factors": {
            "timing": {"exclusive": 2.2, "breaking_news": 2.8, "embargo": 1.9},
            "relevance": {"exact_beat": 2.1, "adjacent_beat": 1.1, "off_beat": 0.2},
            "quality": {"data_driven": 2.5, "executive_access": 1.9, "generic_pitch": 0.2}
        },
        "common_keywords": ["clinical trial", "FDA", "drug approval", "medical device", "patient safety"],
        "personality_traits": "evidence-based, concerned with public health impact, careful about medical claims"
    }
}


def load_journalist(journalist_id: str) -> Dict[str, Any]:
    """Load a journalist persona from JSON file."""
    file_path = Path(f"journalists/{journalist_id}.json")
    
    if not file_path.exists():
        raise FileNotFoundError(f"Journalist file not found: {file_path}")
    
    with open(file_path, 'r') as f:
        return json.load(f)


def save_journalist(journalist_id: str, journalist_data: Dict[str, Any]) -> None:
    """Save a journalist persona to JSON file."""
    file_path = Path(f"journalists/{journalist_id}.json")
    
    # Ensure the journalists directory exists
    file_path.parent.mkdir(exist_ok=True)
    
    with open(file_path, 'w') as f:
        json.dump(journalist_data, f, indent=2)


def list_journalists() -> List[str]:
    """List all available journalist IDs."""
    journalists_dir = Path("journalists")
    
    if not journalists_dir.exists():
        return []
    
    journalist_files = []
    for file_path in journalists_dir.glob("*.json"):
        # Remove .json extension to get journalist ID
        journalist_id = file_path.stem
        journalist_files.append(journalist_id)
    
    return sorted(journalist_files)


def generate_journalist_persona(
    journalist_type: Optional[str] = None,
    named_journalist: Optional[str] = None,
    publication: Optional[str] = None,
    return_cost: bool = False
) -> Dict[str, Any] | Tuple[Dict[str, Any], float]:
    """
    Generate a new journalist persona using AI.
    
    Args:
        journalist_type: Type from JOURNALIST_TEMPLATES (tech, business, investigative, health)
        named_journalist: Specific journalist name (e.g., "Kara Swisher")
        publication: Publication name
        return_cost: Whether to return cost information
        
    Returns:
        Generated journalist dict, optionally with cost
    """
    model = get_model_for_task("generation")  # Use o3 for quality
    
    # Determine template to use
    if journalist_type and journalist_type in JOURNALIST_TEMPLATES:
        template = JOURNALIST_TEMPLATES[journalist_type]
    else:
        # Default to tech template
        template = JOURNALIST_TEMPLATES["tech"]
        journalist_type = "tech"
    
    # Build generation prompt
    if named_journalist:
        prompt = f"""Generate a realistic journalist persona for {named_journalist}. 

REQUIREMENTS:
- Publication: {publication or "appropriate for their expertise"}
- Create a detailed, professional persona based on their known work and style
- Include specific personality traits and communication patterns
- Base the response factors on their actual beat and preferences
"""
    else:
        prompt = f"""Generate a realistic journalist persona for a {journalist_type} journalist.

TEMPLATE GUIDELINES:
- Journalist type: {journalist_type}
- Publication: {publication or "major publication in this field"}
- Base response rate around: {template['base_response_rate']}
- Beat should focus on: {', '.join(template['beat_keywords'])}
- Personality: {template['personality_traits']}
"""

    prompt += f"""
Return a JSON object with these exact fields:

{{
  "name": "Full Name",
  "publication": "{publication or 'Publication Name'}",
  "beat": "Specific beat/specialty area",
  "base_response_rate": {template['base_response_rate']},
  "response_factors": {{
    "timing": {{
      "breaking_news": 2.5,
      "exclusive": 2.0,
      "embargo": 1.5,
      "follow_up": 0.8
    }},
    "relevance": {{
      "exact_beat": 2.0,
      "adjacent_beat": 1.2,
      "off_beat": 0.3
    }},
    "quality": {{
      "data_driven": 1.8,
      "executive_access": 2.0,
      "generic_pitch": 0.3
    }}
  }},
  "keyword_triggers": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
  "system_prompt": "Detailed persona description for AI conversations - include background, expertise, communication style, preferences, and specific behavioral patterns."
}}

IMPORTANT:
- Make the name realistic and professional
- Tailor response_factors to the journalist type
- Include 5-8 relevant keyword_triggers
- Write a detailed system_prompt (200+ words) that captures their personality
- All values must be realistic and balanced
"""

    try:
        if OPENAI_V1:
            # OpenAI v1.0+ API
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are an expert in journalism and media relations. Generate realistic, professional journalist personas."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.8
            )
            content = response.choices[0].message.content
            output_tokens = response.usage.completion_tokens if response.usage else len(content.split()) * 1.3
        else:
            # OpenAI v0.x API
            openai.api_key = os.getenv("OPENAI_API_KEY")
            response = openai.ChatCompletion.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are an expert in journalism and media relations. Generate realistic, professional journalist personas."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.8
            )
            content = response.choices[0].message.content
            output_tokens = response.usage.completion_tokens if hasattr(response, 'usage') else len(content.split()) * 1.3
        
        # Parse JSON response
        journalist_data = json.loads(content.strip())
        
        # Validate required fields
        required_fields = ["name", "publication", "beat", "base_response_rate", "response_factors", "keyword_triggers", "system_prompt"]
        for field in required_fields:
            if field not in journalist_data:
                raise ValueError(f"Generated journalist missing required field: {field}")
        
        # Calculate cost
        input_tokens = len(prompt.split()) * 1.3
        cost = estimate_cost(model, int(input_tokens), int(output_tokens))
        
        if return_cost:
            return journalist_data, cost
        return journalist_data
        
    except json.JSONDecodeError as e:
        error_msg = f"Failed to parse generated journalist JSON: {str(e)}"
        raise ValueError(error_msg)
    except Exception as e:
        error_msg = f"Error generating journalist: {str(e)}"
        raise RuntimeError(error_msg)