import logging
import urllib.parse
import urllib.request
import urllib.robotparser

logger = logging.getLogger(__name__)

class RobotsChecker:
    """Verifies robots.txt politeness compliance before crawling external news sources."""

    def __init__(self, user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) KannadaNewsAI-ResearchBot/1.0"):
        self.user_agent = user_agent
        self.headers = {"User-Agent": self.user_agent}
        self._parsers = {}

    def is_allowed(self, url: str) -> bool:
        """Checks if fetching the given URL is allowed by the host robots.txt."""
        try:
            parsed = urllib.parse.urlparse(url)
            host = f"{parsed.scheme}://{parsed.netloc}"

            if host not in self._parsers:
                rp = urllib.robotparser.RobotFileParser()
                robots_url = f"{host}/robots.txt"
                try:
                    req = urllib.request.Request(robots_url, headers=self.headers)
                    with urllib.request.urlopen(req, timeout=5) as resp:
                        content = resp.read().decode("utf-8", errors="ignore")
                        rp.parse(content.splitlines())
                except Exception as e:
                    logger.warning("Could not read robots.txt for %s: %s (defaulting to allowed)", host, e)
                    rp.parse(["User-agent: *", "Allow: /"])
                self._parsers[host] = rp

            return self._parsers[host].can_fetch("*", url)
        except Exception as e:
            logger.error("Error in robots.txt check for %s: %s", url, e)
            return True
