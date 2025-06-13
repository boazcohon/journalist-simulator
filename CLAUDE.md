# PR Training Bot - Claude Code Development Guide

This bot helps PR professionals practice pitching to AI journalists with realistic personas stored as JSON files.

## 🎯 Project Overview

A Streamlit app where users:
1. Select or create journalist personas (stored as JSON)
2. Practice pitching in two modes:
   - Pitch Evaluator: Get feedback on pitch quality
   - Conversation Mode: Real-time chat with journalist

## 📁 Project Structure

```
pr-training-bot/
├── app.py                    # Main Streamlit interface
├── journalists/              # JSON persona storage
│   ├── .gitkeep             # Keep directory in git
│   └── *.json               # Individual journalist files
├── src/
│   ├── personas.py          # Persona generation & management
│   ├── evaluator.py         # Pitch evaluation logic
│   └── utils.py             # Helper functions
├── tests/                   # Test files
├── .env.example             # OPENAI_API_KEY=your-key-here
├── requirements.txt         # streamlit, openai>=1.0
└── README.md
```

## 🚀 Quick Commands

```bash
# Run the app
streamlit run app.py

# Run tests
pytest tests/

# Format code
black .

# Type checking
mypy src/
```

## 💡 Key Development Patterns

### 1. Working with Journalist Personas

**Creating New Personas**:
```python
# Use o3 for initial generation (quality matters)
# Then switch to o3-mini for interactions (cost-effective)
model = "o3-2025-04-16" if creating else "o3-mini-2025-01-31"
```

**JSON Structure**:
```json
{
  "name": "Jane Smith",
  "publication": "TechCrunch",
  "beat": "Enterprise Software",
  "base_response_rate": 0.15,
  "response_factors": {
    "timing": {"breaking_news": 3.0, "exclusive": 2.5},
    "relevance": {"exact_beat": 2.0, "off_beat": 0.2}
  },
  "keyword_triggers": ["data breach", "security"],
  "system_prompt": "You are Jane Smith..."
}
```

### 2. Response Likelihood Calculation

Use multipliers, not fixed percentages:
```python
def calculate_response_likelihood(pitch, journalist_data):
    likelihood = journalist_data["base_response_rate"]
    
    # Apply multipliers based on pitch
    if "exclusive" in pitch.lower():
        likelihood *= journalist_data["response_factors"]["timing"]["exclusive"]
    
    # Cap at realistic maximum
    return min(likelihood, 0.85)
```

### 3. Cost Optimization

```python
# Decision tree for model selection
def choose_model(task):
    if task == "generate_new_persona":
        return "o3-2025-04-16"  # Quality matters
    elif task == "evaluate_pitch":
        return "o3-mini-2025-01-31"  # 85% quality, 15% cost
    else:
        return "o3-mini-2025-01-31"  # Default to mini
```

## 🏗️ Building Features

### Adding a New Journalist Type

1. Create response factor template:
```python
# In src/personas.py
JOURNALIST_TEMPLATES = {
    "investigative": {
        "base_response_rate": 0.05,
        "response_factors": {...}
    }
}
```

2. Test the persona:
```python
# In tests/test_personas.py
def test_investigative_journalist():
    persona = generate_journalist_persona(type="investigative")
    assert persona["base_response_rate"] < 0.1
```

### Implementing Profile Updates

Never fabricate personal details. Only track observations:
```python
def update_journalist_profile(journalist_file, observation):
    journalist = load_journalist(journalist_file)
    
    # Only professional observations
    if "observations" not in journalist:
        journalist["observations"] = {}
    
    journalist["observations"][observation["type"]].append({
        "date": datetime.now().isoformat(),
        "note": observation["note"],
        "confidence": observation["confidence"]
    })
```

## 🐛 Common Issues & Solutions

### Issue: Inconsistent Journalist Responses
**Fix**: Store system prompts in JSON, don't regenerate
```python
# RIGHT: Use stored prompt
prompt = journalist_data["system_prompt"]
```

### Issue: High API Costs
**Fix**: Cache common operations
- Store journalist system prompts
- Use session state for conversation history
- Batch similar evaluations

### Issue: Journalist Feels Generic
**Fix**: Use specific, measurable traits
- ❌ "Likes tech stories"
- ✅ "Covers data breaches over $10M affecting 50K+ users"

## 🧪 Testing Checklist

Before committing:
- [ ] Journalist maintains voice across 10+ interactions
- [ ] Response likelihood calculation works correctly
- [ ] Cost tracking is accurate
- [ ] Profile updates persist correctly
- [ ] No personal information in personas

## 📝 Code Style

- Use descriptive variable names
- Keep functions under 50 lines
- Type hints for all functions
- Docstrings for public methods
- No hardcoded API keys

## 🔒 Security & Privacy

1. **Never include**:
   - Real journalist personal details
   - Private contact information
   - Unverified claims about real people

2. **Always include**:
   - Only publicly available information
   - Professional patterns and preferences
   - Observable behavior from published work

## 🎯 MVP Checklist

Phase 1 (Core Features):
- [ ] Create/load journalist personas
- [ ] Basic pitch evaluation
- [ ] Store personas as JSON
- [ ] Simple cost tracking

Phase 2 (Enhanced):
- [ ] Conversation mode
- [ ] Response likelihood display
- [ ] Profile update system
- [ ] Multiple journalist scenarios

Phase 3 (Advanced):
- [ ] Team collaboration features
- [ ] Analytics dashboard
- [ ] Export conversation history
- [ ] A/B testing pitches

## 💭 Remember

- Start with 2-3 journalists, not 20
- Test with real PR professionals early
- Response patterns > fictional backstories
- Let users build profiles through actual use
- The goal is education, not deception
