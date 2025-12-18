"""Base collector interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class CollectedArticle:
    """Article data collected from a source."""
    title: str
    url: str
    source: str
    published_at: Optional[datetime]
    content_preview: Optional[str] = None


class BaseCollector(ABC):
    """Abstract base class for news collectors."""
    
    source_name: str
    
    @abstractmethod
    def fetch_articles(self) -> list[CollectedArticle]:
        """Fetch articles from the source."""
        pass
