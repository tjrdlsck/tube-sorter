import json
import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def load_json(file_path: str) -> Optional[Dict[str, Any]]:
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from {file_path}: {e}")
            return None
    return None

def save_state(file_path: str, last_published_at: str):
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump({'last_published_at': last_published_at}, f)
    except Exception as e:
        logger.error(f"Failed to save state: {e}")

def validate_rules(rules_data: Any) -> bool:
    if not rules_data or 'rules' not in rules_data:
        raise ValueError("Invalid rules format: 'rules' key is missing.")
    for i, rule in enumerate(rules_data['rules']):
        if 'keyword' not in rule:
            raise ValueError(f"Rule at index {i} is missing 'keyword'.")
    return True
