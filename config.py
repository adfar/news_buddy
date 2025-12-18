"""Configuration for the AI News Aggregator."""

import os
from dataclasses import dataclass, field


@dataclass
class SourceConfig:
    """Configuration for a news source."""
    name: str
    url: str
    source_type: str  # "rss" or "scrape"
    enabled: bool = True


@dataclass
class Config:
    """Main application configuration."""
    
    # Database
    database_path: str = "news_buddy.db"
    
    # Gemini API
    gemini_api_key: str = field(default_factory=lambda: os.environ.get("GEMINI_API_KEY", ""))
    gemini_model: str = "gemini-2.0-flash"
    
    # Scheduling
    fetch_interval_hours: int = 4
    summary_time_hour: int = 6  # 6 AM
    summary_time_minute: int = 0
    
    # Scraping
    articles_per_source: int = 20
    summary_lookback_hours: int = 24
    
    # Web server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Sources
    sources: list[SourceConfig] = field(default_factory=lambda: [
        SourceConfig(
            name="OpenAI",
            url="https://openai.com/blog/rss.xml",
            source_type="rss"
        ),
        SourceConfig(
            name="Anthropic", 
            url="https://www.anthropic.com/news",
            source_type="scrape"
        ),
        SourceConfig(
            name="DeepMind",
            url="https://deepmind.google/discover/blog/",
            source_type="scrape"
        ),
    ])


# Global config instance
config = Config()
