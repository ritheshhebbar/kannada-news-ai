import json
import logging
import os
import re
import urllib.parse
import urllib.request
from typing import List, Dict, Any, Optional
from services.ml.llm.base import BaseSummarizer
from services.ml.verification.extractive import generate_extractive_summary

logger = logging.getLogger(__name__)

class GeminiSummarizer(BaseSummarizer):
    """Google Gemini LLM summarizer with strict JSON schema and evidence citations."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-3-flash-preview",
        prompt_file: Optional[str] = None,
    ):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "").strip()
        self.model = model or os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")
        
        # Load prompt template
        if prompt_file and os.path.exists(prompt_file):
            with open(prompt_file, "r", encoding="utf-8") as f:
                self.prompt_template = f.read()
        else:
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            default_prompt = os.path.join(base_dir, "prompts", "summarize_v1.txt")
            if os.path.exists(default_prompt):
                with open(default_prompt, "r", encoding="utf-8") as f:
                    self.prompt_template = f.read()
            else:
                self.prompt_template = (
                    "You are a news editor. Summarize these numbered sentences [S0], [S1], ...\n"
                    "Return JSON with headline, summary (2-3 sentences), key_points (text + evidence index), key_facts, uncertain."
                )

    def _call_gemini_api(self, prompt: str) -> Optional[str]:
        if not self.api_key:
            logger.warning("No GEMINI_API_KEY provided; skipping live Gemini API call.")
            return None

        # Support fallback models if primary model is unavailable
        models_to_try = [self.model, "gemini-3.5-flash", "gemini-3.1-flash-lite", "gemini-3-flash-preview"]
        for m in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={self.api_key}"
            payload = {
                "contents": [
                    {
                        "parts": [
                            {"text": prompt}
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.2,
                    "responseMimeType": "application/json"
                }
            }

            try:
                data = json.dumps(payload).encode("utf-8")
                req = urllib.request.Request(
                    url,
                    data=data,
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=15) as resp:
                    resp_json = json.loads(resp.read().decode("utf-8"))
                    text = resp_json["candidates"][0]["content"]["parts"][0]["text"]
                    return text
            except Exception as e:
                logger.warning("Gemini model %s failed: %s", m, e)

        return None

    def summarize(self, numbered_sentences: List[str]) -> Dict[str, Any]:
        if not numbered_sentences:
            return {
                "headline": "Kannada News Brief",
                "summary": "No content available for summarization.",
                "key_points": [],
                "key_facts": {"who": [], "what": [], "where": [], "when": [], "numbers": []},
                "uncertain": [],
            }

        # Build numbered sentences prompt
        formatted_sentences = []
        for idx, sent in enumerate(numbered_sentences):
            formatted_sentences.append(f"[S{idx}] {sent.strip()}")
        joined_text = "\n".join(formatted_sentences)

        full_prompt = f"{self.prompt_template}\n\nInput Sentences:\n{joined_text}"

        # Try Gemini API if key is available
        raw_output = self._call_gemini_api(full_prompt)

        if raw_output:
            try:
                # Strip Markdown code blocks if any
                clean_json_str = raw_output.strip()
                if clean_json_str.startswith("```"):
                    clean_json_str = re.sub(r"^```[a-zA-Z]*\n?", "", clean_json_str)
                    clean_json_str = re.sub(r"\n?```$", "", clean_json_str)
                parsed = json.loads(clean_json_str)
                
                # Sanitize structure
                return {
                    "headline": parsed.get("headline", numbered_sentences[0][:90]),
                    "summary": parsed.get("summary", ""),
                    "key_points": parsed.get("key_points", []),
                    "key_facts": parsed.get("key_facts", {
                        "who": [], "what": [], "where": [], "when": [], "numbers": []
                    }),
                    "uncertain": parsed.get("uncertain", []),
                }
            except Exception as e:
                logger.error("Failed to parse Gemini JSON output: %s (Raw: %s)", e, raw_output[:100])

        # Graceful fallback: Grounded extractive news summary
        extractive = generate_extractive_summary(numbered_sentences)
        return {
            "headline": extractive.get("headline_en", numbered_sentences[0][:90]),
            "summary": extractive.get("summary_en", ""),
            "key_points": extractive.get("key_points", []),
            "key_facts": {
                "who": ["Reported News Entity"],
                "what": ["Current event summary"],
                "where": ["Karnataka"],
                "when": ["Recent"],
                "numbers": []
            },
            "uncertain": []
        }

