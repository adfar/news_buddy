"""APScheduler-based job scheduler for news fetching and summarization."""

from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from collectors import OpenAICollector, AnthropicCollector, DeepMindCollector
from config import config
from database import Article, save_article
from summarizer import generate_daily_summary


def fetch_all_sources():
    """Fetch articles from all configured sources."""
    collectors = [
        OpenAICollector(),
        AnthropicCollector(),
        DeepMindCollector(),
    ]
    
    total_new = 0
    
    for collector in collectors:
        try:
            print(f"[{datetime.now()}] Fetching from {collector.source_name}...")
            articles = collector.fetch_articles()
            
            new_count = 0
            for collected in articles:
                article = Article(
                    id=None,
                    title=collected.title,
                    url=collected.url,
                    source=collected.source,
                    published_at=collected.published_at,
                    content_preview=collected.content_preview,
                    scraped_at=datetime.now()
                )
                if save_article(article):
                    new_count += 1
            
            print(f"  -> Found {len(articles)} articles, {new_count} new")
            total_new += new_count
            
        except Exception as e:
            print(f"  -> Error fetching from {collector.source_name}: {e}")
    
    print(f"[{datetime.now()}] Fetch complete. {total_new} new articles saved.")
    return total_new


def run_daily_summary():
    """Generate and save the daily summary."""
    print(f"[{datetime.now()}] Generating daily summary...")
    try:
        summary = generate_daily_summary()
        print(f"  -> Summary generated for {summary.date}")
    except Exception as e:
        print(f"  -> Error generating summary: {e}")


def create_scheduler() -> BackgroundScheduler:
    """Create and configure the scheduler."""
    scheduler = BackgroundScheduler()
    
    # Fetch job - runs every N hours
    scheduler.add_job(
        fetch_all_sources,
        trigger=IntervalTrigger(hours=config.fetch_interval_hours),
        id="fetch_articles",
        name="Fetch articles from all sources",
        replace_existing=True
    )
    
    # Summary job - runs daily at configured time
    scheduler.add_job(
        run_daily_summary,
        trigger=CronTrigger(
            hour=config.summary_time_hour,
            minute=config.summary_time_minute
        ),
        id="daily_summary",
        name="Generate daily summary",
        replace_existing=True
    )
    
    return scheduler


def start_scheduler() -> BackgroundScheduler:
    """Start the scheduler and return it."""
    scheduler = create_scheduler()
    scheduler.start()
    print(f"Scheduler started. Fetching every {config.fetch_interval_hours} hours.")
    print(f"Daily summary at {config.summary_time_hour:02d}:{config.summary_time_minute:02d}")
    return scheduler
