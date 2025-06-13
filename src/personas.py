import json
import os
from pathlib import Path
from typing import Dict, List, Any


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