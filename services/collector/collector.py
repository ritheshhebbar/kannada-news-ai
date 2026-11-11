import hashlib
import logging
import os
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Dict, List, Optional
import trafilatura
import yaml

# Ensure project paths
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(root_dir, "apps", "api"))
sys.path.insert(0, root_dir)

from app.db import SessionLocal
from app.models import Article, Source, PipelineJob
from app.services.article_service import is_predominantly_kannada
from services.collector.robots import RobotsChecker
from services.worker.worker import process_job

logger = logging.getLogger(__name__)

class NewsCollector:
    """Automated RSS News Collector for Kannada publications."""

    def __init__(self, sources_file: Optional[str] = None, max_articles_per_feed: int = 3):
        self.max_articles_per_feed = max_articles_per_feed
        self.robots = RobotsChecker()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) KannadaNewsAI-ResearchBot/1.0"
        }

        if not sources_file:
            sources_file = os.path.join(os.path.dirname(__file__), "sources.yaml")
        
        self.sources_config = []
        if os.path.exists(sources_file):
            with open(sources_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                self.sources_config = data.get("sources", [])

    def sync_all(self, process_now: bool = True) -> Dict[str, int]:
        """Fetches latest articles from all configured feeds and processes them."""
        db = SessionLocal()
        total_fetched = 0
        total_processed = 0
        total_skipped = 0

        try:
            for s_cfg in self.sources_config:
                if not s_cfg.get("active", True):
                    continue

                source_name = s_cfg["name"]
                feed_url = s_cfg["feed_url"]
                base_url = s_cfg["base_url"]
                section_label = s_cfg.get("section_label", "karnataka")

                # Ensure source exists in DB
                src = db.query(Source).filter(Source.name == source_name).first()
                if not src:
                    src = Source(
                        name=source_name,
                        base_url=base_url,
                        feed_url=feed_url,
                        robots_checked=True,
                        active=True,
                    )
                    db.add(src)
                    db.flush()

                # Fetch feed XML
                try:
                    req = urllib.request.Request(feed_url, headers=self.headers)
                    with urllib.request.urlopen(req, timeout=10) as resp:
                        xml_bytes = resp.read()
                        root = ET.fromstring(xml_bytes)
                except Exception as e:
                    logger.error("Failed to read RSS feed for %s: %s", source_name, e)
                    continue

                items = root.findall(".//item")
                count_for_source = 0

                for item in items:
                    if count_for_source >= self.max_articles_per_feed:
                        break

                    title_el = item.find("title")
                    link_el = item.find("link")
                    if title_el is None or link_el is None:
                        continue

                    title_kn = (title_el.text or "").strip()
                    article_url = (link_el.text or "").strip()

                    if not article_url or not title_kn:
                        continue

                    # Deduplication check by URL
                    existing = db.query(Article).filter(Article.url == article_url).first()
                    if existing:
                        total_skipped += 1
                        continue

                    # Check robots.txt
                    if not self.robots.is_allowed(article_url):
                        logger.warning("robots.txt disallowed fetching: %s", article_url)
                        continue

                    # Download and extract article body
                    try:
                        downloaded = trafilatura.fetch_url(article_url)
                        raw_body = trafilatura.extract(downloaded) or ""
                    except Exception as e:
                        logger.error("Failed extracting article %s: %s", article_url, e)
                        raw_body = ""

                    # Clean paragraphs: remove ads, short menu navigation, and footers
                    blacklist = ["Go Ad Lite", "ಜಾಹೀರಾತು", "Comments", "ಫಾಲೋ ಮಾಡಿ", "ಪ್ರಜಾವಾಣಿ ಆ್ಯಪ್", "ಇ–ಪೇಪರ್", "Subscribe", "ಡೌನ್‌ಲೋಡ್", "Published"]
                    clean_paras = []
                    for line in raw_body.splitlines():
                        l = line.strip()
                        if len(l) < 35 or any(b in l for b in blacklist):
                            continue
                        if is_predominantly_kannada(l, min_ratio=0.3)[0]:
                            clean_paras.append(l)

                    body_kn = "\n\n".join(clean_paras[:5])

                    if not body_kn or len(body_kn.strip()) < 80:
                        continue

                    # Script check
                    is_kn, _ = is_predominantly_kannada(body_kn)
                    if not is_kn:
                        continue

                    content_hash = hashlib.sha256(body_kn.encode("utf-8")).hexdigest()
                    if db.query(Article).filter(Article.content_hash == content_hash).first():
                        total_skipped += 1
                        continue

                    # Create Article
                    article = Article(
                        source_id=src.id,
                        origin="rss",
                        url=article_url,
                        title_kn=title_kn,
                        body_kn=body_kn,
                        content_hash=content_hash,
                        section_label=section_label,
                        status="new",
                        published_at=datetime.now(timezone.utc),
                        fetched_at=datetime.now(timezone.utc),
                    )
                    db.add(article)
                    db.flush()

                    # Create pipeline job
                    job = PipelineJob(
                        article_id=article.id,
                        stage="preprocess",
                        state="queued",
                        attempts=0,
                    )
                    db.add(job)
                    db.commit()

                    total_fetched += 1
                    count_for_source += 1

                    # Process article through the pipeline immediately
                    if process_now:
                        try:
                            logger.info("Processing RSS article ID %d (%s)...", article.id, title_kn[:40])
                            process_job(db, job)
                            total_processed += 1
                        except Exception as e:
                            logger.error("Error processing collected article %d: %s", article.id, e)

                    # Politeness sleep between page fetches
                    delay = float(s_cfg.get("rate_limit_delay_sec", 2.0))
                    time.sleep(delay)

        finally:
            db.close()

        return {
            "fetched": total_fetched,
            "processed": total_processed,
            "skipped": total_skipped,
        }

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    collector = NewsCollector()
    res = collector.sync_all()
    print("Sync complete:", res)
