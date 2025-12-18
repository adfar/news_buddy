"""Web scraper for DeepMind blog."""

import re

import httpx
from selectolax.parser import HTMLParser

from collectors.base import BaseCollector, CollectedArticle


class DeepMindCollector(BaseCollector):
    """Collector for DeepMind blog via web scraping."""
    
    source_name = "DeepMind"
    blog_url = "https://deepmind.google/discover/blog/"
    
    def fetch_articles(self) -> list[CollectedArticle]:
        """Fetch articles from DeepMind blog."""
        response = httpx.get(
            self.blog_url,
            headers={"User-Agent": "NewsBuddy/1.0 (AI News Aggregator)"},
            follow_redirects=True,
            timeout=30
        )
        response.raise_for_status()
        
        parser = HTMLParser(response.text)
        articles = []
        seen_urls = set()
        
        # DeepMind uses various link patterns for blog posts
        for link in parser.css("a"):
            href = link.attributes.get("href", "")
            
            # Match DeepMind blog URLs and external blog.google URLs
            is_deepmind_blog = "/blog/" in href and "deepmind.google" in href
            is_google_blog = "blog.google" in href
            
            if not (is_deepmind_blog or is_google_blog):
                continue
            
            # Skip the main blog listing page
            if href.rstrip("/") == "https://deepmind.google/discover/blog":
                continue
            if href.rstrip("/") == "/discover/blog":
                continue
            
            # Normalize URL
            if href.startswith("/"):
                url = f"https://deepmind.google{href}"
            else:
                url = href
            
            # Remove tracking parameters for deduplication
            base_url = url.split("?")[0]
            
            if base_url in seen_urls:
                continue
            seen_urls.add(base_url)
            
            # Get title - try multiple strategies
            title = self._extract_title(link, base_url)
            
            if not title or len(title) < 5:
                continue
            
            articles.append(CollectedArticle(
                title=title,
                url=base_url,
                source=self.source_name,
                published_at=None,
                content_preview=None
            ))
        
        return articles[:20]
    
    def _extract_title(self, link_node, url: str) -> str:
        """Extract article title using multiple strategies."""
        # Strategy 1: Try aria-label attribute
        aria_label = link_node.attributes.get("aria-label", "")
        if aria_label and self._is_valid_title(aria_label):
            return aria_label
        
        # Strategy 2: Look for a heading inside or near the link
        heading = link_node.css_first("h1, h2, h3, h4")
        if heading:
            text = heading.text(strip=True)
            if self._is_valid_title(text):
                return text
        
        # Strategy 3: Get link text and clean it
        link_text = link_node.text(strip=True)
        # Remove common navigation artifacts
        link_text = re.sub(r'keyboard_arrow_right\s*', '', link_text, flags=re.IGNORECASE)
        link_text = re.sub(r'\s*Learn more\s*$', '', link_text, flags=re.IGNORECASE)
        link_text = re.sub(r'\s*Read more\s*$', '', link_text, flags=re.IGNORECASE)
        link_text = link_text.strip()
        
        if self._is_valid_title(link_text):
            return link_text
        
        # Strategy 4: Extract from URL slug as last resort
        return self._title_from_url(url)
    
    def _is_valid_title(self, text: str) -> bool:
        """Check if text is a valid article title."""
        if not text or len(text) < 5:
            return False
        invalid = ["learn more", "read more", "keyboard_arrow_right", "see more", "view all"]
        return text.lower().strip() not in invalid
    
    def _title_from_url(self, url: str) -> str:
        """Extract a title from the URL slug."""
        # Get the last path segment
        path = url.rstrip("/").split("/")[-1]
        # Remove common prefixes
        path = re.sub(r'^(blog-|post-|article-)', '', path)
        # Replace hyphens with spaces and title case
        title = path.replace("-", " ").replace("_", " ")
        return title.title()

