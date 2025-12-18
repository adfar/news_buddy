"""RSS feed collector for OpenAI."""

from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Optional

import feedparser

from collectors.base import BaseCollector, CollectedArticle


class OpenAICollector(BaseCollector):
    """Collector for OpenAI blog via RSS feed."""
    
    source_name = "OpenAI"
    feed_url = "https://openai.com/blog/rss.xml"
    
    def fetch_articles(self) -> list[CollectedArticle]:
        """Fetch articles from OpenAI RSS feed."""
        feed = feedparser.parse(self.feed_url)
        articles = []
        
        for entry in feed.entries:
            published_at = self._parse_date(entry.get("published"))
            
            articles.append(CollectedArticle(
                title=entry.get("title", "Untitled"),
                url=entry.get("link", ""),
                source=self.source_name,
                published_at=published_at,
                content_preview=entry.get("description", "")[:500] if entry.get("description") else None
            ))
        
        return articles
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse RSS date format."""
        if not date_str:
            return None
        try:
            return parsedate_to_datetime(date_str)
        except (ValueError, TypeError):
            return None
