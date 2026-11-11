import logging
import os
import sys

# Ensure repository root is in sys.path for services import
curr = os.path.dirname(os.path.abspath(__file__))
while curr and os.path.basename(curr) not in ("kannada-news-ai", ""):
    curr = os.path.dirname(curr)
root_dir = curr
if root_dir and root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from fastapi import APIRouter, BackgroundTasks, status
from services.collector.collector import NewsCollector

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/collector", tags=["News Collector"])

def run_collector_sync_task():
    try:
        collector = NewsCollector(max_articles_per_feed=2)
        stats = collector.sync_all(process_now=True)
        logger.info("Background collector sync complete: %s", stats)
    except Exception as e:
        logger.error("Error in background collector sync: %s", e)

@router.post("/sync", status_code=status.HTTP_202_ACCEPTED)
def trigger_live_rss_sync(background_tasks: BackgroundTasks):
    """Trigger background crawler to fetch fresh live Kannada RSS news articles."""
    background_tasks.add_task(run_collector_sync_task)
    return {
        "status": "initiated",
        "message": "Live RSS news crawler has been started in the background. Fresh articles will appear momentarily."
    }
