"""Configuration for AI models and costs."""

# Model configuration based on use case
MODEL_CONFIG = {
    "evaluation": "claude-3-haiku-20240307",  # Fast and cheap for evaluations
    "generation": "claude-3-5-sonnet-20241022",  # High quality for persona generation
    "conversation": "claude-3-haiku-20240307"     # Cost-effective for chat
}

# Approximate cost per 1K tokens (Anthropic pricing)
MODEL_COSTS = {
    "claude-3-haiku-20240307": {
        "input": 0.00025,    # $0.25 per 1M input tokens
        "output": 0.00125    # $1.25 per 1M output tokens
    },
    "claude-3-5-sonnet-20241022": {
        "input": 0.003,      # $3 per 1M input tokens
        "output": 0.015      # $15 per 1M output tokens
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
