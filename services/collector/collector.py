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
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
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

                # Format dynamic date placeholder if present in feed_url
                now = datetime.now()
                feed_url = feed_url.format(month_year=now.strftime("%m-%Y"))

                # Fetch feed XML
                try:
                    req = urllib.request.Request(feed_url, headers=self.headers)
                    with urllib.request.urlopen(req, timeout=12) as resp:
                        xml_bytes = resp.read()
                    try:
                        root = ET.fromstring(xml_bytes)
                    except ET.ParseError:
                        import re
                        clean_xml = re.sub(b"&(?!(amp|lt|gt|quot|apos);)", b"&amp;", xml_bytes)
                        root = ET.fromstring(clean_xml)
                except Exception as e:
                    logger.error("Failed to read RSS/sitemap feed for %s (%s): %s", source_name, feed_url, e)
                    continue

                # Extract candidate entries: check RSS <item> first, then sitemap <url>
                feed_entries = []
                rss_items = root.findall(".//item")
                if rss_items:
                    for item in rss_items:
                        t_el = item.find("title")
                        l_el = item.find("link")
                        if l_el is not None:
                            url_str = (l_el.text or "").strip()
                            title_str = (t_el.text or "").strip() if t_el is not None else ""
                            if url_str:
                                feed_entries.append((title_str, url_str))
                else:
                    # Check XML sitemap format
                    sitemap_urls = root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}url") or root.findall(".//url")
                    # For sitemaps with newest at the end, take reversed
                    for url_node in reversed(sitemap_urls):
                        loc_el = url_node.find("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
                        if loc_el is None:
                            loc_el = url_node.find("loc")
                        if loc_el is not None and loc_el.text:
                            url_str = loc_el.text.strip()
                            news_el = url_node.find("{http://www.google.com/schemas/sitemap-news/0.9}news")
                            title_str = ""
                            if news_el is not None:
                                title_elem = news_el.find("{http://www.google.com/schemas/sitemap-news/0.9}title")
                                if title_elem is not None and title_elem.text:
                                    title_str = title_elem.text.strip()
                            if url_str:
                                feed_entries.append((title_str, url_str))

                count_for_source = 0

                for title_kn, article_url in feed_entries:
                    if count_for_source >= self.max_articles_per_feed:
                        break

                    if not article_url:
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
                        raw_body = ""

                        # Special handling for Udayavani's dynamic Cloudfront JSON
                        if "udayavani.com" in article_url and downloaded:
                            import re
                            from bs4 import BeautifulSoup
                            json_paths = re.findall(r'(/test-news/news-json/[a-zA-Z0-9_.-]+\.json)', downloaded)
                            if json_paths:
                                cf_url = f"https://d3jde0c4xcko0v.cloudfront.net/production{json_paths[0]}"
                                try:
                                    req_cf = urllib.request.Request(cf_url, headers=self.headers)
                                    with urllib.request.urlopen(req_cf, timeout=6) as r_cf:
                                        cf_data = r_cf.read().decode("utf-8", errors="ignore")
                                        soup = BeautifulSoup(cf_data, "html.parser")
                                        raw_body = soup.get_text(separator="\n", strip=True)
                                except Exception as ex_cf:
                                    logger.warning("Udayavani Cloudfront JSON fetch error: %s", ex_cf)

                        if not raw_body and downloaded:
                            raw_body = trafilatura.extract(downloaded) or ""

                        # If title_kn was empty from sitemap, extract from HTML
                        if not title_kn and downloaded:
                            from bs4 import BeautifulSoup
                            soup = BeautifulSoup(downloaded, "html.parser")
                            h1 = soup.find("h1")
                            if h1 and h1.get_text().strip():
                                title_kn = h1.get_text().strip()
                            elif soup.title and soup.title.string:
                                title_kn = soup.title.string.split("|")[0].split("-")[0].strip()

                    except Exception as e:
                        logger.error("Failed extracting article %s: %s", article_url, e)
                        raw_body = ""
                        title_kn = title_kn or ""

                    if not title_kn:
                        continue

                    # Clean paragraphs: remove ads, short menu navigation, and footers
                    blacklist = [
                        "Go Ad Lite", "ಜಾಹೀರಾತು", "Comments", "ಫಾಲೋ ಮಾಡಿ", "ಪ್ರಜಾವಾಣಿ ಆ್ಯಪ್",
                        "ಇ–ಪೇಪರ್", "Subscribe", "ಡೌನ್‌ಲೋಡ್", "Published", "ADVERTISEMENT",
                        "Team Udayavani", "Visit UV English", "Get App Android"
                    ]
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
