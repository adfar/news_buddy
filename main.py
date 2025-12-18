#!/usr/bin/env python3
"""Main entry point for AI News Buddy."""

import argparse
import sys

import uvicorn

from config import config
from database import init_db
from scheduler import fetch_all_sources, run_daily_summary, start_scheduler


def main():
    parser = argparse.ArgumentParser(
        description="AI News Buddy - AI Company News Aggregator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run python main.py init      # Initialize the database
  uv run python main.py fetch     # Fetch articles from all sources
  uv run python main.py summarize # Generate daily summary
  uv run python main.py serve     # Start web server only
  uv run python main.py run       # Start scheduler + web server
        """
    )
    
    parser.add_argument(
        "command",
        choices=["init", "fetch", "summarize", "serve", "run"],
        help="Command to execute"
    )
    parser.add_argument(
        "--host", default=config.host,
        help=f"Host to bind to (default: {config.host})"
    )
    parser.add_argument(
        "--port", type=int, default=config.port,
        help=f"Port to bind to (default: {config.port})"
    )
    
    args = parser.parse_args()
    
    if args.command == "init":
        init_db()
        print("Database initialized successfully!")
        
    elif args.command == "fetch":
        init_db()
        new_count = fetch_all_sources()
        print(f"Fetch complete. {new_count} new articles saved.")
        
    elif args.command == "summarize":
        init_db()
        run_daily_summary()
        print("Summary generated!")
        
    elif args.command == "serve":
        init_db()
        print(f"Starting web server at http://{args.host}:{args.port}")
        uvicorn.run("app:app", host=args.host, port=args.port, reload=False)
        
    elif args.command == "run":
        init_db()
        
        # Do an initial fetch
        print("Running initial fetch...")
        fetch_all_sources()
        
        # Start the scheduler
        scheduler = start_scheduler()
        
        # Start the web server (blocking)
        print(f"\nStarting web server at http://{args.host}:{args.port}")
        try:
            uvicorn.run("app:app", host=args.host, port=args.port, reload=False)
        finally:
            scheduler.shutdown()


if __name__ == "__main__":
    main()
