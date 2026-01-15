from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Video:
    id: str
    title: str
    published_at: str

@dataclass
class Rule:
    keyword: str
    description: str
