"""Configuration for AI models and costs."""

# Model configuration based on use case
MODEL_CONFIG = {
    "evaluation": "o3-mini-2025-01-31",  # Cheap, good enough for evaluations
    "generation": "o3-2025-04-16",       # Quality matters for persona generation
    "conversation": "o3-mini-2025-01-31" # Cost-effective for chat
}

# Approximate cost per 1K tokens (update as needed)
MODEL_COSTS = {
    "o3-mini-2025-01-31": {
        "input": 0.000125,   # $0.000125 per 1K input tokens
        "output": 0.0005     # $0.0005 per 1K output tokens  
    },
    "o3-2025-04-16": {
        "input": 0.015,      # $0.015 per 1K input tokens
        "output": 0.06       # $0.06 per 1K output tokens
    }
}

def get_model_for_task(task: str) -> str:
    """Get the appropriate model for a given task."""
    return MODEL_CONFIG.get(task, MODEL_CONFIG["evaluation"])

def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Estimate cost for a model call."""
    if model not in MODEL_COSTS:
        return 0.0
    
    costs = MODEL_COSTS[model]
    input_cost = (input_tokens / 1000) * costs["input"]
    output_cost = (output_tokens / 1000) * costs["output"]
    
    return input_cost + output_cost