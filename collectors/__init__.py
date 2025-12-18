"""News collectors package."""

from collectors.base import BaseCollector, CollectedArticle
from collectors.rss import OpenAICollector
from collectors.anthropic import AnthropicCollector
from collectors.deepmind import DeepMindCollector

__all__ = [
    "BaseCollector",
    "CollectedArticle", 
    "OpenAICollector",
    "AnthropicCollector",
    "DeepMindCollector",
]
