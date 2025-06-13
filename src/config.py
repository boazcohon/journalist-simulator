"""
Configuration for PR Training Bot
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("Please set OPENAI_API_KEY in your .env file")

# Model Configuration
MODEL_CONFIG = {
    "persona_generation": "o3-2025-04-16",      # High quality for one-time generation
    "evaluation": "o3-mini-2025-01-31",         # Cost-effective for repeated use
    "conversation": "o3-mini-2025-01-31"        # Cost-effective for chat
}

# Cost Tracking (approximate per 1K tokens)
COST_PER_1K_TOKENS = {
    "o3-2025-04-16": {"input": 0.002, "output": 0.008},
    "o3-mini-2025-01-31": {"input": 0.0003, "output": 0.0012}
}
