import logging
import asyncio
import sys
import os
from pathlib import Path

# Add root to sys.path immediately to ensure robust imports
BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Define log directory early
LOG_DIR = BASE_DIR / "refresh_logs"
LOG_DIR.mkdir(exist_ok=True)

# Configure logging
logger = logging.getLogger("Phase5Scheduler")
logger.setLevel(logging.INFO)

# File handler for daily_refresh.log
if not logger.handlers:
    fh = logging.FileHandler(LOG_DIR / "daily_refresh.log")
    fh.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    logger.addHandler(fh)
    
    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(ch)

def daily_data_refresh():
    """
    Main task to refresh mutual fund data:
    1. Scrape new HTML from INDMoney (Async)
    2. Parse HTML to structured JSON
    3. Update Vector Store (Clear and Re-embed)
    """
    logger.info("Starting scheduled daily data refresh...")
    
    # Import phase modules locally so they don't crash the main API server at startup
    try:
        from phase_1.scraper import main as run_scraper_async
        from phase_1.parser import main as run_parser
        from phase_1.mfapi_fetcher import main as run_mfapi
        from phase_1.static_metadata import main as run_static_metadata
        from phase_1.chunker import process_and_store
    except ImportError as e:
        logger.error(f"Failed to import Phase modules inside scheduler task: {e}")
        return
    
    try:        # Step 1: Scrape
        logger.info("Step 1: Scraping fund pages...")
        # Since scraper.main is async, we need to run it in an event loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we are inside an existing loop (like FastAPI), we might need another approach
                # but usually APScheduler runs its own thread.
                # A safer way to run async from sync in a background thread:
                asyncio.run_coroutine_threadsafe(run_scraper_async(), loop).result()
            else:
                asyncio.run(run_scraper_async())
        except RuntimeError:
            # No loop running or other loop issues
            asyncio.run(run_scraper_async())
        
        # Step 2: Parse
        logger.info("Step 2: Parsing scraped data...")
        run_parser()
        
        # Step 3: Map MFAPI Data
        logger.info("Step 3: Fetching MFAPI metrics and NAV history...")
        run_mfapi()
        
        # Step 4: Enrich with Static Metadata
        logger.info("Step 4: Applying static rules and guardrails...")
        run_static_metadata()
        
        # Step 5: Vector Store Sync
        logger.info("Step 5: Updating vector store (clearing collection first)...")
        process_and_store(clear_collection=True)
        
        logger.info("Daily data refresh completed successfully!")
    except Exception as e:
        logger.error(f"Daily refresh failed: {str(e)}", exc_info=True)
        raise e
