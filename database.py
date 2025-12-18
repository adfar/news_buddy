"""SQLite database layer for the AI News Aggregator."""

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from config import config


@dataclass
class Article:
    """Represents a news article."""
    id: Optional[int]
    title: str
    url: str
    source: str
    published_at: Optional[datetime]
    content_preview: Optional[str]
    scraped_at: datetime
    
    @classmethod
    def from_row(cls, row: tuple) -> "Article":
        return cls(
            id=row[0],
            title=row[1],
            url=row[2],
            source=row[3],
            published_at=datetime.fromisoformat(row[4]) if row[4] else None,
            content_preview=row[5],
            scraped_at=datetime.fromisoformat(row[6])
        )


@dataclass
class Summary:
    """Represents a daily summary."""
    id: Optional[int]
    date: str  # YYYY-MM-DD
    content: str
    created_at: datetime
    
    @classmethod
    def from_row(cls, row: tuple) -> "Summary":
        return cls(
            id=row[0],
            date=row[1],
            content=row[2],
            created_at=datetime.fromisoformat(row[3])
        )


SCHEMA = """
CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    url TEXT NOT NULL,
    source_type TEXT NOT NULL,
    last_checked TIMESTAMP,
    enabled INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    url TEXT UNIQUE NOT NULL,
    source TEXT NOT NULL,
    published_at TIMESTAMP,
    content_preview TEXT,
    scraped_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT UNIQUE NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_articles_source ON articles(source);
CREATE INDEX IF NOT EXISTS idx_articles_published ON articles(published_at);
CREATE INDEX IF NOT EXISTS idx_articles_scraped ON articles(scraped_at);
CREATE INDEX IF NOT EXISTS idx_summaries_date ON summaries(date);
"""


@contextmanager
def get_db():
    """Context manager for database connections."""
    conn = sqlite3.connect(config.database_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """Initialize the database schema."""
    with get_db() as conn:
        conn.executescript(SCHEMA)
        conn.commit()
    print(f"Database initialized: {config.database_path}")


def save_article(article: Article) -> Optional[int]:
    """Save an article to the database, returning its ID. Returns None if duplicate."""
    with get_db() as conn:
        try:
            cursor = conn.execute(
                """
                INSERT INTO articles (title, url, source, published_at, content_preview, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    article.title,
                    article.url,
                    article.source,
                    article.published_at.isoformat() if article.published_at else None,
                    article.content_preview,
                    article.scraped_at.isoformat()
                )
            )
            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            # Duplicate URL - article already exists
            return None


def get_articles(
    source: Optional[str] = None,
    since: Optional[datetime] = None,
    limit: int = 100
) -> list[Article]:
    """Get articles with optional filtering."""
    query = "SELECT id, title, url, source, published_at, content_preview, scraped_at FROM articles"
    conditions = []
    params = []
    
    if source:
        conditions.append("source = ?")
        params.append(source)
    
    if since:
        conditions.append("scraped_at >= ?")
        params.append(since.isoformat())
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    query += " ORDER BY published_at DESC, scraped_at DESC LIMIT ?"
    params.append(limit)
    
    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()
        return [Article.from_row(tuple(row)) for row in rows]


def save_summary(summary: Summary) -> int:
    """Save a daily summary, replacing any existing one for that date."""
    with get_db() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO summaries (date, content, created_at)
            VALUES (?, ?, ?)
            """,
            (summary.date, summary.content, summary.created_at.isoformat())
        )
        conn.commit()
        cursor = conn.execute("SELECT last_insert_rowid()")
        return cursor.fetchone()[0]


def get_latest_summary() -> Optional[Summary]:
    """Get the most recent summary."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT id, date, content, created_at FROM summaries ORDER BY date DESC LIMIT 1"
        ).fetchone()
        return Summary.from_row(tuple(row)) if row else None


def get_summaries(limit: int = 30) -> list[Summary]:
    """Get recent summaries."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, date, content, created_at FROM summaries ORDER BY date DESC LIMIT ?",
            (limit,)
        ).fetchall()
        return [Summary.from_row(tuple(row)) for row in rows]
