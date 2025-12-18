"""Gemini-powered summarizer for daily news digests."""

from datetime import datetime, timedelta

import google.generativeai as genai

from config import config
from database import Article, Summary, get_articles, save_summary


def generate_daily_summary() -> Summary:
    """Generate a summary of recent articles using Gemini."""
    # Get articles from the last N hours
    since = datetime.now() - timedelta(hours=config.summary_lookback_hours)
    articles = get_articles(since=since, limit=50)
    
    if not articles:
        content = "No new articles were published in the last 24 hours."
    else:
        content = _generate_summary_with_gemini(articles)
    
    summary = Summary(
        id=None,
        date=datetime.now().strftime("%Y-%m-%d"),
        content=content,
        created_at=datetime.now()
    )
    
    save_summary(summary)
    return summary


def _generate_summary_with_gemini(articles: list[Article]) -> str:
    """Use Gemini to generate a cohesive summary."""
    if not config.gemini_api_key:
        return _fallback_summary(articles)
    
    genai.configure(api_key=config.gemini_api_key)
    model = genai.GenerativeModel(config.gemini_model)
    
    # Build the article context
    article_texts = []
    for i, article in enumerate(articles, 1):
        preview = article.content_preview or "(No preview available)"
        article_texts.append(
            f"{i}. [{article.source}] {article.title}\n"
            f"   URL: {article.url}\n"
            f"   Preview: {preview[:300]}..."
        )
    
    prompt = f"""You are an AI news analyst. Summarize the following news articles from major AI companies (OpenAI, Anthropic, DeepMind) into a cohesive daily digest.

The summary should:
1. Group related news by theme or company
2. Highlight the most significant developments
3. Be written in a professional but accessible tone
4. Include relevant links to the original articles
5. Be around 400-600 words

Here are today's articles:

{chr(10).join(article_texts)}

Write the daily AI news summary in markdown format:"""

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Gemini API error: {e}")
        return _fallback_summary(articles)


def _fallback_summary(articles: list[Article]) -> str:
    """Generate a simple summary without LLM when API is unavailable."""
    lines = ["# Daily AI News Digest\n"]
    
    # Group by source
    by_source = {}
    for article in articles:
        by_source.setdefault(article.source, []).append(article)
    
    for source, source_articles in sorted(by_source.items()):
        lines.append(f"\n## {source}\n")
        for article in source_articles[:5]:
            lines.append(f"- [{article.title}]({article.url})")
    
    lines.append(f"\n\n*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}*")
    return "\n".join(lines)
