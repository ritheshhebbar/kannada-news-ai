import json
import logging
import os
import re
import time
import urllib.parse
import urllib.request
from typing import List, Optional
from dotenv import load_dotenv

curr_dir = os.path.dirname(os.path.abspath(__file__))
while curr_dir and os.path.basename(curr_dir) not in ("kannada-news-ai", ""):
    if os.path.exists(os.path.join(curr_dir, ".git")) or os.path.basename(curr_dir) == "kannada-news-ai":
        break
    curr_dir = os.path.dirname(curr_dir)
repo_root = curr_dir or os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
load_dotenv(os.path.join(repo_root, ".env"))
load_dotenv()
from services.ml.translation.base import BaseTranslator
from services.ml.kannada_text import convert_kannada_digits_to_ascii

logger = logging.getLogger(__name__)

class GoogleTranslator(BaseTranslator):
    """Google Translation engine for Kannada-to-English news supporting both Gemini LLM translation and NMT gateway."""

    def __init__(self, api_key: Optional[str] = None, timeout: float = 12.0, retries: int = 2):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "").strip()
        self.timeout = timeout
        self.retries = retries
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }

    def _translate_batch_gemini(self, sentences: List[str]) -> Optional[List[str]]:
        """Translates a batch of sentences using Google Gemini Flash in a single shot."""
        if not self.api_key or not sentences:
            return None

        prompt = (
            "You are a professional news translator from Kannada to English.\n"
            "Translate each of the following Kannada sentences into clear, journalistic English.\n"
            "Maintain exact 1-to-1 order and return a JSON array of strings matching the length of the input.\n\n"
            f"Input Kannada Sentences:\n{json.dumps(sentences, ensure_ascii=False)}"
        )

        for m in ["gemini-3.1-flash-lite", "gemini-3-flash-preview"]:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={self.api_key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.1,
                    "responseMimeType": "application/json"
                }
            }
            try:
                data = json.dumps(payload).encode("utf-8")
                req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    resp_json = json.loads(resp.read().decode("utf-8"))
                    text = resp_json["candidates"][0]["content"]["parts"][0]["text"].strip()
                    if text.startswith("```"):
                        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
                        text = re.sub(r"\n?```$", "", text)
                    parsed = json.loads(text)
                    if isinstance(parsed, list) and len(parsed) == len(sentences):
                        return [convert_kannada_digits_to_ascii(str(s).strip()) for s in parsed]
            except Exception as e:
                logger.warning("Gemini batch translation with %s failed: %s", m, e)

        return None

    def _translate_single_web(self, text: str) -> str:
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
                    translated = " ".join(translated.split())
                    return convert_kannada_digits_to_ascii(translated)
            except Exception as e:
                logger.warning("Google web translation attempt %d failed: %s", attempt + 1, e)
                if attempt < self.retries - 1:
                    time.sleep(1.0)
                else:
                    return clean

        return clean

    def translate_headline(self, headline: str) -> str:
        if not headline or not headline.strip():
            return "Kannada News Brief"

        # Try Gemini first if key available
        if self.api_key:
            res = self._translate_batch_gemini([headline])
            if res and res[0]:
                return res[0]

        return self._translate_single_web(headline)

    def translate_sentences(self, sentences: List[str]) -> List[str]:
        if not sentences:
            return []

        # Attempt high-performance batch translation via Gemini
        if self.api_key:
            batch_result = self._translate_batch_gemini(sentences)
            if batch_result:
                return batch_result

        # Fallback to single web requests with polite delay
        results = []
        for s in sentences:
            translated = self._translate_single_web(s)
            results.append(translated)
            time.sleep(0.3)
        return results
