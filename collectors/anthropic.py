"""Web scraper for Anthropic news."""

import re
from datetime import datetime
from typing import Optional

import httpx
from selectolax.parser import HTMLParser

from collectors.base import BaseCollector, CollectedArticle


class AnthropicCollector(BaseCollector):
    """Collector for Anthropic news via web scraping."""
    
    source_name = "Anthropic"
    news_url = "https://www.anthropic.com/news"
    
    def fetch_articles(self) -> list[CollectedArticle]:
        """Fetch articles from Anthropic news page."""
        response = httpx.get(
            self.news_url,
            headers={"User-Agent": "NewsBuddy/1.0 (AI News Aggregator)"},
            follow_redirects=True,
            timeout=30
        )
        response.raise_for_status()
        
        parser = HTMLParser(response.text)
        articles = []
        
        # Find all article links - they have a specific pattern
        for link in parser.css("a[href^='/news/']"):
            href = link.attributes.get("href", "")
            
            # Skip the main news page link
            if href == "/news" or href == "/news/":
                continue
            
            # Build full URL
            url = f"https://www.anthropic.com{href}"
            
            # Get the text content for title
            title = link.text(strip=True)
            
            # Skip empty titles or navigation elements
            if not title or len(title) < 5:
                continue
            
            # Try to extract date from parent element or nearby text
            published_at = self._extract_date_from_context(link)
            
            # Avoid duplicates
            if any(a.url == url for a in articles):
                continue
            
            articles.append(CollectedArticle(
                title=title,
                url=url,
                source=self.source_name,
                published_at=published_at,
                content_preview=None
            ))
        
        return articles[:20]  # Limit to most recent
    
    def _extract_date_from_context(self, link_node) -> Optional[datetime]:
        """Try to extract date from surrounding context."""
        # Look for date patterns in parent elements
        parent = link_node.parent
        if parent:
            text = parent.text(strip=True)
            # Look for patterns like "Dec 9, 2025" or "Nov 24, 2025"
            date_match = re.search(
                r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+\d{4}",
                text
            )
            if date_match:
                try:
                    return datetime.strptime(date_match.group(), "%b %d, %Y")
                except ValueError:
                    try:
                        return datetime.strptime(date_match.group(), "%b %d %Y")
                    except ValueError:
                        pass
        return None
