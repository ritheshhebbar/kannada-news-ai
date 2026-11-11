import json
import logging
import time
import urllib.parse
import urllib.request
from typing import List
from services.ml.translation.base import BaseTranslator
from services.ml.kannada_text import convert_kannada_digits_to_ascii

logger = logging.getLogger(__name__)

class GoogleTranslator(BaseTranslator):
    """Real-time Google Translation engine for Kannada-to-English news."""

    def __init__(self, timeout: float = 8.0, retries: int = 3):
        self.timeout = timeout
        self.retries = retries
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }

    def _translate_single(self, text: str) -> str:
        clean = text.strip()
        if not clean:
            return ""

        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=kn&tl=en&dt=t&q={urllib.parse.quote(clean)}"
        for attempt in range(self.retries):
            try:
                req = urllib.request.Request(url, headers=self.headers)
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    translated = "".join(part[0] for part in data[0] if part and part[0])
                    # Clean up multiple whitespaces
                    translated = " ".join(translated.split())
                    return convert_kannada_digits_to_ascii(translated)
            except Exception as e:
                logger.warning("Google translation attempt %d failed for text: %s (err: %s)", attempt + 1, clean[:40], e)
                if attempt < self.retries - 1:
                    time.sleep(0.5 * (attempt + 1))
                else:
                    logger.error("All Google translation attempts failed for: %s", clean[:40])
                    return f"[Translation Error] {clean}"

        return clean

    def translate_headline(self, headline: str) -> str:
        if not headline or not headline.strip():
            return "Kannada News Brief"
        en = self._translate_single(headline)
        # News headlines should be concise and capitalized
        return en.strip()

    def translate_sentences(self, sentences: List[str]) -> List[str]:
        results = []
        for s in sentences:
            translated = self._translate_single(s)
            results.append(translated)
            # Brief politeness pause between sentence requests
            time.sleep(0.05)
        return results

