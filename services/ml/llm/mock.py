from typing import List, Dict, Any
from services.ml.llm.base import BaseSummarizer

class MockSummarizer(BaseSummarizer):
    """High-quality grounded mock summarizer adhering to strict prompt schema with evidence citations."""

    def summarize(self, numbered_sentences: List[str]) -> Dict[str, Any]:
        if not numbered_sentences:
            return {
                "headline": "Kannada News Brief",
                "summary": "No content available for summarization.",
                "key_points": [],
                "key_facts": {"who": [], "what": [], "where": [], "when": [], "numbers": []},
                "uncertain": [],
            }

        first_sent = numbered_sentences[0]
        full_text = " ".join(numbered_sentences)

        # Extract basic entities and numbers
        words = full_text.split()
        who = [w for w in ["Siddaramaiah", "M. B. Patil", "S. Somanath", "Mayank Agarwal", "Prasidh Krishna"] if w in full_text]
        where = [w for w in ["Bengaluru", "Mysuru", "Sriharikota", "Karnataka"] if w in full_text]
        numbers = [w for w in ["₹1,500 crore", "10 lakh", "2,275 kg", "8 wickets", "145 runs", "78 runs", "7 wickets"] if w in full_text]

        key_points = []
        for idx, sent in enumerate(numbered_sentences[:4]):
            key_points.append({
                "text": sent.strip()[:100],
                "evidence": [idx]
            })

        headline = first_sent.split(":")[ -1].strip()[:90] if ":" in first_sent else first_sent[:90]

        return {
            "headline": headline,
            "summary": f"{first_sent[:120]}. " + (numbered_sentences[1][:120] if len(numbered_sentences) > 1 else ""),
            "key_points": key_points,
            "key_facts": {
                "who": who if who else ["Government / News Authority"],
                "what": ["Reported development"],
                "where": where if where else ["Karnataka"],
                "when": ["Recent"],
                "numbers": numbers,
            },
            "uncertain": [],
        }

