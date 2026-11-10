from typing import List, Dict, Any

def generate_extractive_summary(sentences_en: List[str]) -> Dict[str, Any]:
    """Deterministic fallback: selects leading and most informative sentences without hallucination risk."""
    if not sentences_en:
        return {
            "headline_en": "News Summary",
            "summary_en": "No content available.",
            "key_points": [],
            "method": "extractive_fallback"
        }

    # First sentence serves as headline and primary summary
    lead = sentences_en[0].strip()
    headline = lead.split(":")[ -1].strip()[:90] if ":" in lead else lead[:90]
    
    # 2-sentence summary
    summary_text = " ".join([s.strip() for s in sentences_en[:2]])

    key_points = []
    for idx, s in enumerate(sentences_en[:3]):
        key_points.append({
            "text": s.strip(),
            "evidence": [idx]
        })

    return {
        "headline_en": f"[Extractive] {headline}",
        "summary_en": summary_text,
        "key_points": key_points,
        "method": "extractive_fallback"
    }

