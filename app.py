"""FastAPI web application for the AI News Aggregator."""

from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from database import get_articles, get_latest_summary, get_summaries


app = FastAPI(title="AI News Buddy", description="AI Company News Aggregator")

# Setup templates and static files
BASE_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


@app.get("/", response_class=HTMLResponse)
async def home(
    request: Request,
    source: Optional[str] = Query(None, description="Filter by source"),
    limit: int = Query(50, ge=1, le=200)
):
    """Home page with unified news feed."""
    articles = get_articles(source=source, limit=limit)
    sources = ["OpenAI", "Anthropic", "DeepMind"]
    
    return templates.TemplateResponse(
        "feed.html",
        {
            "request": request,
            "articles": articles,
            "sources": sources,
            "current_source": source,
            "now": datetime.now()
        }
    )


@app.get("/summary", response_class=HTMLResponse)
async def latest_summary(request: Request):
    """View the latest daily summary."""
    summary = get_latest_summary()
    return templates.TemplateResponse(
        "summary.html",
        {
            "request": request,
            "summary": summary,
            "now": datetime.now()
        }
    )


@app.get("/summaries", response_class=HTMLResponse)
async def summary_archive(request: Request, limit: int = Query(30, ge=1, le=100)):
    """Archive of past summaries."""
    summaries = get_summaries(limit=limit)
    return templates.TemplateResponse(
        "summaries.html",
        {
            "request": request,
            "summaries": summaries,
            "now": datetime.now()
        }
    )


# JSON API endpoints
@app.get("/api/articles")
async def api_articles(
    source: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200)
):
    """Get articles as JSON."""
    articles = get_articles(source=source, limit=limit)
    return [
        {
            "id": a.id,
            "title": a.title,
            "url": a.url,
            "source": a.source,
            "published_at": a.published_at.isoformat() if a.published_at else None,
            "scraped_at": a.scraped_at.isoformat()
        }
        for a in articles
    ]


@app.get("/api/summary/latest")
async def api_latest_summary():
    """Get the latest summary as JSON."""
    summary = get_latest_summary()
    if not summary:
        return {"error": "No summary available"}
    return {
        "id": summary.id,
        "date": summary.date,
        "content": summary.content,
        "created_at": summary.created_at.isoformat()
    }
